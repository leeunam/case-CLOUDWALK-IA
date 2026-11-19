require "digest"

module Attendances
  class ApplyCaseCommand
    def initialize(user:, case_id:, operation:, key:, data:)
      @user = user
      @case_id = case_id
      @operation = operation
      @key = key.to_s
      @data = data
      @digest = Digest::SHA256.hexdigest(JSON.generate(data.sort.to_h))
    end

    def call
      unless @key.present? && @key.length <= 128
        raise WebhookV1::Error.new(422, "invalid_idempotency_key", "Informe uma chave de idempotência de até 128 caracteres.")
      end

      SupportCase.transaction do
        snapshot = Visibility.new(@user).cases.find(@case_id)
        HumanLocks.brand!(snapshot.brand_id)
        snapshot.reload
        destination = Operations::Attendant.find_by(id: @data["destination_assignee_id"]) if transfer?
        users = HumanLocks.users!([@user.id, snapshot.assignee&.user_id, destination&.user_id].compact).index_by(&:id)
        actor = users.fetch(@user.id)
        record = Visibility.new(actor).cases.lock.find(@case_id)
        receipts = record.command_receipts.where(user: actor, operation: @operation, key: @key)
        existing = receipts.first
        authorize!(actor, record, existing)
        next replay(existing) if existing

        unless record.version == @data.fetch("expected_version")
          raise WebhookV1::Error.new(409, "version_conflict", "O atendimento foi atualizado.", { current_version: record.version })
        end

        message = apply!(record, actor, users, destination)
        result = @operation == "message" ? { case: record.contract_data, message: message.contract_data } : record.contract_data
        receipts.create!(body_sha256: @digest, response_body: result)
        result
      end
    end

    private

    def transfer?
      @operation == "action" && @data["type"] == "transfer"
    end

    def human_action?
      @operation == "message" || %w[wait_for_customer resolve].include?(@data["type"])
    end

    def authorize!(actor, record, existing)
      if human_action?
        attendant = actor.attendant
        owns_case = attendant && record.assignee_id == attendant.id
        if existing && record.status == "resolved" && attendant
          owns_case = record.audits.exists?(event_type: "case.human.resolved", actor_id: attendant.id)
        end
        allowed = actor.role == "analyst" && actor.active_brand_id == record.brand_id && record.queue.active? && owns_case
      else
        allowed = actor.role == "supervisor"
      end
      return if allowed

      raise WebhookV1::Error.new(403, "forbidden", "Ação proibida para este atendimento.")
    end

    def replay(receipt)
      if receipt.body_sha256 != @digest
        raise WebhookV1::Error.new(409, "idempotency_conflict", "A chave já foi usada com outro conteúdo.")
      end

      receipt.response_body
    end

    def apply!(record, actor, users, destination)
      if human_action?
        apply_human_action!(record, actor)
      elsif transfer?
        transfer!(record, actor, users, destination)
      else
        recover_agent!(record, actor)
      end
    end

    def apply_human_action!(record, actor)
      conflict! unless record.status == "human_active"

      assignee = record.assignee_id
      message = if @data.key?("text")
        record.append_message!(type: "human", author_id: assignee, text: @data.fetch("text"),
                               source_event_id: SecureRandom.uuid)
      end
      if @operation == "message"
        record.advance!
        record.audit!("case.human.replied", actor_type: "human", actor_id: assignee, message_id: message.id)
        return message
      end

      if @data["type"] == "wait_for_customer"
        record.advance!(status: "waiting_customer")
        record.audit!("case.human.waiting_customer", actor_type: "human", actor_id: assignee,
                      from_status: "human_active", message_id: message.id)
      else
        record.advance!(status: "resolved", assignee: nil, resolved_at: Time.current,
                        assignment_generation: record.assignment_generation + 1)
        record.audit!("case.human.resolved", actor_type: "human", actor_id: assignee,
                      from_status: "human_active", reason: @data["reason"], previous_assignee_id: assignee)
      end
      AnalystOperation.finish_switch!(actor)
      DistributeHumanWorkJob.schedule(record.brand_id)
    end

    def transfer!(record, actor, users, destination)
      conflict! unless SupportCase::HUMAN_STATUSES.include?(record.status)

      queue = Operations::SupportQueue.find_by(id: @data.fetch("destination_queue_id"), brand_id: record.brand_id, active: true)
      invalid_destination!("Fila indisponível na marca do atendimento.") unless queue
      waiting = record.status == "waiting_customer"
      target = users[destination&.user_id]
      if @data["destination_assignee_id"]
        invalid_destination!("Atendente humano indisponível.") unless target && destination.kind == "human"
        reason = HumanEligibility.new(target).block_reason(record, queue: queue, activates: !waiting)
        invalid_destination!("Atendente inelegível para o destino.", { reason: reason }) if reason
      end

      old_status = record.status
      old_queue = record.queue_id
      old_assignee = record.assignee_id
      origin = users[record.assignee&.user_id]
      changed_owner = old_assignee != destination&.id
      status = waiting ? "waiting_customer" : (destination ? "human_active" : "waiting_human")
      since = record.human_queue_since || Time.current if status == "waiting_human"
      record.advance!(status: status, assignee: destination, queue: queue, blocking_reason: nil, human_queue_since: since,
                      assignment_generation: record.assignment_generation + (changed_owner ? 1 : 0))
      target.update!(last_human_assignment_at: Time.current) if target && changed_owner
      record.audit!("case.human.transferred", actor_type: "supervisor", actor_id: actor.id,
                    from_status: old_status, reason: @data.fetch("reason"), previous_queue_id: old_queue,
                    queue_id: queue.id, previous_assignee_id: old_assignee, assignee_id: destination&.id)
      AnalystOperation.finish_switch!(origin) if origin
      DistributeHumanWorkJob.schedule(record.brand_id)
    end

    def recover_agent!(record, actor)
      conflict! unless record.status == "ai_active" && record.integration_status == "failed"

      turn = record.turns.in_flight.lock.first
      if @data["type"] == "force_handoff"
        turn&.update!(completed_at: Time.current)
        assignee_id = record.assignee_id
        record.advance!(**record.handoff_attributes(summary: @data.fetch("summary"), message_ids: record.messages.order(:sequence).ids))
        record.audit!("case.agent.force_handoff", actor_type: "supervisor", actor_id: actor.id,
                      from_status: "ai_active", reason: @data.fetch("reason"), previous_assignee_id: assignee_id)
        DistributeHumanWorkJob.schedule(record.brand_id)
      else
        if turn
          turn.outbox.lock!.update!(failed_at: nil, attempts: 0, next_attempt_at: Time.current, claim_token: nil)
          record.advance!(integration_status: "pending_delivery", blocking_reason: nil)
        else
          record.update!(blocking_reason: nil)
          AgentIntegration::QueueTurn.call(record)
        end
        record.audit!("case.agent.retry", actor_type: "supervisor", actor_id: actor.id, reason: @data.fetch("reason"))
      end
    end

    def conflict!
      raise WebhookV1::Error.new(409, "invalid_transition", "Ação incompatível com o estado do atendimento.")
    end

    def invalid_destination!(message, details = {})
      raise WebhookV1::Error.new(422, "invalid_transfer_destination", message, details)
    end
  end
end
