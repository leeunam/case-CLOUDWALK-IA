module Operations
  module ConfigurationData
    PRIORITY_NAMES = { "basic" => "Básico", "intermediate" => "Intermediário",
                       "advanced" => "Avançado", "urgent" => "Urgente" }.freeze

    def self.brand(brand)
      { id: brand.id, name: brand.name, version: brand.version,
        default_queue_id: brand.support_queues.find_by!(active: true, is_default: true).id,
        team_ids: brand.brand_teams.order(:team_id).pluck(:team_id) }
    end

    def self.queue(queue)
      { id: queue.id, brand_id: queue.brand_id, name: queue.name, active: queue.active, version: queue.version,
        team_ids: queue.brand_teams.order(:team_id).pluck(:team_id) }
    end

    def self.team(team)
      { id: team.id, name: team.name, version: team.version,
        member_user_ids: team.team_memberships.order(:user_id).pluck(:user_id) }
    end

    def self.category(category)
      { key: category.code, name: category.name, active: category.active }
    end

    def self.catalog(brand)
      priorities = Classification::Catalog::PRIORITIES.map do |key, description|
        { key: key, name: PRIORITY_NAMES.fetch(key), description: description }
      end
      { brand_id: brand.id, version: brand.catalog_version, priorities: priorities,
        categories: brand.categories.order(:code).map { |record| category(record) } }
    end

    def self.profile(profile)
      { id: profile.id, analyst_id: profile.user_id, version: profile.version,
        portfolio_limit: profile.portfolio_limit, alternatives: profile.alternatives }
    end

    def self.scoped_profile_snapshot(snapshot, codes)
      return unless snapshot

      snapshot = snapshot.with_indifferent_access
      snapshot.merge(alternatives: snapshot.fetch(:alternatives).filter_map do |alternative|
        alternative.select { |pair| codes.include?(pair.fetch("category")) }.presence
      end)
    end
  end
end
