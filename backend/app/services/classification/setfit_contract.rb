require "bigdecimal"
require "digest"
require "json"
require "json_schemer"

module Classification
  class SetfitContract
    class Invalid < StandardError; end
    class Unavailable < StandardError; end

    # SHA-256 dos mapas de script/f08/jev/catalog.json na serialização canônica do contrato HTTP.
    APPROVED_CATALOG_SHA256 = "0eeeeb80ca60a5bfef03a01100fcf7d9399b293a937ec1d9c5498c97bd572fb4"
    PIN_FILE_SHA256 = "a39450eec74c1d32915ec98f1510aecc11428281633ac9cd9cbb913d200e6897"
    IDENTITY_KEYS = %w[contract_version package_sha256 model_sha256 capture_policy_sha256 decision_policy_sha256].freeze
    FIELDS = %w[category priority].freeze

    def self.current
      @current ||= new(ENV.fetch("CLASSIFICATION_CONTRACT_DIR", Rails.root.join("../docs/contratos/classification-http")))
    end

    def self.catalog_sha256(catalog)
      Digest::SHA256.hexdigest(JSON.generate(catalog.sort.to_h.transform_values { |items| items.sort.to_h }))
    end

    def initialize(directory)
      bytes = File.binread(File.join(directory, "pins.json"))
      raise Unavailable unless Digest::SHA256.hexdigest(bytes) == PIN_FILE_SHA256

      @pins = JSON.parse(bytes)
      @schema = JSONSchemer.schema(JSON.parse(File.read(File.join(directory, "v1.json"))))
    rescue SystemCallError, JSON::ParserError
      raise Unavailable
    end

    def identities
      @pins.slice(*IDENTITY_KEYS)
    end

    def compatible?(catalog)
      approved = { "category" => Catalog::CATEGORY_DESCRIPTIONS, "priority" => Catalog::PRIORITIES }
      return false unless self.class.catalog_sha256(approved) == APPROVED_CATALOG_SHA256

      FIELDS.all? do |field|
        catalog.fetch(field).all? { |code, description| approved[field].key?(code) && approved[field][code] == description }
      end
    end

    def valid_schema?(definition, body)
      @schema.ref("#/$defs/#{definition}").valid?(body)
    end

    def decode(status, bytes, request, snapshot)
      raise Invalid unless bytes.force_encoding(Encoding::UTF_8).valid_encoding?
      body = JSON.parse(bytes, decimal_class: BigDecimal, allow_duplicate_key: false, allow_nan: false)
      if status != 200
        raise Invalid unless [422, 502, 503, 504].include?(status) && valid_schema?("Error#{status}", body)
        return Result.review(body.fetch("error"), evidence: { "http_status" => status }, retryable: status == 503)
      end

      raise Invalid unless valid_schema?("Response", body)
      raise Invalid unless body.slice(*IDENTITY_KEYS) == snapshot.fetch("identities") &&
        body["id"] == request.fetch("id") && body["catalog_version"].is_a?(Integer) && body["catalog_version"] == request.fetch("catalog_version") &&
        body["catalog_sha256"] == snapshot.fetch("catalog_sha256")

      received = request.fetch("received")
      outcomes = FIELDS.to_h do |field|
        observation = body.fetch("fields").fetch(field)
        verify_field!(field, observation, received[field], body.fetch("calls")[field], request.fetch("catalog")[field])
        [field, observation.fetch("decision")]
      end
      outcome = if outcomes.value?("error") then "error"
      elsif outcomes.value?("review") then "review"
      else "complete"
      end
      raise Invalid unless body.fetch("outcome") == outcome
      applied = if outcome == "complete"
        outcomes.filter_map { |field, decision| [field, body.dig("fields", field, "raw")] if decision == "accept" }.to_h
      else
        {}
      end
      raise Invalid unless body.fetch("applied") == applied

      evidence = body.merge("http_status" => status)
      return complete(received, applied, evidence) if outcome == "complete"

      issues = outcomes.filter_map do |field, decision|
        [field, body.dig("fields", field, "reason")] if %w[review error].include?(decision)
      end.to_h
      Result.new(status: :review, classification: {}, issues: issues, evidence: evidence, retryable: false, retry_after_seconds: nil)
    end

    def complete(received, applied, evidence = nil)
      classification = {}
      received.each do |field, value|
        classification[field.to_sym] = value || applied.fetch(field)
        classification[:"#{field}_source"] = value ? "channel" : "setfit"
      end
      Result.new(status: :complete, classification: classification, issues: {}, evidence: evidence,
                 retryable: false, retry_after_seconds: nil)
    end

    private

    def verify_field!(field, observation, received, calls, active)
      decision = observation.fetch("decision")
      raise Invalid unless calls.is_a?(Integer) && calls == (received.nil? ? 1 : 0)
      if received
        raise Invalid unless decision == "provided"
        return
      end

      cut = @pins.fetch("decision_policy").fetch(field).transform_values { |n| BigDecimal(n.to_s) }
      raise Invalid unless observation.fetch("cut") == cut
      return if decision == "error"

      vector = observation.fetch("vector")
      raise Invalid unless vector && vector.fetch("classes") == @pins.fetch("class_order").fetch(field)
      scores = vector.fetch("scores")
      raise Invalid unless (scores.sum - 1).abs <= BigDecimal("1e-6")
      score, runner_up = scores.max(2)
      raw = vector.fetch("classes")[scores.index(score)]
      margin = score - runner_up
      raise Invalid unless observation.fetch("raw") == raw && (observation.fetch("margin") - margin).abs <= BigDecimal("1e-15")

      reason = if raw == Jev::Classifier::ABSTENTION then "raw_review"
      elsif !active.key?(raw) then "inactive_label"
      elsif score < cut.fetch("tau") then "below_tau"
      elsif margin <= cut.fetch("delta") then "low_margin"
      else "accepted"
      end
      raise Invalid unless observation.fetch("reason") == reason && decision == (reason == "accepted" ? "accept" : "review")
    end
  end
end
