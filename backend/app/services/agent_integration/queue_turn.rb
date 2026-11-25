module AgentIntegration
  module QueueTurn
    # Executado na transação que mantém o atendimento bloqueado.
    def self.call(support_case)
      history = support_case.messages.order(:sequence).map(&:contract_data)
      now = Time.current
      request_id = SecureRandom.uuid
      turn = support_case.turns.create!(request_event_id: request_id,
                                       assignment_generation: support_case.assignment_generation,
                                       through_sequence: history.last.fetch(:sequence))
      body = JSON.generate(
        schema_version: "1.0", event_type: "agent.turn.requested", event_id: request_id,
        occurred_at: now.iso8601(6), correlation_id: support_case.correlation_id,
        case_id: support_case.id, brand_id: support_case.brand_id,
        assignment_generation: turn.assignment_generation, turn_id: turn.id,
        payload: { classification: support_case.classification, history: history }
      )
      AgentOutbox.create!(agent_turn: turn, event_id: request_id, body: body, next_attempt_at: now)
      support_case.advance!(integration_status: "pending_delivery")
      support_case.audit!("agent.turn.requested", actor_type: "system", event_id: request_id, turn_id: turn.id)
    end
  end
end
