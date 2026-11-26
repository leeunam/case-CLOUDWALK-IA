require "digest"

module AgentIntegration
  module E01
    class Round
      IDENTITY = %w[event_id case_id brand_id correlation_id turn_id assignment_generation].freeze

      attr_reader :outbox, :turn, :support_case, :request_data

      # O orçamento já está bloqueado. As travas de domínio seguem marca, caso,
      # rodada e outbox, na mesma ordem das operações de atendimento.
      def initialize(request_event_id)
        @outbox = AgentOutbox.find_by(event_id: request_event_id)
        raise Error, "not_found" unless @outbox

        @turn = @outbox.agent_turn
        @support_case = @turn.support_case
        Attendances::HumanLocks.brand!(@support_case.brand_id)
        @support_case.lock!
        @turn.lock!
        @outbox.lock!
      end

      def verify_origin!(sha256)
        @request_data = Contract.parse_object(@outbox.body)
        expected = [@outbox.event_id, @support_case.id, @support_case.brand_id, @support_case.correlation_id,
                    @turn.id, @turn.assignment_generation]
        unless sha256 == body_sha256 && @request_data.values_at(*IDENTITY) == expected &&
               @outbox.event_id == @turn.request_event_id && @outbox.agent_turn_id == @turn.id &&
               @turn.support_case_id == @support_case.id && WebhookV1::Contract.valid?("AgentTurnRequested", @request_data)
          raise Error, "request_mismatch"
        end
      rescue JSON::ParserError, EncodingError
        raise Error, "request_mismatch"
      end

      def body_sha256
        Digest::SHA256.hexdigest(@outbox.body)
      end

      def current?(now)
        @turn.completed_at.nil? && @support_case.status == "ai_active" && @support_case.assignee&.kind == "ai" &&
          @turn.assignment_generation == @support_case.assignment_generation &&
          (@turn.result_due_at.nil? || @turn.result_due_at > now)
      end

      def dispatchable!(now)
        raise Error, "turn_stale" unless current?(now) && @outbox.failed_at.nil?
        raise Error, "publication_pending" unless @outbox.published_at && @turn.result_due_at
      end

      def record!(reason, now, failure: false)
        current_failure = failure && current?(now)
        if current_failure
          @turn.update!(completed_at: now)
          @support_case.advance!(integration_status: "failed", blocking_reason: "e01_#{reason}")
        end

        @support_case.audit!(current_failure ? "agent.execution.failed" : "agent.execution.#{failure ? 'obsolete' : 'discarded'}",
                             actor_type: "system", reason: reason, event_id: @outbox.event_id, turn_id: @turn.id)
      end
    end
  end
end
