require "test_helper"

class SetfitTurnContractTest < ActionDispatch::IntegrationTest
  setup do
    @old_passwords = ENV["CLOUDWALK_DEMO_PASSWORDS"]
    ENV["CLOUDWALK_DEMO_PASSWORDS"] = JSON.generate("bia@example.test" => "synthetic")
    Rails.application.load_seed
    @channel = Operations::Brand.find_by!(code: "aurora").channels.find_by!(kind: "chat")
  end

  teardown do
    ENV["CLOUDWALK_DEMO_PASSWORDS"] = @old_passwords
  end

  test "mixed sources survive later turns, staff projection and ambiguous delivery" do
    data = { "source_event_id" => "mixed-1", "external_conversation_id" => "mixed", "external_customer_id" => "customer",
             "text" => "Preciso de ajuda com o Pix.", "category" => "pix", "priority" => "basic" }
    receipt = receive(data)
    record = Attendances::SupportCase.find(receipt.fetch(:case_id))
    first = record.turns.sole
    assert_equal "1.0", JSON.parse(first.outbox.body).fetch("schema_version")
    finish(first)

    # O complemento será produzido pelo provedor de B. Esta fronteira consome a origem persistida.
    record.update!(priority_source: "setfit", integration_status: "idle")
    followup = data.merge("source_event_id" => "mixed-2", "text" => "Ainda preciso de ajuda.")
    assert_equal receipt, receive(followup)
    turn = record.turns.in_flight.sole
    body = turn.outbox.body
    request = JSON.parse(body)
    assert_equal "1.1", request.fetch("schema_version")
    assert_equal turn.request_event_id, request.fetch("event_id")
    assert_equal %w[channel setfit], request.dig("payload", "classification").values_at("category_source", "priority_source")
    assert WebhookV1::Contract.valid?("AgentTurnRequested", request)
    assert_not WebhookV1::Contract.valid?("AgentTurnRequested", request.merge("schema_version" => "1.0"))
    get "/api/v1/session"
    post "/api/v1/session", params: { email: "bia@example.test", password: "synthetic" }, as: :json,
         headers: { "X-CSRF-Token" => response.parsed_body.fetch("csrf_token") }
    assert_response :success
    get "/api/v1/cases/#{record.id}"
    assert_response :success
    staff = response.parsed_body
    assert WebhookV1::Contract.valid?("CaseV11", staff)
    assert_equal request.dig("payload", "classification"), staff.fetch("classification")
    get "/api/v1/cases"
    assert_response :success
    assert WebhookV1::Contract.valid?("CaseListV11", response.parsed_body)
    assert_equal staff, response.parsed_body.fetch("items").sole

    first.outbox.update!(published_at: Time.current)
    delivery = AgentIntegration::DeliverOutbox.new(url: "http://bridge.test", secret: "synthetic")
    bodies = []
    delivery.define_singleton_method(:publish) do |bytes|
      bodies << bytes
      bodies.size == 1 ? "bridge_http_503" : "published"
    end
    assert delivery.run_once
    travel 4.seconds do
      assert delivery.run_once
    end
    assert_equal [body, body], bodies
    assert_equal receipt, receive(followup)
    assert_equal 2, record.turns.count

    finish(turn)
    record.reload.update!(integration_status: "idle", category_source: "setfit", priority_source: "channel")
    receive(data.merge("source_event_id" => "mixed-3", "text" => "Qual é o próximo passo?"))
    next_request = JSON.parse(record.turns.in_flight.sole.outbox.body)
    assert_equal "1.1", next_request.fetch("schema_version")
    assert_not_equal request.fetch("event_id"), next_request.fetch("event_id")
  end

  private

  def finish(turn)
    turn.update!(completed_at: Time.current)
  end

  def receive(data)
    Attendances::ReceiveChannelMessage.new(@channel, data, JSON.generate(data)).call
  end
end
