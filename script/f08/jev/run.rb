require "open3"
require "optparse"
require "securerandom"
require "time"
require_relative "evaluation"

module F08Jev
  class Runner
    ROOT = File.expand_path("../../..", __dir__)
    REPORT_VERSION = "1.0.0"
    DEFAULT_MODEL = "jev-latest"
    TIMEOUT_SECONDS = 5

    def initialize(args)
      @options = { mode: "offline" }
      @parser = OptionParser.new do |parser|
        parser.banner = "Uso: ruby script/f08/jev/run.rb [--mode validate|offline|live] [opções]"
        parser.on("--mode MODE", %w[validate offline live]) { |mode| @options[:mode] = mode }
        parser.on("--limit N", Integer, "Seleciona os N primeiros relatos na ordem versionada") { |n| @options[:limit] = n }
        parser.on("--model ID", "Modelo solicitado ao vivo") { |model| @options[:model] = model }
        parser.on("--reviewed-sha256 HASH", "Hash do dataset revisado no chat central") { |hash| @options[:reviewed] = hash }
        parser.on("--budget-reference ID", "Referência do orçamento aprovado no chat central") { |id| @options[:budget] = id }
      end
      @parser.parse!(args)
      raise OptionParser::InvalidArgument, "argumentos posicionais não são aceitos" unless args.empty?
    end

    def run
      dataset = Dataset.new(dataset_path: File.join(__dir__, "dataset.json"), catalog_path: File.join(__dir__, "catalog.json"))
      mode = @options.fetch(:mode)
      limit = @options.fetch(:limit, dataset.cases.size)
      if @options.key?(:limit) && !limit.between?(1, dataset.cases.size)
        raise ValidationError, "--limit precisa estar entre 1 e #{dataset.cases.size}"
      end
      live_only = @options.keys.intersect?(%i[model reviewed budget])
      raise ValidationError, "modelo, revisão e orçamento são opções exclusivas do modo live" if live_only && mode != "live"
      raise ValidationError, "--limit não se aplica ao modo validate" if mode == "validate" && @options[:limit]

      manifest = manifest(dataset, mode)
      if mode == "validate"
        return manifest.merge(status: "validated", selection: selection(dataset.cases))
      end

      client = build_client(mode, dataset)
      evaluation = Evaluation.new(catalog: dataset.catalog, mode: mode)
      cases = dataset.cases.first(limit)
      rows = cases.map do |entry|
        evaluation.observe(entry, client).tap do |row|
          row[:model] = nil if @secret && row[:model]&.include?(@secret)
        end
      end
      controls = mode == "offline" ? Controls.new(dataset.catalog).run(evaluation) : []
      valid = controls.all? { |row| row.fetch(:passed) } && rows.all? do |row|
        row[:channel_preservation].values.all? && row[:request_count] == 1 && row[:questions] == row[:missing]
      end

      manifest.merge(
        status: valid ? "completed" : "invariant_failed",
        selection: selection(cases),
        parameters: { limit: limit, concurrency: 1, attempts_per_case: 1, requested_model: client.model,
                      timeout_seconds: mode == "live" ? TIMEOUT_SECONDS : nil, budget_reference: @options[:budget] },
        metrics: evaluation.summarize(rows), cases: rows, offline_controls: controls,
        finished_at: Time.now.utc.iso8601
      )
    end

    private

    def build_client(mode, dataset)
      if mode == "offline"
        require_relative "controls"
        return Classification::Jev::DemoFixture.new
      end

      unless @options[:limit] && @options[:reviewed] == dataset.metadata.dig(:dataset, :sha256) &&
             @options[:budget]&.match?(/\A[a-zA-Z0-9_.\/-]+\z/)
        raise ValidationError, "live exige --limit, --reviewed-sha256 igual ao dataset revisado e --budget-reference"
      end
      @secret = ENV["TYPESAFE_API_KEY"].to_s.strip
      raise ValidationError, "TYPESAFE_API_KEY ausente" if @secret.empty?

      model = @options.fetch(:model, ENV.fetch("CLOUDWALK_JEV_MODEL", DEFAULT_MODEL))
      unless model.match?(/\A[a-zA-Z0-9_.\/-]+\z/) && !model.include?(@secret) && !@options[:budget].include?(@secret)
        raise ValidationError, "identificador de modelo ou de orçamento inválido"
      end

      Classification::Jev::HttpClient.new(api_key: @secret, model: model, timeout_seconds: TIMEOUT_SECONDS)
    end

    def manifest(dataset, mode)
      revision, _, revision_status = Open3.capture3("git", "rev-parse", "HEAD", chdir: ROOT)
      dirty, _, dirty_status = Open3.capture3("git", "--no-optional-locks", "status", "--porcelain", chdir: ROOT)
      dataset.metadata.merge(
        report_version: REPORT_VERSION, run_id: SecureRandom.uuid, started_at: Time.now.utc.iso8601,
        mode: mode, scenario: "classificacao_de_campos_omitidos", ruby: RUBY_VERSION,
        git_revision: revision_status.success? ? revision.strip : nil,
        git_dirty: dirty_status.success? ? !dirty.empty? : nil
      )
    end

    def selection(cases)
      {
        total_cases: cases.size,
        by_missing: cases.map { |entry| entry.fetch("missing").join("+") }.tally,
        by_stratum: cases.map { |entry| entry.fetch("stratum") }.tally
      }
    end
  end
end

if $PROGRAM_NAME == __FILE__
  begin
    report = F08Jev::Runner.new(ARGV).run
    puts JSON.pretty_generate(report)
    exit 1 if report[:status] == "invariant_failed"
  rescue F08Jev::ValidationError, Errno::ENOENT => error
    warn JSON.generate(status: "blocked", reason: error.message)
    exit 2
  rescue OptionParser::ParseError
    # Erros de argumentos não repetem valores digitados por engano.
    warn JSON.generate(status: "blocked", reason: "opções inválidas, consulte --help")
    exit 2
  end
end
