require "test_helper"

class AttendanceFlowTest < ActionDispatch::IntegrationTest
  setup do
    @environment = ENV.to_h.slice("CLOUDWALK_CHANNEL_SECRET", "CLOUDWALK_AGENT_EVENTS_SECRET", "CLOUDWALK_DEMO_PASSWORDS")
    ENV.update(
      "CLOUDWALK_CHANNEL_SECRET" => "test-channel",
      "CLOUDWALK_AGENT_EVENTS_SECRET" => "test-callback",
      "CLOUDWALK_DEMO_PASSWORDS" => JSON.generate("bia@example.test" => "test-bia-password")
    )
    @forgery_protection = Api::V1::BrowserController.allow_forgery_protection
    Api::V1::BrowserController.allow_forgery_protection = true
    Rails.application.load_seed
    @chat = chat("aurora")
  end

  teardown do
    %w[CLOUDWALK_CHANNEL_SECRET CLOUDWALK_AGENT_EVENTS_SECRET CLOUDWALK_DEMO_PASSWORDS].each do |key|
      ENV[key] = @environment[key]
    end
    Api::V1::BrowserController.allow_forgery_protection = @forgery_protection
  end

  test "two turns persist and repeat only the original effects" do
    first = post_channel(channel_body)
    assert_response 202
    validate("ChannelReceipt", first)
    assert_equal first, post_channel(channel_body)
    assert_response 202
    post_channel(channel_body + " ")
    assert_response 409
    assert_equal "idempotency_conflict", json.dig("error", "code")

    record = Attendances::SupportCase.find(first.fetch("case_id"))
    assert_equal 1, record.messages.count
    assert_equal 1, record.turns.count
    request1 = request_for(record)
    assert_equal first.fetch("correlation_id"), request1.fetch("correlation_id")
    assert_equal first.fetch("case_id"), request1.fetch("case_id")
    assert_equal [1], request1.dig("payload", "history").map { |message| message.fetch("sequence") }
    reply = proposal(request1, "reply")
    assert_equal "applied", post_result(reply).fetch("disposition")
    assert_equal "duplicate", post_result(reply).fetch("disposition")
    post_result(reply.deep_merge("payload" => { "text" => "Alteração indevida." }))
    assert_response 409

    continuation = channel_body(source_event_id: "msg-2", text: "Funcionou. Obrigado!", category: nil, priority: nil)
    assert_equal first, post_channel(continuation)
    request2 = request_for(record)
    assert_equal [1, 2, 3], request2.dig("payload", "history").map { |message| message.fetch("sequence") }
    assert_equal "applied", post_result(proposal(request2, "resolve")).fetch("disposition")
    assert_equal %w[resolved idle], [record.reload.status, record.integration_status]
    assert_equal [1, 2, 3, 4], record.messages.order(:sequence).pluck(:sequence)
    assert_equal 2, record.turns.count

    get "/api/v1/cases/#{record.id}/messages"
    assert_response 401
    login
    get "/api/v1/cases/#{record.id}"
    validate("Case", json)
    assert_equal "resolved", json.fetch("status")
    assert_nil json.fetch("assignee")

    get "/api/v1/cases/#{record.id}/messages", params: { limit: 2 }
    validate("MessageList", json)
    assert_equal 2, json.fetch("next_after_sequence")
    get "/api/v1/cases/#{record.id}/messages", params: { after_sequence: 2 }
    validate("MessageList", json)
    assert_equal %w[customer ai], json.fetch("items").map { |message| message.dig("author", "type") }
    assert_nil json.fetch("next_after_sequence")
  end

  test "a resolution with new messages opens another turn and stale results are audited" do
    record = Attendances::SupportCase.find(post_channel(channel_body).fetch("case_id"))
    initial = request_for(record)
    assert_equal "applied", post_result(proposal(initial, "reply")).fetch("disposition")

    post_channel(channel_body(source_event_id: "msg-2", text: "Entendi."))
    second = request_for(record)
    post_channel(channel_body(source_event_id: "msg-3", text: "Ainda preciso de ajuda."))
    assert_equal 1, record.turns.in_flight.count
    assert_equal 2, record.turns.count

    assert_equal "applied", post_result(proposal(second, "resolve")).fetch("disposition")
    assert_equal "ai_active", record.reload.status
    third = request_for(record)
    assert_equal [1, 2, 3, 4, 5], third.dig("payload", "history").map { |message| message.fetch("sequence") }

    stale = proposal(second, "resolve")
    assert_equal "discarded", post_result(stale).fetch("disposition")
    assert_equal "duplicate", post_result(stale).fetch("disposition")
    assert_equal 1, record.audits.where(event_type: "agent.result.discarded").count
    assert_equal "applied", post_result(proposal(third, "resolve")).fetch("disposition")
    assert_equal "resolved", record.reload.status

    fresh = post_channel(channel_body(source_event_id: "msg-4"))
    assert_equal record.id, Attendances::SupportCase.find(fresh.fetch("case_id")).previous_case_id
    assert_not_equal fresh, post_channel(channel_body)
    assert_equal record.id, json.fetch("case_id")
  end

  test "the bridge acknowledgement and an early result do not overwrite a newer state" do
    record = Attendances::SupportCase.find(post_channel(channel_body).fetch("case_id"))
    request = request_for(record)
    delivery = AgentIntegration::DeliverOutbox.new(url: "http://bridge.test/webhooks/v1/agent/requests", secret: "test")
    def delivery.publish(_body) = "bridge_http_503"
    assert delivery.run_once
    outbox = record.turns.sole.outbox.reload
    assert_nil outbox.published_at
    assert_equal "pending_delivery", record.reload.integration_status

    outbox.update!(next_attempt_at: Time.current)
    def delivery.publish(_body) = "published"
    assert delivery.run_once
    assert_equal "awaiting_result", record.reload.integration_status
    assert_equal 2, outbox.reload.attempts
    assert_equal request.fetch("event_id"), JSON.parse(outbox.body).fetch("event_id")
    assert_equal "applied", post_result(proposal(request, "reply")).fetch("disposition")

    post_channel(channel_body(source_event_id: "msg-2", text: "Funcionou."))
    assert_equal "applied", post_result(proposal(request_for(record), "resolve")).fetch("disposition")
    assert delivery.run_once
    assert_equal "resolved", record.reload.status
    assert_equal "idle", record.integration_status
  end

  test "signed boundaries and case scope are enforced" do
    post_channel(channel_body, timestamp: (Time.now.to_i - 301).to_s)
    assert_response 401
    post_channel(channel_body, secret: "wrong")
    assert_response 401
    post_channel(channel_body, timestamp: ["123", "123"].join(","))
    assert_response 401
    post_channel("{")
    assert_response 422

    visible = post_channel(channel_body).fetch("case_id")
    other = post_channel(channel_body, channel: chat("horizonte")).fetch("case_id")
    login_without_csrf
    login
    get "/api/v1/case-filters"
    validate("CaseFilters", json)
    assert_equal [@chat.brand_id], json.fetch("brands").map { |brand| brand.fetch("id") }

    get "/api/v1/cases"
    validate("CaseList", json)
    assert_equal [visible], json.fetch("items").map { |record| record.fetch("id") }
    get "/api/v1/cases/#{other}"
    assert_response 404
    get "/api/v1/cases/#{other}/messages"
    assert_response 404

    get "/api/v1/session"
    delete "/api/v1/session", headers: { "X-CSRF-Token" => json.fetch("csrf_token") }
    assert_response 204
    get "/api/v1/cases"
    assert_response 401
  end

  test "missing and invalid classification are accepted without a broker request" do
    missing = post_channel(channel_body(category: nil))
    invalid = post_channel(channel_body(source_event_id: "invalid", external_conversation_id: "other", priority: {}))
    assert_response 202
    pending = Attendances::SupportCase.find(missing.fetch("case_id"))
    review = Attendances::SupportCase.find(invalid.fetch("case_id"))
    assert_equal ["classification_pending", "classification_review"], [pending.status, review.status]
    assert_equal "basic", pending.priority
    assert_equal "pix", review.category
    assert_empty AgentIntegration::AgentOutbox.all
  end

  private

  def json
    JSON.parse(response.body)
  end

  def chat(brand)
    Operations::Brand.find_by!(code: brand).channels.find_by!(kind: "chat")
  end

  def channel_body(**overrides)
    JSON.generate({
      source_event_id: "msg-1", external_conversation_id: "conversation", external_customer_id: "customer",
      text: "Qual é o prazo de confirmação de um Pix?", category: "pix", priority: "basic"
    }.merge(overrides))
  end

  def post_channel(raw, channel: @chat, secret: WebhookV1::Signature.channel_secret(channel), timestamp: Time.now.to_i.to_s)
    post "/webhooks/v1/channels/#{channel.id}/messages", params: raw,
         headers: WebhookV1::Signature.headers(secret, raw, timestamp: timestamp).merge("Content-Type" => "application/json")
    json
  end

  def post_result(data)
    raw = JSON.generate(data)
    post "/webhooks/v1/agent/events", params: raw,
         headers: WebhookV1::Signature.headers(ENV.fetch("CLOUDWALK_AGENT_EVENTS_SECRET"), raw)
                                     .merge("Content-Type" => "application/json")
    result = json
    validate("AgentReceipt", result) if response.status == 200
    result
  end

  def validate(definition, data)
    assert WebhookV1::Contract.valid?(definition, data), "Resposta fora de #{definition}: #{data.inspect}"
  end

  def request_for(record)
    request = JSON.parse(record.turns.in_flight.sole.outbox.body)
    validate("AgentTurnRequested", request)
    request
  end

  def proposal(request, type)
    request.merge("event_id" => SecureRandom.uuid, "event_type" => "agent.#{type}.proposed",
                  "payload" => { "request_event_id" => request.fetch("event_id"), "text" => "Resposta sintética." })
  end

  def login_without_csrf
    post "/api/v1/session", params: { email: "bia@example.test", password: "test-bia-password" }, as: :json
    assert_response 403
  end

  def login
    get "/api/v1/session"
    validate("Session", json)
    token = json.fetch("csrf_token")
    post "/api/v1/session", params: { email: "bia@example.test", password: "test-bia-password" },
         as: :json, headers: { "X-CSRF-Token" => token }
    assert_response 200
    validate("Session", json)
  end
end
