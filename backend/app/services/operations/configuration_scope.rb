module Operations
  class ConfigurationScope
    def initialize(actor)
      @actor = actor
    end

    def brands
      Brand.where(id: SupervisorBrand.where(user: @actor).select(:brand_id))
    end

    def teams
      linked = Team.where(id: BrandTeam.where(brand_id: brands.select(:id)).select(:team_id))
      orphaned = Team.where(orphaned_from_brand_id: brands.select(:id)).where.not(id: BrandTeam.select(:team_id))
      linked.or(orphaned)
    end

    def team_brand_ids(team)
      team.brand_teams.order(:brand_id).pluck(:brand_id).presence || [team.orphaned_from_brand_id].compact
    end

    def analyst_brand_ids(analyst)
      BrandTeam.where(team_id: analyst.team_memberships.select(:team_id)).distinct.order(:brand_id).pluck(:brand_id)
    end

    def authorize_all!(ids)
      return if ids.present? && brands.where(id: ids).count == ids.size

      raise WebhookV1::Error.new(403, "forbidden", "A alteração exige autorização nas marcas afetadas.")
    end

    def authorize_profile!(profile)
      codes = profile.alternatives.flatten.pluck("category").uniq
      return if (codes - visible_profile_category_codes(codes: codes)).empty?

      raise WebhookV1::Error.new(403, "forbidden", "Perfil indisponível para esta supervisão.")
    end

    def visible_profile_category_codes(brand_ids: brands.select(:id), codes: nil)
      catalog = codes ? Category.where(code: codes) : Category.all
      supervised = catalog.where(brand_id: brand_ids)
      outside = catalog.where.not(brand_id: brand_ids)
      supervised.where(active: true).or(supervised.where.not(code: outside.select(:code))).distinct.pluck(:code)
    end

    def analysts(brand: nil, profile: true)
      authorized_links = BrandTeam.where(brand_id: brand ? brand.id : brands.select(:id))
      members = TeamMembership.where(team_id: authorized_links.select(:team_id))
      analysts = User.where(role: "analyst", id: Attendant.where(kind: "human").select(:user_id))
                     .where(id: members.select(:user_id))
      unless profile
        # Quem supervisiona toda a operação também pode recolocar contas sem equipe.
        return User.where(role: "analyst", id: Attendant.where(kind: "human").select(:user_id)) unless
          Brand.where.not(id: brands.select(:id)).exists?
        return analysts
      end

      outside = BrandTeam.where.not(brand_id: brands.select(:id))
      analysts.where.not(id: TeamMembership.where(team_id: outside.select(:team_id)).select(:user_id))
    end
  end
end
