require "digest"

module Attendances
  class ApplyAgentResult
    def initialize(data, body)
      @data = data
      @event_id = data.fetch("event_id").downcase
      @payload = data.fetch("payload")
      @digest = Digest::SHA256.hexdigest(body)
    end

    def call
      SupportCase.transaction do
        existing = AgentIntegration::AgentReceipt.find_by(event_id: @event_id)
        next duplicate(existing) if existing

        support_case = SupportCase.lock.find_by(id: @data.fetch("case_id"))
        turn = support_case&.turns&.in_flight&.lock&.first
        reason = discard_reason(support_case, turn)
        disposition = reason ? discard(support_case, reason) : apply(support_case, turn)
        AgentIntegration::AgentReceipt.create!(event_id: @event_id, body_sha256: @digest, disposition: disposition)
        { event_id: @data.fetch("event_id"), disposition: disposition }
      end
    rescue ActiveRecord::RecordNotUnique
      existing = AgentIntegration::AgentReceipt.find_by(event_id: @event_id)
      raise unless existing

      duplicate(existing)
    end

    private

    def duplicate(existing)
      if existing.body_sha256 != @digest
        raise WebhookV1::Error.new(409, "idempotency_conflict",
                                  "O evento do agente já foi aceito com outro conteúdo.")
      end

      { event_id: @data.fetch("event_id"), disposition: "duplicate" }
    end

    def discard_reason(support_case, turn)
      return "unknown_case" unless support_case
      return "non_current_turn" unless support_case.status == "ai_active" && support_case.assignee&.kind == "ai" &&
                                       turn&.assignment_generation == support_case.assignment_generation
      return "expired_turn" if turn.result_due_at && turn.result_due_at <= Time.current

      context = [support_case.brand_id, support_case.correlation_id, support_case.assignment_generation,
                 turn.id, turn.request_event_id]
      expected = @data.values_at("brand_id", "correlation_id", "assignment_generation", "turn_id") +
                 [@payload.fetch("request_event_id")]
      return "correlation_mismatch" unless context == expected.map { |value| value.is_a?(String) ? value.downcase : value }
      return unless @data.fetch("event_type") == "agent.handoff.proposed"

      eligible = support_case.messages.where(sequence: ..turn.through_sequence).pluck(:id)
      "invalid_handoff_references" unless (@payload.fetch("message_ids").map(&:downcase) - eligible).empty?
    end

    def discard(support_case, reason)
      # Um ID de marca/correlação divergente nunca é usado para alterar o caso.
      CaseAudit.create!(support_case: support_case, correlation_id: @data.fetch("correlation_id"),
                        event_type: "agent.result.discarded", actor_type: "ai",
                        from_status: support_case&.status, to_status: support_case&.status, reason: reason,
                        details: { event_id: @event_id, case_id: @data.fetch("case_id"),
                                   turn_id: @data.fetch("turn_id"), request_event_id: @payload.fetch("request_event_id") })
      "discarded"
    end

    def apply(support_case, turn)
      old_status = support_case.status
      actor_id = support_case.assignee_id
      newer_messages = support_case.messages.where(author_type: "customer").where("sequence > ?", turn.through_sequence).exists?
      if @payload.key?("text")
        support_case.append_message!(type: "ai", author_id: support_case.assignee_id,
                                     text: @payload.fetch("text"), source_event_id: @event_id)
      end
      turn.update!(completed_at: Time.current, result_event_id: @event_id)
      attributes = { integration_status: "idle", blocking_reason: nil }
      case @data.fetch("event_type")
      when "agent.resolve.proposed"
        unless newer_messages
          attributes.merge!(status: "resolved", assignee: nil, resolved_at: Time.current,
                            assignment_generation: support_case.assignment_generation + 1)
        end
      when "agent.handoff.proposed"
        attributes.merge!(status: "waiting_human", assignee: nil, human_queue_since: Time.current,
                          handoff: @payload.slice("summary", "message_ids"),
                          assignment_generation: support_case.assignment_generation + 1)
      end
      support_case.advance!(**attributes)
      support_case.audit!(@data.fetch("event_type"), actor_type: "ai",
                          actor_id: actor_id, from_status: old_status,
                          event_id: @event_id, turn_id: turn.id, request_event_id: turn.request_event_id)
      AgentIntegration::QueueTurn.call(support_case) if newer_messages && support_case.status == "ai_active"
      "applied"
    end
  end
end
