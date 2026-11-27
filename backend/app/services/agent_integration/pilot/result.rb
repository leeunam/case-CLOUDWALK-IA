require "active_support/core_ext/digest/uuid"
require "base64"

module AgentIntegration
  module Pilot
    class Result
      MAX_BYTES = 64.kilobytes
      BASE64_BOUNDARY = ((MAX_BYTES + 2) / 3) * 4
      IMMUTABLE_FIELDS = %w[occurred_at correlation_id case_id brand_id assignment_generation turn_id].freeze
      METADATA_FIELDS = %w[knowledge_version ontology_version policy_version source_refs handoff_rule].freeze

      attr_reader :bytes, :sha256, :metadata

      # No limite do schema, o padding decide se o resultado cabe em 64 KiB.
      # Acima dele, verificar a forma canônica antes de classificar o excesso.
      def self.check_encoded_size!(encoded)
        decode!(encoded) if encoded.bytesize >= BASE64_BOUNDARY
      end

      def self.decode!(encoded)
        bytes = Base64.strict_decode64(encoded)
        raise Error, "invalid_body" unless Base64.strict_encode64(bytes) == encoded
        raise Error, "too_large" if bytes.bytesize > MAX_BYTES

        bytes
      rescue ArgumentError
        raise Error, "invalid_body"
      end
      def initialize(body, request_data, snapshot)
        @bytes = self.class.decode!(body.fetch("result_b64"))
        @sha256 = Digest::SHA256.hexdigest(@bytes)
        raise Error, "result_mismatch" unless @sha256 == body.fetch("result_sha256")

        event = Contract.parse_object(@bytes)
        unless WebhookV1::Contract.valid?("AgentResult", event) && same_request?(event, request_data) &&
               body.fetch("policy_version") == snapshot.data.fetch("policy_version") && persistable_text?(event)
          raise Error, "result_mismatch"
        end

        validate_handoff!(event, body.fetch("handoff_rule"), request_data)
        @metadata = body.slice(*METADATA_FIELDS)
      rescue JSON::ParserError, EncodingError
        raise Error, "invalid_body"
      end

      private

      def persistable_text?(event)
        event.fetch("payload").values_at("text", "summary").compact.none? { |text| text.include?("\0") }
      end

      def same_request?(event, request_data)
        request_id = request_data.fetch("event_id")
        expected_id = Digest::UUID.uuid_v5(Digest::UUID::URL_NAMESPACE, "cloudwalk:e01-luna-v1:#{request_id}")

        event.fetch("event_id") == expected_id && event.fetch("payload").fetch("request_event_id") == request_id &&
          event.values_at(*IMMUTABLE_FIELDS) == request_data.values_at(*IMMUTABLE_FIELDS) &&
          event.fetch("assignment_generation").is_a?(Integer)
      end

      def validate_handoff!(event, rule, request_data)
        if event.fetch("event_type") != "agent.handoff.proposed"
          raise Error, "result_mismatch" if rule

          return
        end

        raise Error, "result_mismatch" unless rule

        payload = event.fetch("payload")
        ids = payload.fetch("message_ids")
        messages = request_data.fetch("payload").fetch("history").select { |message| ids.include?(message.fetch("id")) }
        if ids != messages.map { |message| message.fetch("id") } ||
           payload.fetch("summary") != messages.map { |message| message.fetch("text") }.join("\n")
          raise Error, "result_mismatch"
        end
      end
    end
  end
end
