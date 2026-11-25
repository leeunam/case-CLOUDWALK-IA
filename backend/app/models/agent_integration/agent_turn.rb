module AgentIntegration
  class AgentTurn < ApplicationRecord
    belongs_to :support_case, class_name: "Attendances::SupportCase"
    has_one :outbox, class_name: "AgentIntegration::AgentOutbox"

    scope :in_flight, -> { where(completed_at: nil) }
  end
end
