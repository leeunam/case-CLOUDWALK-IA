require "minitest/autorun"
require "open3"
require "tmpdir"
require_relative "controls"
require_relative "run"

class F08JevTest < Minitest::Test
  ABSTENTION = F08Jev::ABSTENTION
  HttpClient = Classification::Jev::HttpClient
  DATASET_PATH = File.join(__dir__, "dataset.json")
  CATALOG_PATH = File.join(__dir__, "catalog.json")

  def setup
    @dataset = F08Jev::Dataset.new(dataset_path: DATASET_PATH, catalog_path: CATALOG_PATH)
    @evaluation = F08Jev::Evaluation.new(catalog: @dataset.catalog, mode: "offline")
    @controls = F08Jev::Controls.new(@dataset.catalog)
  end

  def test_dataset_distribution_and_hashes
    assert_equal 60, @dataset.cases.size
    assert_equal F08Jev::SPLITS, @dataset.distribution
    assert_equal Digest::SHA256.file(DATASET_PATH).hexdigest, @dataset.metadata.dig(:dataset, :sha256)
    assert_equal Digest::SHA256.file(CATALOG_PATH).hexdigest, @dataset.metadata.dig(:catalog, :sha256)
  end

  def test_validation_rejects_duplicate_ids_and_normalized_texts
    reject_dataset(/IDs duplicados/) { |cases| cases[1]["id"] = cases[0]["id"] }
    reject_dataset(/relatos duplicados/) { |cases| cases[1]["text"] = "  #{cases[0]["text"].upcase}  " }
  end

  def test_validation_rejects_bad_codes_masks_and_strata
    reject_dataset(/rótulo fora do catálogo/) { |cases| cases[0]["expected"]["category"] = "outro" }
    reject_dataset(/campo recebido fora do catálogo/) { |cases| cases[0]["received"]["priority"] = "" }
    reject_dataset(/campos .* inconsistentes/) { |cases| cases[0]["missing"] = %w[category priority] }
    reject_dataset(/abstenção e estrato inconsistentes/) { |cases| cases[0]["expected"]["category"] = ABSTENTION }
    reject_dataset(/prioridade e estrato inconsistentes/) { |cases| cases[0]["stratum"] = "urgente" }
    reject_dataset(/distribuição esperada/) { |cases| cases.pop }
  end

  def test_validation_rejects_snapshot_drift_and_invalid_json
    catalog = JSON.parse(File.read(CATALOG_PATH))
    catalog.fetch("category")["pix"] = "Uma descrição diferente."
    with_json(catalog) do |path|
      error = assert_raises(F08Jev::ValidationError) do
        F08Jev::Dataset.new(dataset_path: DATASET_PATH, catalog_path: path)
      end
      assert_match(/diverge/, error.message)
      File.write(path, "inválido")
      error = assert_raises(F08Jev::ValidationError) do
        F08Jev::Dataset.new(dataset_path: DATASET_PATH, catalog_path: path)
      end
      assert_match(/JSON inválido/, error.message)
    end
  end

  def test_controls_verify_preservation_invalid_inputs_abstention_and_transport
    rows = @controls.run(@evaluation).to_h { |row| [row.fetch(:id), row] }
    assert_equal 7, rows.size
    assert rows.values.all? { |row| row.fetch(:passed) }
    assert_equal({ "priority" => true }, rows.dig("campo-preservado", :channel_preservation))
    assert_equal ["category"], rows.dig("campo-preservado", :questions)
    assert_equal :unavailable, rows.dig("entrada-invalida", :fields, "category", :raw_status)
    assert_equal :invalid_response, rows.dig("saida-invalida", :fields, "category", :raw_status)
    assert_equal :transport_failure, rows.dig("erro-rede", :fields, "category", :raw_status)
    assert_equal :timeout, rows.dig("timeout", :issues, :provider)
    assert_nil rows.dig("timeout", :provider_latency_ms)
  end

  def test_rates_keep_channel_fields_and_expected_abstentions_out_of_accuracy
    rows = [
      observe({ "category" => "pix" }, { "category" => "pix", "priority" => "urgent" }, { "priority" => "basic" }),
      observe({ "category" => "pix", "priority" => ABSTENTION }, { "category" => "pix", "priority" => ABSTENTION }),
      observe({ "category" => ABSTENTION }, { "category" => ABSTENTION }, { "priority" => "advanced" }),
      observe({ "category" => ABSTENTION }, { "category" => "pix" }, { "priority" => "urgent" }),
      observe({ "category" => "pix" }, { "category" => ABSTENTION }, { "priority" => "urgent" }),
      observe({ "category" => "pix" }, { "category" => "unknown" }, { "priority" => "urgent" }),
      observe({ "priority" => "urgent" }, {}, { "category" => "pix" }, client: timeout_client)
    ]
    metrics = @evaluation.summarize(rows)
    category = metrics.fetch(:by_field).fetch("category")
    assert_rate(category, :raw_accuracy, 2, 4)
    assert_rate(category, :raw_accuracy_given_choice, 2, 2)
    assert_rate(category, :applied_accuracy, 1, 4)
    assert_rate(category, :automatic_coverage, 2, 6)
    assert_equal 1, category.fetch(:coverage_blocked_after_choice)
    assert_rate(category, :abstentions, 2, 6)
    assert_rate(category, :correct_abstentions, 1, 2)
    assert_rate(category, :undue_abstentions, 1, 4)
    assert_rate(category, :automatic_on_expected_abstention, 1, 2)
    assert_rate(category, :invalid_responses, 1, 6)
    assert_rate(metrics.fetch(:by_field).fetch("priority"), :transport_failures, 1, 2)
    assert_rate(metrics.fetch(:by_field).fetch("priority"), :raw_accuracy_given_choice, 0, 0)
    assert_rate(metrics, :channel_fields_preserved, 6, 6)
    assert_equal 8, metrics.fetch(:questions)
    assert_equal 7, metrics.fetch(:requests)
    assert_equal({ samples: 0, p50: nil, p95: nil }, metrics.fetch(:provider_latency_ms))
  end

  def test_urgent_priority_outcomes_partition_only_expected_urgent_omissions
    rows = [
      observe({ "priority" => "urgent" }, { "priority" => "urgent" }, { "category" => "pix" }),
      observe({ "priority" => "urgent" }, { "priority" => "advanced" }, { "category" => "pix" }),
      observe({ "priority" => "urgent", "category" => ABSTENTION }, { "priority" => "urgent", "category" => ABSTENTION }),
      observe({ "priority" => "urgent" }, {}, { "category" => "pix" }),
      observe({ "priority" => "urgent" }, {}, { "category" => "pix" }, client: timeout_client),
      observe({ "category" => "pix" }, { "category" => "pix" }, { "priority" => "urgent" })
    ]
    urgent = @evaluation.summarize(rows).fetch(:urgent_priority)
    assert_equal 5, urgent.size
    urgent.each_key { |key| assert_rate(urgent, key, 1, 5) }
  end

  def test_recognized_choice_with_invalid_evidence_does_not_score
    expected = { "category" => "pix" }
    response = fixture_response(expected)
    response.dig("answers", "category")["confidence"] = 2.0
    client = Classification::Jev::FixtureClient.new(answers: response.fetch("answers"))
    row = observe(expected, {}, { "priority" => "basic" }, client: client)

    assert_equal "pix", row.dig(:fields, "category", :observed_choice)
    assert_equal :invalid_response, row.dig(:fields, "category", :raw_status)
    assert_nil row.dig(:fields, "category", :applied)
    category = @evaluation.summarize([row]).dig(:by_field, "category")
    assert_rate(category, :raw_accuracy, 0, 1)
    assert_rate(category, :raw_accuracy_given_choice, 0, 0)
    assert_rate(category, :applied_accuracy, 0, 1)
  end

  def test_live_latency_includes_failed_samples_when_observed
    live = F08Jev::Evaluation.new(catalog: @dataset.catalog, mode: "live")
    entry = { "id" => "sample", "received" => {}, "missing" => ["priority"], "text" => "controle",
              "expected" => { "priority" => "urgent" } }
    failure = live.observe(entry, timeout_client)
    assert_kind_of Integer, failure.fetch(:provider_latency_ms)
    rows = [4, 12, 28, 100].map { |latency| failure.merge(provider_latency_ms: latency) }
    rows << failure.merge(provider_latency_ms: nil)
    metrics = live.summarize(rows)
    assert_equal({ samples: 4, p50: 12, p95: 100 }, metrics.fetch(:provider_latency_ms))
    assert_equal({ status: "unavailable", amount: nil, currency: nil }, metrics.fetch(:provider_cost))
  end

  def test_cli_offline_runs_without_key_and_live_refuses_before_network
    offline, stderr, status = cli("--mode", "offline", "--limit", "3")
    assert status.success?, stderr
    report = JSON.parse(offline)
    assert_equal "completed", report.fetch("status")
    assert_equal({ "category" => 1, "priority" => 1, "category+priority" => 1 }, report.dig("selection", "by_missing"))
    assert_equal 7, report.fetch("offline_controls").size
    assert_equal 4, report.dig("metrics", "questions")

    hash = @dataset.metadata.dig(:dataset, :sha256)
    stdout, stderr, status = cli("--mode", "live", "--limit", "3", "--reviewed-sha256", "errado", "--budget-reference", "F08")
    assert_equal 2, status.exitstatus
    assert_empty stderr
    report = JSON.parse(stdout)
    assert_equal "blocked", report.fetch("status")
    assert_equal "live", report.fetch("mode")
    assert_equal 3, report.dig("selection", "total_cases")
    assert_equal hash, report.dig("dataset", "sha256")
    assert_match(/live exige/, report.fetch("reason"))

    stdout, stderr, status = cli("--mode", "live", "--limit", "3", "--reviewed-sha256", hash, "--budget-reference", "F08")
    assert_equal 2, status.exitstatus
    assert_empty stderr
    assert_equal "TYPESAFE_API_KEY ausente", JSON.parse(stdout).fetch("reason")

    stdout, stderr, status = cli("--mode", "invalid-mode")
    assert_equal 2, status.exitstatus
    assert_empty stderr
    assert_equal "blocked", JSON.parse(stdout).fetch("status")
    refute_includes stdout, "invalid-mode"
  end

  def test_live_cli_reports_unavailable_measurement_when_all_requests_return_401
    report, status = live_cli([[401, {}], [401, {}], [401, {}]])

    assert_equal 1, status.exitstatus
    assert_equal "measurement_unavailable", report.fetch("status")
    assert_equal "unavailable", report.dig("measurement", "status")
    assert_equal "no_evaluable_response", report.dig("measurement", "reason")
    assert_equal 0, report.dig("measurement", "evaluable_cases")
    assert_equal [401, 401, 401], report.fetch("cases").map { |row| row.fetch("http_status") }
    assert_equal({ "transport_failure" => 3 }, report.dig("metrics", "cases", "outcomes"))
    assert_equal 3, report.dig("metrics", "requests")
    assert_equal 4, report.dig("metrics", "questions")
    assert_equal 3, report.dig("metrics", "provider_latency_ms", "samples")
    assert_empty report.dig("metrics", "returned_models")
  end

  def test_live_cli_preserves_partial_measurement_and_failed_attempts
    response = fixture_response("priority" => "urgent")
    report, status = live_cli([[401, {}], [200, response]])

    assert status.success?
    assert_equal "completed", report.fetch("status")
    assert_equal "partial", report.dig("measurement", "status")
    assert_equal "incomplete_responses", report.dig("measurement", "reason")
    assert_equal 1, report.dig("measurement", "evaluable_cases")
    assert_equal 1, report.dig("metrics", "by_field", "priority", "applied_accuracy", "count")
    assert_equal({ "transport_failure" => 1, "complete" => 1 }, report.dig("metrics", "cases", "outcomes"))
    assert_equal 2, report.dig("metrics", "provider_latency_ms", "samples")
  end

  def test_live_cli_counts_valid_abstentions_as_available_measurement
    responses = @dataset.cases.first(3).map do |entry|
      [200, fixture_response(entry.fetch("missing").to_h { |field| [field, ABSTENTION] })]
    end
    report, status = live_cli(responses)

    assert status.success?
    assert_equal "completed", report.fetch("status")
    assert_equal "available", report.dig("measurement", "status")
    assert_equal 3, report.dig("measurement", "evaluable_cases")
    assert_equal({ "abstention" => 3 }, report.dig("metrics", "cases", "outcomes"))
    assert_equal 0, report.dig("metrics", "cases", "automatic", "count")
  end

  def test_live_cli_preserves_valid_choice_when_returned_model_is_missing
    response = fixture_response("priority" => "urgent").reject { |key| key == "model" }
    report, status = live_cli([[401, {}], [200, response]])

    assert status.success?
    assert_equal "partial", report.dig("measurement", "status")
    assert_equal 1, report.dig("measurement", "evaluable_cases")
    assert_equal 1, report.dig("metrics", "by_field", "priority", "raw_accuracy", "count")
    assert_equal 0, report.dig("metrics", "by_field", "priority", "applied_accuracy", "count")
    assert_equal "invalid_response", report.fetch("cases").last.fetch("outcome")
  end

  private

  def observe(expected, choices, received = {}, client: @controls.fixture(choices))
    entry = { "id" => "sample", "received" => received, "missing" => expected.keys, "text" => "controle",
              "expected" => expected }
    @evaluation.observe(entry, client)
  end

  def timeout_client
    HttpClient.new(api_key: "controle-offline", connection_factory: ->(*) { raise Timeout::Error })
  end

  def assert_rate(metrics, key, count, denominator)
    fraction = count.fdiv(denominator) if denominator.positive?
    assert_equal({ count: count, denominator: denominator, fraction: fraction }, metrics.fetch(key))
  end

  def reject_dataset(message)
    data = JSON.parse(File.read(DATASET_PATH))
    yield data.fetch("cases")
    with_json(data) do |path|
      error = assert_raises(F08Jev::ValidationError) do
        F08Jev::Dataset.new(dataset_path: path, catalog_path: CATALOG_PATH)
      end
      assert_match(message, error.message)
    end
  end

  def with_json(data)
    Dir.mktmpdir do |dir|
      path = File.join(dir, "sample.json")
      File.write(path, JSON.generate(data))
      yield path
    end
  end

  def cli(*args)
    Open3.capture3({ "TYPESAFE_API_KEY" => nil }, RbConfig.ruby, File.join(__dir__, "run.rb"), *args)
  end

  def fixture_response(choices)
    @controls.fixture(choices).call(state: nil, questions: choices)
  end

  def live_cli(responses)
    Dir.mktmpdir do |dir|
      fake_http_path = File.join(dir, "fake_http.rb")
      http_client = File.expand_path("../../../backend/app/services/classification/jev/http_client", __dir__)
      File.write(fake_http_path, <<~RUBY)
        require #{http_client.inspect}
        responses = #{responses.inspect}
        response_class = Struct.new(:code, :body)
        connection = Object.new
        class << connection
          attr_accessor :use_ssl, :open_timeout, :read_timeout, :write_timeout, :max_retries
          def start
            yield self
          end
        end
        connection.define_singleton_method(:request) do |_request|
          code, body = responses.shift || raise("chamada de teste inesperada")
          response_class.new(code.to_s, JSON.generate(body))
        end
        fake_connection = Module.new do
          define_method(:initialize) do |**options|
            super(**options, connection_factory: ->(*) { connection })
          end
        end
        Classification::Jev::HttpClient.prepend(fake_connection)
      RUBY
      stdout, stderr, status = Open3.capture3(
        { "TYPESAFE_API_KEY" => "chave-sintetica", "CLOUDWALK_JEV_MODEL" => nil },
        RbConfig.ruby, "-r", fake_http_path, File.join(__dir__, "run.rb"),
        "--mode", "live", "--limit", responses.size.to_s,
        "--reviewed-sha256", @dataset.metadata.dig(:dataset, :sha256), "--budget-reference", "F08-test"
      )
      assert_empty stderr
      refute_includes stdout, "chave-sintetica"
      [JSON.parse(stdout), status]
    end
  end
end
