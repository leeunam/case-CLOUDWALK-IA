require "json_schemer"

module AgentIntegration
  module E01
    module Contract
      UUID = /\A[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\z/
      SHA256 = /\A[0-9a-f]{64}\z/
      SCHEMERS = Concurrent::Map.new

      class UniqueKeys < Hash
        def []=(key, value)
          raise JSON::ParserError, "Duplicate key" if key?(key)

          super
        end
      end

      def self.parse_object(raw)
        text = raw.dup.force_encoding(Encoding::UTF_8)
        raise JSON::ParserError unless text.valid_encoding?

        value = JSON.parse(text, object_class: UniqueKeys, allow_nan: false)
        raise JSON::ParserError unless value.is_a?(Hash)

        value
      end

      def self.valid?(definition, value)
        SCHEMERS.compute_if_absent(definition) do
          paths = [Rails.root.join("../docs/contratos"), Pathname.new("/workspace/docs/contratos")]
          schema_path = paths.map { |path| path.join("e01/ledger.schema.json") }.find(&:file?)
          raise "Schema privado E01 não encontrado." unless schema_path

          schema = JSON.parse(schema_path.read).slice("$schema", "$defs")
          JSONSchemer.schema(schema.merge("$ref" => "#/$defs/#{definition}"), format: true)
        end.valid?(value)
      end

      def self.parse_operation!(operation, bytes)
        data = parse_object(bytes)
        raise Error, "invalid_body" unless valid?(operation, data)
        %w[owner_id lease_token].each do |field|
          raise Error, "invalid_body" if data.key?(field) && !UUID.match?(data.fetch(field))
        end
        %w[request_sha256 result_sha256].each do |field|
          raise Error, "invalid_body" if data.key?(field) && !SHA256.match?(data.fetch(field))
        end
        data
      rescue JSON::ParserError, EncodingError
        raise Error, "invalid_body"
      end
    end
  end
end
