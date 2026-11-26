require "active_support/core_ext/digest/uuid"
require "base64"

module AgentIntegration
  module E01
    class Result
      MAX_BYTES = 64.kilobytes
      IMMUTABLE_FIELDS = %w[occurred_at correlation_id case_id brand_id assignment_generation turn_id].freeze
      METADATA_FIELDS = %w[knowledge_version ontology_version policy_version source_refs handoff_rule].freeze

      attr_reader :bytes, :sha256, :metadata

      def initialize(body, request_data, snapshot)
        @bytes = Base64.strict_decode64(body.fetch("result_b64"))
        raise Error, "too_large" if @bytes.bytesize > MAX_BYTES

        @sha256 = Digest::SHA256.hexdigest(@bytes)
        unless @sha256 == body.fetch("result_sha256") && Base64.strict_encode64(@bytes) == body.fetch("result_b64")
          raise Error, "result_mismatch"
        end

        event = Contract.parse_object(@bytes)
        unless WebhookV1::Contract.valid?("AgentResult", event) && same_request?(event, request_data) &&
               body.fetch("policy_version") == snapshot.data.fetch("policy_version")
          raise Error, "result_mismatch"
        end

        validate_handoff!(event, body.fetch("handoff_rule"), request_data)
        @metadata = body.slice(*METADATA_FIELDS)
      rescue ArgumentError, JSON::ParserError, EncodingError
        raise Error, "invalid_body"
      end

      private

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
