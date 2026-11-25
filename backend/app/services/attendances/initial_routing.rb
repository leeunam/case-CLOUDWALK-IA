module Attendances
  module InitialRouting
    # A marca já está bloqueada por quem aplica a primeira classificação.
    def self.choose(brand, classification)
      category, priority = classification.values_at(:category, :priority)
      rule = Operations::RoutingRule.where(brand: brand, active: true, category: [nil, category], priority: [nil, priority])
                                    .order(:position).first
      [rule&.queue || brand.support_queues.find_by!(active: true, is_default: true), rule]
    end

    def self.record!(record, rule)
      record.audit!("case.routing.applied", actor_type: "system", queue_id: record.queue_id,
                    rule_id: rule&.id, rule_version: rule&.version)
    end
  end
end
