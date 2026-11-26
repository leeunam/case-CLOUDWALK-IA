# frozen_string_literal: true

require "digest"
require "bigdecimal"

# Executado pelo checker do repositório. Não faz chamadas de rede nem carrega os modelos.
class ClassificationHttpFixtures
  FIELDS = %w[category priority].freeze
  HASHES = %w[package_sha256 model_sha256 capture_policy_sha256 decision_policy_sha256].freeze
  PINS_SHA = "a39450eec74c1d32915ec98f1510aecc11428281633ac9cd9cbb913d200e6897"
  VECTOR_SHA = "0cadca6fc5e2291b3e471df649d098123bf01cb8b422803c45b6cb9f22d63807"
  ERRORS = {
    422 => %w[invalid_request unsupported_catalog text_out_of_scope],
    502 => %w[invalid_worker_frame worker_failure], 503 => %w[busy not_ready], 504 => %w[processing_timeout]
  }.freeze

  def initialize(directory)
    @root = directory.join("../../..").realpath
    @fixtures = directory.join("fixtures")
    @pins = read(directory.join("pins.json"))
    schema = read(directory.join("v1.json"))
    report_errors(JSONSchemer.validate_schema(schema).to_a, "classification-http/v1.json")
    @validator = JSONSchemer.schema(schema, format: true)
    @canonical = read(@root.join("script/f08/jev/catalog.json"))
  end

  def check
    verify_pins
    request = read(@fixtures.join("request.json"))
    ensure_valid(valid_request?(request), "pedido")
    check_vector(request)
    %w[complete review error].each do |outcome|
      response = read(@fixtures.join("response-#{outcome}.json"))
      frame = @fixtures.join("#{outcome}.jsonl").binread
      ensure_valid(response["outcome"] == outcome && valid_response?(request, response, frame), "resposta #{outcome}")
      check_mutations(request, response, frame) if outcome == "complete"
    end
    check_partial_application
    ERRORS.each do |status, codes|
      codes.each do |code|
        error = read(@fixtures.join("#{status}-#{code.tr('_', '-')}.json"))
        ensure_valid(error["error"] == code && valid?("Error#{status}", error), "recusa #{status} #{code}")
        ensure_valid((ERRORS.keys - [status]).none? { |other| valid?("Error#{other}", error) }, "status da recusa")
      end
    end
  end

  private

  def ensure_valid(condition, label)
    abort "Contrato HTTP privado inválido em #{label}" unless condition
  end

  def read(path)
    JSON.parse(path.read, allow_duplicate_key: false)
  end

  def valid?(name, object)
    @validator.ref("#/$defs/#{name}").valid?(object)
  end

  def verify_pins
    pin_path = @fixtures.parent.join("pins.json")
    ensure_valid(Digest::SHA256.file(pin_path).hexdigest == PINS_SHA, "pins da adoção")
    catalog = @root.join("script/f08/jev/catalog.json")
    ensure_valid(Digest::SHA256.file(catalog).hexdigest == @pins["catalog_file_sha256"] &&
                 @canonical["version"] == @pins["ipc_catalog_version"], "catálogo IPC")
    inventory = @pins.fetch("worker_files")
    runtime = @pins.fetch("runtime_files")
    ensure_valid(inventory.size == 17 && runtime.size == 3, "inventários de execução")
    inventory.merge(runtime).each do |path, digest|
      ensure_valid(Digest::SHA256.file(@root.join(path)).hexdigest == digest, path)
    end
  end

  def canonical_bytes(catalog)
    JSON.generate(catalog.sort.to_h.transform_values { |items| items.sort.to_h }).encode(Encoding::UTF_8)
  end

  def check_vector(request)
    bytes = canonical_bytes(request.fetch("catalog"))
    ensure_valid(bytes.b == @fixtures.join("catalog-canonical.json").binread && bytes.bytesize == 449 &&
                 Digest::SHA256.hexdigest(bytes) == VECTOR_SHA, "vetor Ruby de catálogo")
    changed = request["catalog"].merge("category" => request["catalog"]["category"].merge("pix" => request["catalog"]["category"]["pix"] + "!"))
    ensure_valid(Digest::SHA256.hexdigest(canonical_bytes(changed)) != VECTOR_SHA, "mutação da descrição")
    changed_version = request.merge("catalog_version" => request["catalog_version"] + 1)
    ensure_valid(canonical_bytes(changed_version["catalog"]) == bytes, "versão operacional independente")
  end

  def valid_request?(request)
    valid?("Request", request) && request.fetch("catalog_version").instance_of?(Integer) &&
      FIELDS.all? do |name|
        map = request.fetch("catalog").fetch(name)
        value = request.fetch("received").fetch(name)
        (value.nil? || map.key?(value)) && map.all? { |code, desc| @canonical.fetch(name)[code] == desc }
      end
  end

  def valid_response?(request, response, raw_frame)
    return false unless valid_request?(request) && valid?("Response", response)
    return false unless response["catalog_version"].instance_of?(Integer) &&
      response.values_at("contract_version", "id", "catalog_version") == request.values_at("contract_version", "id", "catalog_version")
    return false unless response["catalog_sha256"] == Digest::SHA256.hexdigest(canonical_bytes(request["catalog"])) &&
      response.slice(*HASHES) == @pins.slice(*HASHES) && response["raw_frame_sha256"] == Digest::SHA256.hexdigest(raw_frame)
    return false unless raw_frame.end_with?("\n") && raw_frame.count("\n") == 1 && !raw_frame.include?("\r")

    frame = JSON.parse(raw_frame, allow_duplicate_key: false)
    accepted = {}
    decisions = FIELDS.map do |name|
      field = response.fetch("fields").fetch(name)
      call = response.fetch("calls").fetch(name)
      observed = frame.fetch("fields").fetch(name)
      return false unless call.instance_of?(Integer) && call == frame.fetch("calls").fetch(name)
      return false unless field.slice("vector", "raw", "margin") == observed.slice("vector", "raw", "margin")

      expected = if request.fetch("received").fetch(name)
        return false unless call.zero?
        %w[provided provided]
      else
        return false unless call == 1 && field["cut"] == @pins["decision_policy"].fetch(name)
        if field["vector"].nil?
          ["error", observed.fetch("reason")]
        else
          evaluate_vector(name, field, request["catalog"].fetch(name))
        end
      end
      return false unless field.values_at("decision", "reason") == expected

      accepted[name] = field["raw"] if field["decision"] == "accept"
      field["decision"]
    end
    outcome = if decisions.include?("error")
      "error"
    elsif decisions.include?("review")
      "review"
    else
      "complete"
    end
    response["outcome"] == outcome && response["applied"] == (outcome == "complete" ? accepted : {})
  end

  def evaluate_vector(name, field, catalog)
    vector = field.fetch("vector")
    classes = vector.fetch("classes")
    scores = vector.fetch("scores").map { |n| BigDecimal(n.to_s) }
    return unless classes == @pins["class_order"].fetch(name) && (scores.sum - 1).abs <= BigDecimal("1e-6")

    top, second = scores.max(2)
    label = classes.fetch(scores.index(top))
    margin = top - second
    return unless field["raw"] == label && (BigDecimal(field.fetch("margin").to_s) - margin).abs <= BigDecimal("1e-15")
    return %w[review raw_review] if label == "informacao_insuficiente"
    return %w[review inactive_label] unless catalog.key?(label)
    return %w[review below_tau] if top < BigDecimal(field["cut"]["tau"].to_s)
    return %w[review low_margin] if margin <= BigDecimal(field["cut"]["delta"].to_s)

    %w[accept accepted]
  end

  def check_partial_application
    request = read(@fixtures.join("request-both.json"))
    response = read(@fixtures.join("response-complete-both.json"))
    frame = @fixtures.join("complete-both.jsonl").binread
    ensure_valid(request.fetch("received") == { "category" => nil, "priority" => nil } &&
                 response.fetch("applied") == { "category" => "pix", "priority" => "urgent" } &&
                 valid_response?(request, response, frame), "complemento integral de dois ausentes")

    partial = response.merge("applied" => response.fetch("applied").except("priority"))
    ensure_valid(valid?("Response", partial), "aplicação parcial estruturalmente válida")
    ensure_valid(!valid_response?(request, partial, frame), "aplicação parcial de dois aceites")
  end

  def check_mutations(request, response, frame)
    [
      response.merge("id" => "00000000-0000-4000-8000-000000000000"),
      response.merge("catalog_version" => request["catalog_version"] + 1),
      response.merge("catalog_version" => request["catalog_version"].to_f),
      response.merge("catalog_sha256" => "a" * 64),
      response.merge("raw_frame_sha256" => Digest::SHA256.hexdigest(frame.chomp)),
      response.merge("calls" => response["calls"].merge("category" => 1)),
      response.merge("calls" => response["calls"].merge("priority" => 1.0)),
      response.merge("applied" => {}),
      response.merge("outcome" => "review", "applied" => {})
    ].each { |bad| ensure_valid(!valid_response?(request, bad, frame), "mutação do retorno") }
    ensure_valid(!valid_request?(request.merge("received" => { "category" => "pix", "priority" => "basic" })), "pedido completo")
    ensure_valid(!valid_request?(request.merge("received" => { "category" => "terminal", "priority" => nil })), "código ausente no snapshot")
    changed_catalog = request["catalog"].merge("category" => request["catalog"]["category"].merge("pix" => "Outra descrição."))
    ensure_valid(!valid_request?(request.merge("catalog" => changed_catalog)), "catálogo incompatível")
    ensure_valid(!valid_request?(request.merge("catalog_version" => 7.0)), "versão literal")
  end
end
