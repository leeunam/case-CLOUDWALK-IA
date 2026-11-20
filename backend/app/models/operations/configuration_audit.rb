module Operations
  class ConfigurationAudit < ApplicationRecord
    belongs_to :brand
    RESOURCE_TYPES = %w[brand team queue routing_rule catalog capacity_profile].freeze

    def contract_data
      as_json(only: %i[id brand_id correlation_id resource_type resource_id version before after]).merge(
        actor: { type: "supervisor", id: actor_id }, occurred_at: created_at.iso8601(6)
      )
    end
  end
end
