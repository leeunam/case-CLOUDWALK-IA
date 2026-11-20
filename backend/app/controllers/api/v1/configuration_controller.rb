module Api
  module V1
    class ConfigurationController < BrowserController
      before_action :require_user!
      before_action :require_supervisor!

      rescue_from ActiveRecord::RecordNotFound do
        render json: { error: { code: "not_found", message: "Configuração indisponível." } }, status: 404
      end

      def brands
        list(scope.brands, "brands") { |row| Operations::ConfigurationData.brand(row) }
      end

      def update_brand
        render json: configuration.update_brand(path_id(:brand_id), payload("BrandUpdate"))
      end

      def teams
        actor_brand_ids = scope.brands.ids
        list(scope.teams, "teams") do |row|
          Operations::ConfigurationData.team(row).merge(editable: (scope.team_brand_ids(row) - actor_brand_ids).empty?)
        end
      end

      def create_team
        render json: configuration.save_team(nil, payload("TeamInput")), status: :created
      end

      def update_team
        render json: configuration.save_team(path_id(:id), payload("TeamUpdate"))
      end

      def queues
        list(brand.support_queues, "queues", brand.id) { |row| Operations::ConfigurationData.queue(row) }
      end

      def create_queue
        render json: configuration.save_queue(path_id(:brand_id), nil, payload("QueueInput")), status: :created
      end

      def update_queue
        render json: configuration.save_queue(path_id(:brand_id), path_id(:id), payload("QueueUpdate"))
      end

      def routing_rules
        list(Operations::RoutingRule.where(brand: brand), "routing_rules", brand.id,
             order: %i[position id], direction: :asc, &:contract_data)
      end

      def create_routing_rule
        render json: configuration.save_rule(path_id(:brand_id), nil, payload("RoutingRuleInput")), status: :created
      end

      def update_routing_rule
        render json: configuration.save_rule(path_id(:brand_id), path_id(:id), payload("RoutingRuleUpdate"))
      end

      def configuration_audit
        filters = request.query_parameters
        type, id = filters.values_at("resource_type", "resource_id")
        invalid_query!("resource_type") if filters.key?("resource_type") && !Operations::ConfigurationAudit::RESOURCE_TYPES.include?(type)
        invalid_query!("resource_id") if filters.key?("resource_id") && (!type || !uuid?(id))
        events = Operations::ConfigurationAudit.where(brand: brand)
        events = events.where(resource_type: type) if type
        events = events.where(resource_id: id) if id
        list(events, "configuration_audit", brand.id, type, id, order: %i[created_at id], &:contract_data)
      end

      def catalog
        render json: Operations::ConfigurationData.catalog(brand)
      end

      def update_catalog
        render json: configuration.save_catalog(path_id(:brand_id), payload("CatalogUpdate"))
      end

      def analysts
        raw = request.query_parameters["brand_id"]
        invalid_query!("brand_id") if request.query_parameters.key?("brand_id") && !uuid?(raw)
        selected = scope.brands.find(raw) if raw
        list_analysts(scope.analysts(brand: selected), "analysts", raw, include_brands: true)
      end

      def team_members
        list_analysts(scope.analysts(profile: false), "team_members")
      end

      def queue_analysts
        queue = brand.support_queues.find_by!(id: path_id(:id), active: true)
        members = Operations::TeamMembership.where(team_id: queue.brand_teams.select(:team_id))
        list_analysts(scope.analysts(brand: brand, profile: false).where(id: members.select(:user_id)), "queue_analysts", queue.id)
      end

      def capacity_profile
        analyst = scope.analysts.find(path_id(:analyst_id))
        render json: Operations::ConfigurationData.profile(analyst.capacity_profiles.find_by!(active: true))
      end

      def create_capacity_profile
        render json: configuration.save_profile(path_id(:analyst_id), payload("CapacityProfileInput"), create: true),
               status: :created
      end

      def update_capacity_profile
        render json: configuration.save_profile(path_id(:analyst_id), payload("CapacityProfileUpdate"), create: false)
      end

      private

      def list_analysts(relation, *scope_parts, include_brands: false)
        list(relation.includes(:attendant), *scope_parts) do |row|
          data = { user_id: row.id, attendant_id: row.attendant.id, name: row.name }
          data[:brand_ids] = scope.analyst_brand_ids(row) if include_brands
          data
        end
      end

      def require_supervisor!
        return if current_user.role == "supervisor"

        raise WebhookV1::Error.new(403, "forbidden", "A configuração exige acesso de supervisão.")
      end

      def path_id(key)
        id = request.path_parameters.fetch(key)
        raise ActiveRecord::RecordNotFound unless uuid?(id)

        id.downcase
      end

      def uuid?(value)
        value.is_a?(String) && WebhookV1::Contract::UUID.match?(value)
      end

      def brand
        @brand ||= scope.brands.find(path_id(:brand_id))
      end

      def scope
        @scope ||= Operations::ConfigurationScope.new(current_user)
      end

      def configuration
        @configuration ||= Operations::Configuration.new(current_user)
      end

      def payload(definition)
        WebhookV1::Contract.parse!(request.raw_post, definition)
      end

      def list(relation, *parts, order: [:id], direction: :desc)
        page = paginated(relation, order: order, direction: direction, scope: ["configuration", current_user.id, *parts])
        render json: page.merge(items: page.fetch(:items).map { |row| yield row })
      end
    end
  end
end
