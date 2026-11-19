require "json"
require "concurrent/map"

module WebhookV1
  module Contract
    UUID = /\A[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\z/i
    SCHEMERS = Concurrent::Map.new

    def self.parse!(body, definition)
      data = JSON.parse(body)
      unless valid?(definition, data)
        raise Error.new(422, "invalid_payload", "Corpo fora do contrato #{definition}.")
      end

      data
    rescue JSON::ParserError, EncodingError, ActionDispatch::Http::Parameters::ParseError
      raise Error.new(422, "invalid_payload", "JSON inválido.")
    end

    def self.valid?(definition, data)
      SCHEMERS.compute_if_absent(definition) do
        require "json_schemer"

        paths = [Rails.root.join("../docs/contratos"), Pathname.new("/workspace/docs/contratos")]
        schema_path = paths.map { |path| path.join("schemas/v1.json") }.find(&:file?)
        raise "Schema v1 dos webhooks não encontrado." unless schema_path

        document = JSON.parse(schema_path.read)
        JSONSchemer.schema(document.merge("$ref" => "#/$defs/#{definition}"), format: true)
      end.valid?(data)
    end
  end
end
