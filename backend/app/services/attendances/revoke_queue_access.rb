module Attendances
  module RevokeQueueAccess
    def self.allowed?(user, record)
      user.role == "analyst" && Visibility.new(user).queues.where(active: true).exists?(record.queue_id)
    end

    # Marca, responsável e atendimento já bloqueados pelo chamador.
    def self.call(record, owner)
      return if record.assignee_id != owner.attendant&.id || !SupportCase::PORTFOLIO_STATUSES.include?(record.status) ||
        allowed?(owner, record)

      previous = record.status
      previous_assignee = record.assignee_id
      waiting = previous == "waiting_customer"
      record.advance!(assignee: nil, status: waiting ? previous : "waiting_human",
                      assignment_generation: record.assignment_generation + 1,
                      human_queue_since: waiting ? nil : record.human_queue_since || Time.current,
                      blocking_reason: "queue_access_revoked")
      record.audit!("case.human.unassigned", actor_type: "system", from_status: previous,
                    reason: "queue_access_revoked", previous_assignee_id: previous_assignee, queue_id: record.queue_id)
      AnalystOperation.release_work!(owner, record.brand_id)
    end
  end
end
