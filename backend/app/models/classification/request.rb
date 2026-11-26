module Classification
  class Request < ApplicationRecord
    self.table_name = "classification_requests"

    belongs_to :support_case, class_name: "Attendances::SupportCase"
    has_many :attempts, class_name: "Classification::Attempt", foreign_key: :classification_request_id

    def job_queue
      provider == "setfit" ? "classification_setfit" : "default"
    end

    scope :open, -> { where(completed_at: nil) }
    scope :due, -> { open.where(available_at: ..Time.current) }
  end
end
