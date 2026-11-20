module Operations
  class Configuration
    def initialize(actor)
      @actor = actor
      @scope = ConfigurationScope.new(actor)
    end

    def update_brand(brand_id, data)
      transaction do
        brand = @scope.brands.find(brand_id)
        check_version!(brand.version, data)
        before = ConfigurationData.brand(brand)
        queue = brand.support_queues.find_by(id: data.fetch("default_queue_id"), active: true)
        invalid!("Selecione uma fila padrão ativa da marca.") unless queue
        links = brand.brand_teams.order(:id).to_a
        desired = ids(data, "team_ids")
        additions = desired - links.map(&:team_id)
        invalid!("Equipe indisponível para vínculo.") unless @scope.teams.where(id: additions).count == additions.size
        removed = links.reject { |link| desired.include?(link.team_id) }
        Team.where(id: additions + removed.map(&:team_id)).each do |team|
          @scope.authorize_all!((@scope.team_brand_ids(team) + [brand.id]).uniq)
        end
        affected = brand.support_queues.where(id: QueueTeam.where(brand_team_id: removed.map(&:id)).select(:support_queue_id))
        affected.each do |entry|
          if entry.active? && !entry.queue_teams.where.not(brand_team_id: removed.map(&:id)).exists?
            invalid!("A revogação deixaria uma fila ativa sem equipe.")
          end
        end
        # A alteração da marca também publica as filas cujos vínculos foram removidos.
        affected_queues = affected.order(:id).to_a
        affected_queues.each do |entry|
          old_queue = ConfigurationData.queue(entry)
          entry.queue_teams.where(brand_team_id: removed.map(&:id)).delete_all
          entry.update!(version: entry.version + 1)
          audit!([brand.id], "queue", old_queue, ConfigurationData.queue(entry))
        end
        brand.brand_teams.where(id: removed.map(&:id)).delete_all
        removed.each do |link|
          link.team.update!(orphaned_from_brand_id: brand.id) unless link.team.brand_teams.exists?
        end
        @scope.teams.where(id: additions).order(:id).each do |team|
          brand.brand_teams.create!(team: team)
          team.update!(orphaned_from_brand_id: nil) if team.orphaned_from_brand_id
        end
        unless queue.is_default?
          brand.support_queues.find(before.fetch(:default_queue_id)).update!(is_default: false)
          queue.update!(is_default: true)
        end
        brand.update!(name: name(data), version: brand.version + 1)
        if removed.any?
          users = TeamMembership.where(team_id: removed.map(&:team_id)).select(:user_id)
          reconcile!([brand.id], user_ids: users, queue_ids: affected_queues.map(&:id))
        end
        audit!([brand.id], "brand", before, ConfigurationData.brand(brand))
      end
    end

    def save_team(id, data)
      transaction do
        team = id ? @scope.teams.find(id) : Team.new(code: SecureRandom.uuid)
        existing = team.persisted?
        brand_ids = existing ? @scope.team_brand_ids(team) : ids(data, "brand_ids", default: @scope.brands.order(:id).ids)
        @scope.authorize_all!(brand_ids)
        check_version!(team.version, data) if existing
        before = ConfigurationData.team(team) if existing
        team.name = name(data)
        team.version += 1 if existing
        team.save!
        unless existing
          @scope.brands.where(id: brand_ids).order(:id).each do |brand|
            old_brand = ConfigurationData.brand(brand)
            team.brand_teams.create!(brand: brand)
            brand.update!(version: brand.version + 1)
            audit!([brand.id], "brand", old_brand, ConfigurationData.brand(brand))
          end
        end
        if data.key?("member_user_ids")
          desired = ids(data, "member_user_ids")
          current = team.team_memberships.pluck(:user_id)
          additions = desired - current
          invalid!("Analista indisponível para vínculo.") unless @scope.analysts(profile: false).where(id: additions).count == additions.size
          removed = current - desired
          team.team_memberships.where(user_id: removed).delete_all
          additions.each { |user_id| team.team_memberships.create!(user_id: user_id) }
          reconcile!(brand_ids, user_ids: removed) if removed.any?
        end
        Attendances::DistributeHumanWorkJob.schedule
        audit!(brand_ids, "team", before, ConfigurationData.team(team))
      end
    end

    def save_queue(brand_id, id, data)
      transaction do
        brand = @scope.brands.find(brand_id)
        queue = id ? brand.support_queues.find(id) : brand.support_queues.new(code: SecureRandom.uuid)
        existing = queue.persisted?
        check_version!(queue.version, data) if existing
        before = ConfigurationData.queue(queue) if existing
        desired = ids(data, "team_ids")
        links = brand.brand_teams.where(team_id: desired).order(:id).to_a
        invalid!("Vincule somente equipes autorizadas na marca.") if links.size != desired.size
        active = data.fetch("active")
        invalid!("Uma fila ativa precisa de pelo menos uma equipe.") if active && links.empty?
        validate_queue_deactivation!(queue) if existing && !active && queue.active?
        queue.assign_attributes(name: name(data), active: active)
        queue.version += 1 if existing
        queue.save!
        previous_links = queue.queue_teams.pluck(:brand_team_id)
        next_links = links.map(&:id)
        removed = previous_links - next_links
        queue.queue_teams.where(brand_team_id: removed).delete_all
        (next_links - previous_links).each { |link_id| queue.queue_teams.create!(brand: brand, brand_team_id: link_id) }
        if removed.any? || !active
          revoked_links = active ? removed : previous_links
          teams = BrandTeam.where(id: revoked_links).select(:team_id)
          users = TeamMembership.where(team_id: teams).select(:user_id)
          reconcile!([brand.id], user_ids: users, queue_ids: [queue.id])
        else
          Attendances::DistributeHumanWorkJob.schedule(brand.id)
        end
        audit!([brand.id], "queue", before, ConfigurationData.queue(queue))
      end
    end

    def save_rule(brand_id, id, data)
      transaction do
        brand = @scope.brands.find(brand_id)
        rules = RoutingRule.where(brand: brand)
        rule = id ? rules.find(id) : rules.new
        existing = rule.persisted?
        check_version!(rule.version, data) if existing
        before = rule.contract_data if existing
        active, position, category, priority = data.values_at("active", "position", "category", "priority")
        invalid!("Informe categoria ou prioridade para a regra.") unless category || priority
        validate_integer!(position)
        queue = brand.support_queues.find_by(id: data.fetch("queue_id"))
        invalid!("Selecione uma fila da marca, ativa para publicação.") unless queue && (!active || queue.active?)
        if category && active && !Classification::Catalog.category_active?(brand, category)
          invalid!("Selecione uma categoria ativa da marca.")
        end
        if active && rules.where.not(id: rule.id).exists?(position: position, active: true)
          invalid!("Já existe uma regra ativa nessa posição.")
        end
        rule.assign_attributes(queue: queue, position: position, category: category, priority: priority, active: active)
        rule.version += 1 if existing
        rule.save!
        audit!([brand.id], "routing_rule", before, rule.contract_data)
      end
    end

    def save_catalog(brand_id, data)
      transaction do
        brand = @scope.brands.find(brand_id)
        check_version!(brand.catalog_version, data)
        before = ConfigurationData.catalog(brand)
        entries = data.fetch("categories")
        codes = entries.map { |entry| entry.fetch("key") }
        invalid!("O catálogo tem chaves de categoria duplicadas.") unless codes.uniq.size == codes.size
        unless codes.all? { |code| Classification::Catalog.category_code?(code) }
          invalid!("O catálogo contém uma chave não permitida pelo Jev.")
        end
        active = entries.filter_map { |entry| entry.fetch("key") if entry.fetch("active") }
        invalid!("O Jev aceita até 254 categorias ativas.") if active.size > Classification::Jev::Classifier::MAX_CATALOG_SIZE
        existing = brand.categories.index_by(&:code)
        removed = existing.values.select(&:active?).map(&:code) - active
        validate_catalog_dependencies!(brand, removed)
        entries.each do |entry|
          code = entry.fetch("key")
          category = existing[code] || brand.categories.new(code: code)
          category.update!(name: name(entry), active: entry.fetch("active"))
        end
        # Chaves omitidas ficam inativas para preservar a leitura do histórico.
        brand.categories.where(code: removed - codes).update_all(active: false, updated_at: Time.current)
        brand.update!(catalog_version: brand.catalog_version + 1)
        audit!([brand.id], "catalog", before, ConfigurationData.catalog(brand), resource_id: brand.id)
      end
    end

    def save_profile(user_id, data, create:)
      transaction do
        user = @scope.analysts.find(user_id)
        brand_ids = @scope.analyst_brand_ids(user)
        @scope.authorize_all!(brand_ids)
        user.lock!
        previous = user.capacity_profiles.find_by(active: true)
        if create
          if previous
            raise WebhookV1::Error.new(409, "profile_exists", "Já existe um perfil ativo para este analista.")
          end
        else
          raise ActiveRecord::RecordNotFound unless previous

          check_version!(previous.version, data)
        end
        limit, alternatives = data.values_at("portfolio_limit", "alternatives")
        validate_profile!(limit, alternatives, brand_ids)
        before = ConfigurationData.profile(previous) if previous
        version = user.capacity_profiles.maximum(:version).to_i + 1
        previous&.update!(active: false)
        profile = user.capacity_profiles.create!(version: version, portfolio_limit: limit, alternatives: alternatives)
        after = ConfigurationData.profile(profile)
        Brand.where(id: brand_ids).each do |brand|
          codes = brand.categories.pluck(:code)
          audit!([brand.id], "capacity_profile", scoped_profile_snapshot(before, codes),
                 scoped_profile_snapshot(after, codes), resource_id: user.id)
          Attendances::DistributeHumanWorkJob.schedule(brand.id)
        end
        after
      end
    end

    private

    def transaction(&block)
      ApplicationRecord.transaction do
        # Vínculos e perfis atravessam marcas. O bloqueio global das marcas já é
        # usado pela operação dos analistas e mantém a mesma ordem nas edições.
        Attendances::HumanLocks.all_brands!
        @correlation_id = SecureRandom.uuid
        block.call
      end
    rescue ActiveRecord::RecordInvalid => error
      invalid!(error.record.errors.full_messages.join(", "))
    end

    def audit!(brand_ids, type, before, after, resource_id: after[:id])
      brand_ids.each do |brand_id|
        ConfigurationAudit.create!(brand_id: brand_id, actor_id: @actor.id, correlation_id: @correlation_id,
                                   resource_type: type, resource_id: resource_id,
                                   version: after.fetch(:version), before: before, after: after)
      end
      after
    end

    def check_version!(version, data)
      return if version == data.fetch("expected_version")

      raise WebhookV1::Error.new(409, "version_conflict", "A configuração foi atualizada.", { current_version: version })
    end

    def invalid!(message)
      raise WebhookV1::Error.new(422, "invalid_configuration", message)
    end

    def ids(data, key, default: [])
      data.fetch(key, default).map(&:downcase).uniq
    end

    def name(data)
      data.fetch("name").strip.presence || invalid!("Informe um nome.")
    end

    def validate_integer!(value)
      invalid!("Valor inteiro acima do limite suportado.") if value > 2**31 - 1
    end

    def validate_queue_deactivation!(queue)
      invalid!("Escolha outra fila padrão antes de desativar esta.") if queue.is_default?
      if RoutingRule.exists?(queue_id: queue.id, active: true) ||
          Attendances::SupportCase.where(queue: queue).where.not(status: "resolved").exists?
        invalid!("Retire as regras ativas e transfira os atendimentos em andamento antes de desativar a fila.")
      end
    end

    def validate_catalog_dependencies!(brand, removed)
      return if removed.empty?

      if RoutingRule.where(brand: brand, active: true, category: removed).exists?
        invalid!("Há regras ativas que usam categorias removidas.")
      end
      scopes = BrandTeam.where(brand: brand).select(:team_id)
      analysts = User.where(id: TeamMembership.where(team_id: scopes).select(:user_id))
      CapacityProfile.where(user: analysts, active: true).includes(:user).find_each do |profile|
        used = profile.alternatives.flatten.pluck("category") & removed
        next if used.empty?

        other_brands = @scope.analyst_brand_ids(profile.user) - [brand.id]
        still_available = Category.where(brand_id: other_brands, active: true, code: used).distinct.pluck(:code)
        invalid!("Há perfis ativos que dependem das categorias removidas.") if (used - still_available).any?
      end
    end

    def validate_profile!(limit, alternatives, brand_ids)
      validate_integer!(limit)
      codes = Category.where(brand_id: brand_ids, active: true).distinct.pluck(:code)
      normalized = alternatives.map do |alternative|
        pairs = alternative.map do |pair|
          invalid!("O perfil contém uma categoria fora do catálogo ativo do analista.") unless codes.include?(pair.fetch("category"))

          pair.values_at("priority", "category")
        end
        invalid!("Uma alternativa contém pares repetidos.") if pairs.uniq.size != pairs.size
        invalid!("O teto da carteira precisa comportar cada alternativa.") if alternative.sum { |pair| pair.fetch("limit") } > limit
        alternative.map { |pair| pair.values_at("priority", "category", "limit") }.sort
      end
      invalid!("O perfil contém alternativas repetidas.") if normalized.uniq.size != normalized.size
    end

    def scoped_profile_snapshot(snapshot, codes)
      return unless snapshot

      snapshot.merge(alternatives: snapshot.fetch(:alternatives).filter_map do |alternative|
        alternative.select { |pair| codes.include?(pair.fetch("category")) }.presence
      end)
    end

    def reconcile!(brand_ids, user_ids:, queue_ids: nil)
      portfolio = Attendances::SupportCase.where(brand_id: brand_ids, status: Attendances::SupportCase::PORTFOLIO_STATUSES)
                                            .where.not(assignee_id: nil)
      portfolio = if queue_ids
        portfolio.where(queue_id: queue_ids)
      else
        portfolio.where(assignee_id: Attendant.where(user_id: user_ids).select(:id))
      end
      owner_ids = Attendant.where(id: portfolio.select(:assignee_id)).select(:user_id)
      owners = Attendances::HumanLocks.users!(User.where(id: owner_ids).or(User.where(id: user_ids)).select(:id))
      by_attendant = owners.index_by { |owner| owner.attendant&.id }
      portfolio.order(:id).lock.each do |record|
        owner = by_attendant[record.assignee_id]
        Attendances::RevokeQueueAccess.call(record, owner) if owner
      end
      owners.each { |owner| Attendances::AnalystOperation.reconcile_access!(owner) if owner.role == "analyst" }
      brand_ids.each { |id| Attendances::DistributeHumanWorkJob.schedule(id) }
    end
  end
end
