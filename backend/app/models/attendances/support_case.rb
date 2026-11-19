module Attendances
  class SupportCase < ApplicationRecord
    STATUSES = %w[classification_pending classification_review ai_active waiting_human
                  human_active waiting_customer waiting_resumption resolved].freeze
    INTEGRATION_STATUSES = %w[idle pending_delivery awaiting_result failed].freeze
    PORTFOLIO_STATUSES = %w[human_active waiting_customer waiting_resumption].freeze
    HUMAN_STATUSES = (PORTFOLIO_STATUSES + ["waiting_human"]).freeze

    belongs_to :brand, class_name: "Operations::Brand"
    belongs_to :channel, class_name: "Operations::Channel"
    belongs_to :queue, class_name: "Operations::SupportQueue"
    belongs_to :channel_conversation
    belongs_to :assignee, class_name: "Operations::Attendant", optional: true
    has_many :messages, class_name: "Attendances::CaseMessage"
    has_many :turns, class_name: "AgentIntegration::AgentTurn"
    has_many :audits, class_name: "Attendances::CaseAudit"
    has_many :command_receipts, class_name: "Attendances::CaseCommandReceipt"

    def classification
      { category: category, category_source: category_source, priority: priority, priority_source: priority_source }
    end

    def advance!(**attributes)
      update!(**attributes, version: version + 1)
    end

    def append_message!(type:, author_id:, text:, source_event_id:)
      messages.create!(sequence: messages.maximum(:sequence).to_i + 1, author_type: type,
                       author_id: author_id, source_event_id: source_event_id, text: text)
    end

    def audit!(event_type, actor_type:, actor_id: nil, from_status: status, reason: nil, **details)
      audits.create!(correlation_id: correlation_id, event_type: event_type, actor_type: actor_type,
                     actor_id: actor_id, from_status: from_status, to_status: status,
                     reason: reason, details: details)
    end
  end
end
