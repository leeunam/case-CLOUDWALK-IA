require "digest"
require "json"
require_relative "../../../backend/app/services/classification/catalog"
require_relative "../../../backend/app/services/classification/jev/classifier"

module F08Jev
  FIELDS = %w[category priority].freeze
  ABSTENTION = Classification::Jev::Classifier::ABSTENTION
  SPLITS = { ["category"] => 20, ["priority"] => 20, FIELDS => 20 }.freeze
  STRATA = %w[rotina urgente ambiguo].freeze

  class ValidationError < StandardError; end

  class Dataset
    attr_reader :cases, :catalog, :metadata, :distribution

    def initialize(dataset_path:, catalog_path:)
      dataset, dataset_hash = read_json(dataset_path)
      @catalog, catalog_hash = read_json(catalog_path)
      validate_catalog
      require_valid(dataset.is_a?(Hash) && dataset.keys.sort == %w[cases language review version] &&
                    version?(dataset["version"]) && dataset["review"] == "provisional" &&
                    dataset["language"] == "pt-BR" && dataset["cases"].is_a?(Array),
                    "manifesto do dataset inválido")

      @cases = dataset.fetch("cases")
      @cases.each_with_index { |entry, index| validate_case(entry, index + 1) }
      require_valid(@cases.map { |entry| entry.fetch("id") }.uniq.size == @cases.size, "IDs duplicados")
      texts = @cases.map { |entry| entry.fetch("text").strip.downcase.gsub(/[[:space:]]+/, " ") }
      require_valid(texts.uniq.size == @cases.size, "relatos duplicados")

      @distribution = @cases.map { |entry| entry.fetch("missing") }.tally
      require_valid(@distribution == SPLITS, "distribuição esperada: 20/20/20")
      SPLITS.each_key do |split|
        strata = @cases.filter_map { |entry| entry.fetch("stratum") if entry.fetch("missing") == split }
        require_valid((STRATA - strata).empty?, "faltam estratos em #{split.join('+')}")
      end

      @metadata = {
        dataset: { version: dataset.fetch("version"), sha256: dataset_hash, review: dataset.fetch("review"),
                   language: dataset.fetch("language") },
        catalog: { version: @catalog.fetch("version"), sha256: catalog_hash }
      }
    end

    private

    def read_json(path)
      bytes = File.binread(path)
      [JSON.parse(bytes), Digest::SHA256.hexdigest(bytes)]
    rescue JSON::ParserError, EncodingError
      raise ValidationError, "JSON inválido em #{File.basename(path)}"
    end

    def validate_catalog
      product = Classification::Catalog
      expected = { "category" => product::CATEGORY_DESCRIPTIONS, "priority" => product::PRIORITIES }
      require_valid(@catalog.is_a?(Hash) && @catalog.keys.sort == %w[category priority version] &&
                    version?(@catalog["version"]) && @catalog.slice(*FIELDS) == expected,
                    "catálogo fixado diverge do catálogo do produto")
    end

    def validate_case(entry, line)
      keys = %w[expected id missing rationale received stratum text]
      require_valid(entry.is_a?(Hash) && entry.keys.sort == keys && entry["id"].is_a?(String) &&
                    entry["id"].match?(/\Ajev-\d{3}\z/) && nonblank?(entry["text"]) &&
                    nonblank?(entry["rationale"]) && STRATA.include?(entry["stratum"]), "caso #{line} inválido")

      id, received, missing, expected, stratum = entry.values_at("id", "received", "missing", "expected", "stratum")
      require_valid(SPLITS.key?(missing) && received.is_a?(Hash) && expected.is_a?(Hash) &&
                    received.keys.sort == FIELDS - missing && expected.keys.sort == missing,
                    "#{id}: campos recebidos, omitidos e esperados inconsistentes")
      require_valid(received.all? { |field, value| @catalog.fetch(field).key?(value) },
                    "#{id}: campo recebido fora do catálogo")
      require_valid(expected.all? { |field, value| value == ABSTENTION || @catalog.fetch(field).key?(value) },
                    "#{id}: rótulo fora do catálogo")
      require_valid((stratum == "ambiguo") == expected.value?(ABSTENTION), "#{id}: abstenção e estrato inconsistentes")
      priority = expected.fetch("priority") { received.fetch("priority") }
      unless stratum == "ambiguo"
        require_valid((stratum == "urgente") == (priority == "urgent"), "#{id}: prioridade e estrato inconsistentes")
      end
    end

    def require_valid(condition, message)
      raise ValidationError, message unless condition
    end

    def version?(value)
      value.is_a?(String) && value.match?(/\A\d+\.\d+\.\d+\z/)
    end

    def nonblank?(value)
      value.is_a?(String) && value.valid_encoding? && !value.strip.empty?
    end
  end
end
