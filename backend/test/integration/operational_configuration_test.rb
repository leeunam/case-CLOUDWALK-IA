require "test_helper"

class OperationalConfigurationTest < ActionDispatch::IntegrationTest
  setup do
    @old_env = %w[CLOUDWALK_DEMO_PASSWORDS CLOUDWALK_JEV_MODE].to_h { |key| [key, ENV[key]] }
    @forgery = Api::V1::BrowserController.allow_forgery_protection
    Api::V1::BrowserController.allow_forgery_protection = true
    ENV["CLOUDWALK_DEMO_PASSWORDS"] = {
      "supervisor@example.test" => "test", "limited@example.test" => "test", "bia@example.test" => "test"
    }.to_json
    ENV["CLOUDWALK_JEV_MODE"] = "fixture"
    Rails.application.load_seed
    @brand = Operations::Brand.find_by!(code: "aurora")
    @other = Operations::Brand.find_by!(code: "horizonte")
    @base = "/api/v1/brands/#{@brand.id}"
    @channel = @brand.channels.find_by!(kind: "chat")
    @default = @brand.support_queues.find_by!(is_default: true)
    @shared = Operations::Team.find_by!(code: "shared")
    @specialists = Operations::Team.find_by!(code: "aurora_specialists")
    @team_ids = [@shared.id, @specialists.id]
    @bia = Operations::User.find_by!(email: "bia@example.test")
    @supervisor = Operations::User.find_by!(email: "supervisor@example.test")
    @limited = Operations::User.create!(email: "limited@example.test", role: "supervisor", name: "Supervisão Aurora")
    Operations::SupervisorBrand.create!(brand: @brand, user: @limited)
    @identity = BrowserAccess::Session.create!(audience: "simulator", expires_at: 1.hour.from_now)
  end

  teardown do
    @old_env.each { |key, value| ENV[key] = value }
    Api::V1::BrowserController.allow_forgery_protection = @forgery
  end

  test "supervisão publica duas equipes e regra ordenada sem mudar o caso anterior" do
    old_case = receive
    token = login(@supervisor.email)
    queue = create_queue(token)
    second_queue = create_queue(token, name: "Triagem prioritária")

    second_rule = create_rule(token, queue, position: 20)
    first_rule = create_rule(token, second_queue, position: 10, priority: "basic")
    routed = receive
    assert_equal second_queue.fetch("id"), routed.queue_id
    assert_equal @default.id, old_case.reload.queue_id
    assert_equal 1, routed.turns.count

    post "/api/v1/cases/#{old_case.id}/classification", as: :json,
      headers: headers(token).merge("Idempotency-Key" => "reclassify"),
      params: { expected_version: old_case.version, category: "pix", priority: "urgent", reason: "Impacto revisado" }
    assert_response 200
    assert_equal ["urgent", @default.id, 1], [old_case.reload.priority, old_case.queue_id, old_case.turns.count]

    get "/api/v1/cases/#{routed.id}/audit"
    assert_response 200
    entry = response.parsed_body.fetch("items").find { |event| event.fetch("type") == "case.routing.applied" }
    assert_equal [first_rule.fetch("id"), 1], entry.fetch("routing").values_at("rule_id", "rule_version")
    assert WebhookV1::Contract.valid?("AuditList", response.parsed_body)

    put "#{@base}/routing-rules/#{first_rule.fetch('id')}", as: :json, headers: headers(token),
      params: first_rule.except("id", "brand_id", "version").merge("expected_version" => 1, "active" => false)
    assert_response 200
    assert_equal second_queue.fetch("id"), routed.reload.queue_id
    assert_equal queue.fetch("id"), receive.queue_id

    get "#{@base}/routing-rules", params: { limit: 1 }
    assert_response 200
    assert_equal [first_rule.fetch("id")], response.parsed_body.fetch("items").pluck("id")
    cursor = response.parsed_body.fetch("next_cursor")
    get "#{@base}/routing-rules", params: { limit: 1, cursor: cursor }
    assert_response 200
    assert_equal [second_rule.fetch("id")], response.parsed_body.fetch("items").pluck("id")

    audit = "#{@base}/configuration-audit"
    filters = { resource_type: "routing_rule", resource_id: first_rule.fetch("id"), limit: 1 }
    get audit, params: filters
    assert_response 200
    assert WebhookV1::Contract.valid?("ConfigurationAuditList", response.parsed_body)
    edit = response.parsed_body.fetch("items").sole
    assert_equal [2, @supervisor.id], [edit.fetch("version"), edit.dig("actor", "id")]
    assert_equal [true, false], [edit.dig("before", "active"), edit.dig("after", "active")]
    cursor = response.parsed_body.fetch("next_cursor")
    get audit, params: filters.merge(cursor: cursor)
    assert_response 200
    assert_nil response.parsed_body.fetch("items").sole.fetch("before")
    get audit, params: filters.merge(cursor: cursor, resource_id: second_rule.fetch("id"))
    assert_response 422
  end

  test "recusa alterações inválidas sem auditoria ou mudança parcial" do
    token = login(@supervisor.email)
    queue = create_queue(token, team_ids: [@specialists.id])
    create_rule(token, queue)
    count = Operations::ConfigurationAudit.count
    foreign_team = Operations::Team.find_by!(code: "horizonte_specialists")
    post "#{@base}/queues", params: { name: "Inválida", active: true, team_ids: [foreign_team.id] },
      as: :json, headers: headers(token)
    assert_response 422
    [[@default.id, @team_ids], [queue.fetch("id"), [@specialists.id]]].each do |id, teams|
      put "#{@base}/queues/#{id}", params: { name: "Nova", active: false, team_ids: teams, expected_version: 1 },
        as: :json, headers: headers(token)
      assert_response 422
    end
    put @base, params: { name: "Alteração parcial", default_queue_id: @default.id, team_ids: [@shared.id], expected_version: 1 },
      as: :json, headers: headers(token)
    assert_response 422
    assert_equal 1, @brand.reload.version
    assert_equal count, Operations::ConfigurationAudit.count
    assert @brand.brand_teams.exists?(team: @specialists)

    limited = login(@limited.email)
    put "/api/v1/teams/#{@shared.id}", params: { name: "Sem autorização", expected_version: 1 },
      as: :json, headers: headers(limited)
    assert_response 403
    get "/api/v1/brands/#{@other.id}/configuration-audit"
    assert_response 404
    assert_equal count, Operations::ConfigurationAudit.count
  end

  test "criação de equipe publica vínculo e edição exige versão atual" do
    token = login(@limited.email)
    post "/api/v1/teams", params: { name: "Suporte local", brand_ids: [@brand.id], member_user_ids: [@bia.id] },
      as: :json, headers: headers(token)
    assert_response 201
    data = response.parsed_body
    assert WebhookV1::Contract.valid?("Team", data)
    team = Operations::Team.find(data.fetch("id"))
    assert_equal [@brand.id], team.brand_teams.pluck(:brand_id)
    assert_equal [@bia.id], team.team_memberships.pluck(:user_id)
    assert_equal 2, @brand.reload.version

    path = "/api/v1/teams/#{team.id}"
    put path, params: { name: "Nova equipe", expected_version: 1 }, as: :json, headers: headers(token)
    assert_response 200
    put path, params: { name: "Perdida", expected_version: 1, member_user_ids: [] }, as: :json, headers: headers(token)
    assert_response 409
    assert_equal ["Nova equipe", 2], team.reload.attributes.values_at("name", "version")
    assert_equal [@bia.id], team.team_memberships.pluck(:user_id)
  end

  test "catálogo e perfis alteram elegibilidade sem soltar ativos e recusam dependências" do
    token = login(@supervisor.email)
    get "#{@base}/catalog"
    assert_response 200
    catalog = response.parsed_body
    categories = catalog.fetch("categories") + [{ "key" => "conta_digital", "name" => "Conta digital", "active" => true }]
    put "#{@base}/catalog", params: { expected_version: 1, categories: categories }, as: :json, headers: headers(token)
    assert_response 200
    assert WebhookV1::Contract.valid?("Catalog", response.parsed_body)

    old = receive
    old.advance!(assignee: @bia.attendant, status: "human_active")
    incoming = receive(category: "conta_digital")
    assert_equal "ai_active", incoming.status
    assert_equal "active_capacity", Attendances::HumanEligibility.new(@bia).block_reason(incoming)

    path = "/api/v1/analysts/#{@bia.id}/capacity-profile"
    pair = { priority: "basic", category: "conta_digital", limit: 1 }
    too_large = [[pair.merge(limit: 2)]]
    duplicates = [[pair, pair.merge(limit: 2)]]
    [too_large, duplicates, [[pair.merge(category: "inexistente")]]].each do |alternatives|
      put path, params: { expected_version: 1, portfolio_limit: 1, alternatives: alternatives },
        as: :json, headers: headers(token)
      assert_response 422
    end
    profile = { expected_version: 1, portfolio_limit: 2, alternatives: [[pair]] }
    put path, params: profile, as: :json, headers: headers(token)
    assert_response 200
    assert_equal 2, response.parsed_body.fetch("version")
    put path, params: profile, as: :json, headers: headers(token)
    assert_response 409

    assert_equal ["human_active", @bia.attendant.id], [old.reload.status, old.assignee_id]
    assert_equal "active_capacity", Attendances::HumanEligibility.new(@bia).block_reason(incoming)
    old.advance!(status: "waiting_customer")
    assert_nil Attendances::HumanEligibility.new(@bia).block_reason(incoming)

    deactivation = categories.map { |entry| entry.fetch("key") == "conta_digital" ? entry.merge("active" => false) : entry }
    put "#{@base}/catalog", params: { expected_version: 2, categories: deactivation },
      as: :json, headers: headers(token)
    assert_response 422
    assert_equal 2, @brand.reload.catalog_version
  end

  test "revogar o último vínculo fora do escopo protege o perfil inteiro" do
    alex = Operations::User.find_by!(email: "alex@example.test")
    foreign_category = @other.categories.create!(code: "conta_horizonte", name: "Conta Horizonte")
    token = login(@supervisor.email)
    path = "/api/v1/analysts/#{alex.id}/capacity-profile"
    local_pair = { priority: "basic", category: "pix", limit: 1 }
    alternatives = [[local_pair], [local_pair.merge(category: foreign_category.code, limit: 2)]]
    put path, params: { expected_version: 1, portfolio_limit: 2, alternatives: alternatives },
      as: :json, headers: headers(token)
    assert_response 200
    published = response.parsed_body

    retained_members = @shared.team_memberships.where.not(user_id: alex.id).pluck(:user_id)
    put "/api/v1/teams/#{@shared.id}", params: {
      name: @shared.name, expected_version: @shared.version, member_user_ids: retained_members
    }, as: :json, headers: headers(token)
    assert_response 200

    limited = login(@limited.email)
    get "/api/v1/analysts"
    assert_response 200
    entry = response.parsed_body.fetch("items").find { |item| item.fetch("user_id") == alex.id }
    assert_equal [@brand.id], entry.fetch("brand_ids")
    get path
    assert_response 403
    assert_equal({ "error" => { "code" => "forbidden", "message" => "Perfil indisponível para esta supervisão." } },
      response.parsed_body)

    @brand.categories.create!(code: foreign_category.code, name: "Chave histórica Aurora", active: false)
    get path
    assert_response 403
    assert_not_includes response.body, foreign_category.code

    # Simula a projeção antiga feita quando o catálogo histórico compartilhava a chave.
    legacy = Operations::ConfigurationAudit.find_by!(brand: @brand, resource_type: "capacity_profile",
                                                    resource_id: alex.id, version: 2)
    legacy.update_column(:after, published)

    audit_count = Operations::ConfigurationAudit.count
    assert_no_difference -> { alex.capacity_profiles.count } do
      put path, params: { expected_version: 2, portfolio_limit: 1, alternatives: [[local_pair]] },
        as: :json, headers: headers(limited)
      assert_response 403
      post path, params: { portfolio_limit: 1, alternatives: [[local_pair]] }, as: :json, headers: headers(limited)
      assert_response 403
    end
    assert_equal audit_count, Operations::ConfigurationAudit.count

    local_path = "/api/v1/analysts/#{@bia.id}/capacity-profile"
    get local_path
    assert_response 200
    put local_path, params: { expected_version: 1, portfolio_limit: 1, alternatives: [[local_pair]] },
      as: :json, headers: headers(limited)
    assert_response 200
    assert_equal 2, response.parsed_body.fetch("version")

    token = login(@supervisor.email)
    get path
    assert_response 200
    assert_equal published, response.parsed_body
    put path, params: { expected_version: 2, portfolio_limit: 1, alternatives: [[local_pair]] },
      as: :json, headers: headers(token)
    assert_response 200
    assert_equal 3, response.parsed_body.fetch("version")

    repair = Operations::ConfigurationAudit.find_by!(brand: @brand, resource_type: "capacity_profile",
                                                    resource_id: alex.id, version: 3)
    assert_equal [[local_pair.stringify_keys]], repair.before.fetch("alternatives")

    login(@limited.email)
    get "#{@base}/configuration-audit", params: { resource_type: "capacity_profile", resource_id: alex.id }
    assert_response 200
    assert_not_includes response.body, foreign_category.code
    assert_equal [3, 2], response.parsed_body.fetch("items").pluck("version")
    assert_equal published, legacy.reload.after
  end

  test "revogar equipe de uma fila retira leitura e preserva espera sem responsável" do
    active = receive
    active.advance!(status: "human_active", assignee: @bia.attendant)
    waiting = receive
    waiting.advance!(status: "waiting_customer", assignee: @bia.attendant)
    token = login(@supervisor.email)
    put "#{@base}/queues/#{@default.id}", params: { name: @default.name, active: true, team_ids: [@shared.id], expected_version: 1 },
      as: :json, headers: headers(token)
    assert_response 200

    assert_equal ["waiting_human", nil], [active.reload.status, active.assignee_id]
    assert_equal ["waiting_customer", nil], [waiting.reload.status, waiting.assignee_id]
    assert_equal "queue_access_revoked", active.audits.find_by!(event_type: "case.human.unassigned").reason
    analyst_token = login(@bia.email)
    get "/api/v1/cases/#{active.id}"
    assert_response 404
    command(active, analyst_token, { type: "resolve" }, "revoked")
    assert_response 404
  end

  test "Jev e revisão usam regra e recuperação usa os comandos canônicos" do
    token = login(@supervisor.email)
    queue = create_queue(token)
    create_rule(token, queue)
    pending = receive(category: nil)
    assert_equal @default.id, pending.queue_id
    Classification::CompleteRequestJob.perform_now(Classification::Request.find_by!(support_case: pending).id)
    assert_equal queue.fetch("id"), pending.reload.queue_id
    assert_equal 1, pending.turns.count

    review = receive(category: "fora")
    payload = { expected_version: review.version, category: "pix", priority: "basic", reason: "Triagem revisada" }
    2.times do
      post "/api/v1/cases/#{review.id}/classification", params: payload, as: :json,
        headers: headers(token).merge("Idempotency-Key" => "review")
      assert_response 200
    end
    assert_equal queue.fetch("id"), review.reload.queue_id
    assert_equal 1, review.turns.count

    review.advance!(integration_status: "failed", blocking_reason: "bridge_http_503")
    get "/api/v1/cases", params: { integration_status: "failed" }
    assert_response 200
    assert_equal [review.id], response.parsed_body.fetch("items").pluck("id")
    command(review, token, { type: "retry_agent", reason: "Ponte disponível" }, "retry")
    assert_response 200
    assert_equal "pending_delivery", review.reload.integration_status
    assert_equal 1, review.turns.count
    review.advance!(integration_status: "failed")
    command(review, token, { type: "force_handoff", reason: "Falha persistente", summary: "Cliente aguarda confirmação." }, "handoff")
    assert_response 200
    assert_equal "waiting_human", review.reload.status
    command(review, token, { type: "transfer", destination_queue_id: @default.id, reason: "Direcionar à fila geral" }, "transfer")
    assert_response 200
    assert_equal @default.id, review.reload.queue_id
  end

  private

  def headers(token)
    { "X-CSRF-Token" => token }
  end

  def login(email)
    get "/api/v1/session"
    post "/api/v1/session", params: { email: email, password: "test" }, as: :json,
      headers: headers(response.parsed_body.fetch("csrf_token"))
    assert_response 200
    response.parsed_body.fetch("csrf_token")
  end

  def create_queue(token, name: "Triagem Pix", team_ids: @team_ids)
    post "#{@base}/queues", params: { name: name, active: true, team_ids: team_ids }, headers: headers(token), as: :json
    assert_response 201
    data = response.parsed_body
    assert WebhookV1::Contract.valid?("Queue", data)
    assert_equal team_ids.sort, data.fetch("team_ids")
    data
  end

  def create_rule(token, queue, position: 10, priority: nil)
    post "#{@base}/routing-rules", params: {
      active: true, position: position, queue_id: queue.fetch("id"), category: "pix", priority: priority
    }, headers: headers(token), as: :json
    assert_response 201
    response.parsed_body
  end

  def receive(category: "pix")
    payload = { "text" => "Qual é o prazo de confirmação de um Pix?", "priority" => "basic" }
    payload["category"] = category if category
    result = BrowserAccess::SendSimulatorMessage.new(identity: @identity, channel_id: @channel.id,
      key: SecureRandom.uuid, data: payload).call
    Attendances::SupportCase.find(result.fetch(:case_id))
  end

  def command(record, token, params, key)
    post "/api/v1/cases/#{record.id}/actions", params: params.merge(expected_version: record.version),
      headers: headers(token).merge("Idempotency-Key" => key), as: :json
  end
end
