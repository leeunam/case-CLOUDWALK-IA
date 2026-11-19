require "test_helper"

class HumanServiceTest < ActionDispatch::IntegrationTest
  setup do
    @environment = ENV.to_h.slice("CLOUDWALK_CHANNEL_SECRET", "CLOUDWALK_AGENT_EVENTS_SECRET", "CLOUDWALK_DEMO_PASSWORDS")
    ENV.update("CLOUDWALK_CHANNEL_SECRET" => "test-channel", "CLOUDWALK_AGENT_EVENTS_SECRET" => "test-agent",
               "CLOUDWALK_DEMO_PASSWORDS" => JSON.generate(
                 "alex@example.test" => "test-password", "bia@example.test" => "test-password",
                 "supervisor@example.test" => "test-password"
               ))
    @forgery_protection = Api::V1::BrowserController.allow_forgery_protection
    Api::V1::BrowserController.allow_forgery_protection = true
    Rails.application.load_seed
    @aurora = Operations::Brand.find_by!(code: "aurora")
    @horizonte = Operations::Brand.find_by!(code: "horizonte")
    @alex = Operations::User.find_by!(email: "alex@example.test")
    @bia = Operations::User.find_by!(email: "bia@example.test")
    @bia.update!(available: false)
  end

  teardown do
    %w[CLOUDWALK_CHANNEL_SECRET CLOUDWALK_AGENT_EVENTS_SECRET CLOUDWALK_DEMO_PASSWORDS].each { |key| ENV[key] = @environment[key] }
    Api::V1::BrowserController.allow_forgery_protection = @forgery_protection
  end

  test "handoff, human reply, customer return, resume and resolution preserve the history" do
    record = handoff(priority: "urgent")
    assert record.handoff.fetch("message_ids").include?(record.messages.first.id)
    distribute
    assert_equal "human_active", record.reload.status
    assert_equal @alex.attendant.id, record.assignee_id
    assert_equal 1, record.audits.where(event_type: "case.human.assigned").count

    login(@alex.email)
    payload = { text: "Vou verificar.", expected_version: record.version }
    command(record, "messages", payload, key: "reply", csrf: "invalid")
    assert_response 403
    command(record, "messages", payload, key: "reply")
    assert_response 201
    original = json
    assert_contract("CaseMessageResult", original)
    command(record, "messages", payload, key: "reply")
    assert_response 201
    assert_equal original, json
    command(record, "messages", payload.merge(text: "Outro texto"), key: "reply")
    assert_response 409
    command(record, "messages", payload, key: "different-command")
    assert_response 409
    assert_equal 1, record.messages.where(author_type: "human").count

    wait_for_customer(record)
    competing = handoff(priority: "urgent")
    distribute
    assert_equal "human_active", competing.reload.status
    receipt = return_from_customer(record, event_id: "return")
    assert_equal receipt, return_from_customer(record, event_id: "return")
    distribute
    assert_equal ["waiting_resumption", @alex.attendant.id, "active_capacity"],
                 [record.reload.status, record.assignee_id, record.blocking_reason]
    assert_equal 4, record.messages.count
    assert_equal 1, record.audits.where(event_type: "case.human.customer_returned").count
    assigned_at = @alex.reload.last_human_assignment_at

    resolve(competing)
    distribute
    assert_equal "human_active", record.reload.status
    assert_equal @alex.attendant.id, record.assignee_id
    assert_equal assigned_at, @alex.reload.last_human_assignment_at
    payload = { type: "resolve", expected_version: record.version }
    command(record, "actions", payload, key: "resolve-record")
    assert_response 200
    original = json
    command(record, "actions", payload, key: "resolve-record")
    assert_response 200
    assert_equal original, json
    assert_equal %w[customer human human customer], record.messages.order(:sequence).pluck(:author_type)
    assert_equal [0, 0], operation.values_at("active_count", "portfolio_count")

    login("supervisor@example.test")
    get "/api/v1/cases/#{record.id}/audit", params: { limit: 2 }
    assert_response 200
    assert_contract("AuditList", json)
    assert_equal "case.human.resolved", json.fetch("items").first.fetch("type")
    cursor = json.fetch("next_cursor")
    previous_ids = json.fetch("items").pluck("id")
    get "/api/v1/cases/#{record.id}/audit", params: { limit: 2, cursor: cursor }
    assert_response 200
    assert_empty previous_ids & json.fetch("items").pluck("id")
    get "/api/v1/cases/#{competing.id}/audit", params: { cursor: cursor }
    assert_response 422
  end

  test "six pending cases hold the entire portfolio even if all customers return" do
    login(@alex.email)
    portfolio = Array.new(6) do
      record = handoff(priority: "urgent")
      distribute
      wait_for_customer(record)
      record
    end
    seventh = handoff(priority: "urgent")
    distribute
    assert_equal ["waiting_human", "portfolio_limit"], [seventh.reload.status, seventh.blocking_reason]
    assert_equal [0, 6], operation.values_at("active_count", "portfolio_count")

    @alex.capacity_profiles.find_by!(active: true).update!(portfolio_limit: 4)
    portfolio.each { |record| return_from_customer(record) }
    distribute
    assert_equal [1, 6], operation.values_at("active_count", "portfolio_count")
    assert_equal({ "human_active" => 1, "waiting_resumption" => 5 }, Attendances::SupportCase
      .where(id: portfolio.map(&:id), assignee: @alex.attendant).group(:status).count)
    assert_nil seventh.reload.assignee_id
  end

  test "brand switch drains active work and postpones returns from the former brand" do
    login(@alex.email)
    pending = handoff(priority: "urgent")
    distribute
    wait_for_customer(pending)
    active = handoff
    distribute
    patch_operation(switch_target_brand_id: @horizonte.id)
    assert_response 200
    assert_equal [@aurora.id, @horizonte.id], json.fetch("operation").values_at("active_brand_id", "switch_target_brand_id")
    during_switch = handoff
    distribute
    assert_equal ["waiting_human", "brand_switch_pending"], [during_switch.reload.status, during_switch.blocking_reason]
    resolve(active)
    assert_equal [@horizonte.id, nil], operation.values_at("active_brand_id", "switch_target_brand_id")
    assert_equal 1, Operations::AnalystOperationAudit.where(user: @alex, event_type: "analyst.brand.switched").count

    return_from_customer(pending)
    distribute
    assert_equal ["waiting_resumption", "different_operating_brand"], [pending.reload.status, pending.blocking_reason]
    assert_equal [0, 1], operation.values_at("active_count", "portfolio_count")
    patch_operation(switch_target_brand_id: @aurora.id)
    assert_response 200
    distribute
    assert_equal "human_active", pending.reload.status
    assert_equal @alex.attendant.id, pending.assignee_id
  end

  test "transfer revalidates brand, role, destination and queue access" do
    record = handoff
    distribute
    destination_queue = @aurora.support_queues.find_by!(code: "specialist")
    data = { type: "transfer", reason: "Especialização", expected_version: record.reload.version,
             destination_queue_id: destination_queue.id, destination_assignee_id: @bia.attendant.id }
    login(@bia.email)
    command(record, "actions", data)
    assert_response 403
    get "/api/v1/cases/#{record.id}/audit"
    assert_response 403
    command(record, "messages", { text: "Sem responsabilidade.", expected_version: record.version })
    assert_response 403
    patch_operation(switch_target_brand_id: @horizonte.id)
    assert_response 403
    external = handoff(brand: @horizonte)
    command(external, "actions", data)
    assert_response 404

    login("supervisor@example.test")
    command(record, "actions", data.merge(destination_queue_id: external.queue_id))
    assert_response 422
    command(record, "actions", data)
    assert_response 422
    assert_equal "analyst_unavailable", json.dig("error", "details", "reason")
    @bia.update!(available: true)
    initial_queue = record.queue_id
    command(record, "actions", data)
    assert_response 200
    assert_contract("Case", json)
    assert_equal ["human_active", destination_queue.id, @bia.attendant.id],
                 [record.reload.status, record.queue_id, record.assignee_id]
    audit = record.audits.find_by!(event_type: "case.human.transferred")
    assert_equal [initial_queue, destination_queue.id, @alex.attendant.id, @bia.attendant.id],
                 audit.details.values_at("previous_queue_id", "queue_id", "previous_assignee_id", "assignee_id")

    login(@bia.email)
    wait_for_customer(record)
    login("supervisor@example.test")
    command(record, "actions", data.merge(expected_version: record.reload.version, destination_assignee_id: nil))
    assert_response 200
    assert_equal ["waiting_customer", nil], [record.reload.status, record.assignee_id]
    return_from_customer(record)
    assert_equal "waiting_human", record.reload.status
    distribute
    assert_equal "human_active", record.reload.status
  end

  test "distribution uses absolute load, longest without assignment and stable user ID" do
    @bia.update!(available: true)
    first_user, second_user = [@alex, @bia].sort_by(&:id)
    first = handoff
    distribute
    assert_equal first_user.attendant.id, first.reload.assignee_id
    second_user.update!(last_human_assignment_at: Time.current + 1.hour)
    second = handoff
    distribute
    assert_equal second_user.attendant.id, second.reload.assignee_id
    first_user.update!(last_human_assignment_at: Time.current)
    second_user.update!(last_human_assignment_at: 1.hour.ago)
    third = handoff
    distribute
    assert_equal second_user.attendant.id, third.reload.assignee_id
  end

  test "aged case takes precedence and an incompatible case does not block the next item" do
    login(@alex.email)
    fresh = handoff(priority: "urgent")
    aged = handoff
    aged.update!(human_queue_since: 16.minutes.ago)
    compatible = handoff
    distribute
    assert_equal ["waiting_human", "human_active", "human_active"], [fresh, aged, compatible].map { |record| record.reload.status }
    assert_equal "active_capacity", fresh.blocking_reason
    assert_equal "basic", aged.priority
  end

  test "access revocation removes a waiting owner and prevents subsequent mutation" do
    record = handoff
    distribute
    login(@alex.email)
    wait_for_customer(record)
    Operations::TeamMembership.where(user: @alex).delete_all
    command(record, "actions", { type: "resolve", expected_version: record.reload.version })
    assert_response 404
    distribute
    assert_equal ["waiting_customer", nil], [record.reload.status, record.assignee_id]
    assert_equal "queue_access_revoked", record.audits.find_by!(event_type: "case.human.unassigned").reason
    return_from_customer(record)
    assert_equal "waiting_human", record.reload.status
  end

  test "supervisor can retry a failed delivery and force a handoff with its original history" do
    record = open_case(brand: @aurora, priority: "basic")
    turn = record.turns.in_flight.sole
    outbox = turn.outbox
    outbox.update!(attempts: 3, failed_at: Time.current)
    record.advance!(integration_status: "failed", blocking_reason: "bridge_http_503")
    login("supervisor@example.test")
    command(record, "actions", { type: "retry_agent", reason: "Ponte recuperada.", expected_version: record.version })
    assert_response 200
    assert_equal ["pending_delivery", nil], [record.reload.integration_status, record.blocking_reason]
    assert_equal [0, nil], [outbox.reload.attempts, outbox.failed_at]
    assert_equal turn.id, record.turns.in_flight.sole.id

    record.advance!(integration_status: "failed")
    command(record, "actions", { type: "force_handoff", reason: "Falha persistente.", summary: "Cliente precisa de ajuda.",
                                 expected_version: record.version })
    assert_response 200
    assert_contract("Case", json)
    assert_equal ["waiting_human", nil], [record.reload.status, record.assignee_id]
    assert_equal [record.messages.first.id], record.handoff.fetch("message_ids")
    assert_empty record.turns.in_flight
    distribute
    assert_equal "human_active", record.reload.status
  end

  private

  def json
    JSON.parse(response.body)
  end

  def assert_contract(definition, data)
    assert WebhookV1::Contract.valid?(definition, data), "Resposta fora de #{definition}: #{data.inspect}"
  end

  def login(email)
    get "/api/v1/session"
    post "/api/v1/session", params: { email: email, password: "test-password" }, as: :json,
         headers: { "X-CSRF-Token" => json.fetch("csrf_token") }
    assert_response 200
    @csrf = json.fetch("csrf_token")
  end

  def operation
    get "/api/v1/session"
    assert_response 200
    assert_contract("Session", json)
    json.fetch("operation")
  end

  def patch_operation(**data)
    patch "/api/v1/session/operation", params: data, as: :json, headers: { "X-CSRF-Token" => @csrf }
  end

  def command(record, path, data, key: SecureRandom.uuid, csrf: @csrf)
    post "/api/v1/cases/#{record.id}/#{path}", params: data, as: :json,
         headers: { "Idempotency-Key" => key, "X-CSRF-Token" => csrf }
  end

  def signed(path, secret, data)
    raw = JSON.generate(data)
    post path, params: raw, headers: WebhookV1::Signature.headers(secret, raw).merge("Content-Type" => "application/json")
    json
  end

  def handoff(brand: @aurora, priority: "basic")
    record = open_case(brand: brand, priority: priority)
    request = JSON.parse(record.turns.in_flight.sole.outbox.body)
    proposal = request.merge("event_id" => SecureRandom.uuid, "event_type" => "agent.handoff.proposed",
                             "payload" => { "request_event_id" => request.fetch("event_id"), "summary" => "Ajuda com Pix.",
                                            "message_ids" => [record.messages.first.id] })
    assert_equal "applied", signed("/webhooks/v1/agent/events", ENV.fetch("CLOUDWALK_AGENT_EVENTS_SECRET"), proposal).fetch("disposition")
    assert_response 200
    record.reload
  end

  def open_case(brand:, priority:)
    channel = brand.channels.find_by!(kind: "chat")
    receipt = signed("/webhooks/v1/channels/#{channel.id}/messages", WebhookV1::Signature.channel_secret(channel),
                     { source_event_id: SecureRandom.uuid, external_conversation_id: SecureRandom.uuid,
                       external_customer_id: "cliente", text: "Preciso de ajuda.", priority: priority, category: "pix" })
    assert_response 202
    Attendances::SupportCase.find(receipt.fetch("case_id"))
  end

  def return_from_customer(record, event_id: SecureRandom.uuid)
    conversation = record.channel_conversation
    receipt = signed("/webhooks/v1/channels/#{record.channel_id}/messages", WebhookV1::Signature.channel_secret(record.channel),
                     { source_event_id: event_id, external_conversation_id: conversation.external_conversation_id,
                       external_customer_id: conversation.external_customer_id, text: "Aqui estão os dados." })
    assert_response 202
    assert_equal record.id, receipt.fetch("case_id")
    receipt
  end

  def distribute
    Attendances::DistributeHumanWorkJob.perform_now(@aurora.id)
  end

  def wait_for_customer(record)
    command(record, "actions", { type: "wait_for_customer", text: "Envie o comprovante.", expected_version: record.reload.version })
    assert_response 200
    assert_contract("Case", json)
    assert_equal "waiting_customer", json.fetch("status")
  end

  def resolve(record)
    command(record, "actions", { type: "resolve", expected_version: record.reload.version })
    assert_response 200
    assert_equal "resolved", json.fetch("status")
  end
end
