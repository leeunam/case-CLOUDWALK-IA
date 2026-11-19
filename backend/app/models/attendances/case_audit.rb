module Attendances
  class CaseAudit < ApplicationRecord
    belongs_to :support_case, optional: true

    def contract_data
      { id: id, case_id: support_case_id, correlation_id: correlation_id, occurred_at: created_at.iso8601(6),
        actor: { type: actor_type, id: actor_id }, type: event_type, reason: reason,
        previous_status: from_status, new_status: to_status }
    end
  end
end
