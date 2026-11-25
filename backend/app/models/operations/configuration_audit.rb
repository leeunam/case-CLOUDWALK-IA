module Operations
  class ConfigurationAudit < ApplicationRecord
    belongs_to :brand
    RESOURCE_TYPES = %w[brand team queue routing_rule catalog capacity_profile].freeze
    PROFILE_SCOPE_KEY = "_profile_scope_version".freeze
    PROFILE_SCOPE_VERSION = 1

    def self.with_verified_profile_scope(snapshot)
      snapshot.merge(PROFILE_SCOPE_KEY => PROFILE_SCOPE_VERSION)
    end

    def contract_data
      data = as_json(only: %i[id brand_id correlation_id resource_type resource_id version before after]).merge(
        actor: { type: "supervisor", id: actor_id }, occurred_at: created_at.iso8601(6)
      )
      if resource_type == "capacity_profile" && data.fetch("after").delete(PROFILE_SCOPE_KEY) != PROFILE_SCOPE_VERSION
        data.fetch("before")&.delete("alternatives")
        data.fetch("after").delete("alternatives")
      end
      data
    end
  end
end
