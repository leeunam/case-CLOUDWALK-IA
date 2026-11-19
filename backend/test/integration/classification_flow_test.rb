require "test_helper"

class ClassificationFlowTest < ActionDispatch::IntegrationTest
  include ActiveSupport::Testing::TimeHelpers

  setup do
    Rails.application.load_seed
    @brand = Operations::Brand.find_by!(code: "aurora")
    @channel = @brand.channels.find_by!(kind: "chat")
    @old_channel_secret = ENV["CLOUDWALK_CHANNEL_SECRET"]
    @old_passwords = ENV["CLOUDWALK_DEMO_PASSWORDS"]
    @old_mode = ENV["CLOUDWALK_JEV_MODE"]
    @forgery_protection = Api::V1::BrowserController.allow_forgery_protection
    Api::V1::BrowserController.allow_forgery_protection = true
    ENV["CLOUDWALK_CHANNEL_SECRET"] = "classification-test-channel-root"
    ENV["CLOUDWALK_DEMO_PASSWORDS"] = { "supervisor@example.test" => "test", "bia@example.test" => "test" }.to_json
    ENV["CLOUDWALK_JEV_MODE"] = "fixture"
  end

  teardown do
    ENV["CLOUDWALK_CHANNEL_SECRET"] = @old_channel_secret
    ENV["CLOUDWALK_DEMO_PASSWORDS"] = @old_passwords
    ENV["CLOUDWALK_JEV_MODE"] = @old_mode
    Api::V1::BrowserController.allow_forgery_protection = @forgery_protection
  end

  test "complemento executado uma vez preserva campo, evidência e rodada" do
    raw = body(text: "Qual é o prazo de confirmação de um Pix?", priority: "basic")
    record = receive(raw)
    receive(raw)
    request = Classification::Request.find_by!(support_case: record)

    2.times { Classification::CompleteRequestJob.perform_now(request.id) }

    assert_equal "ai_active", record.reload.status
    assert_equal 2, record.classification_version
    assert_equal ["pix", "jev", "basic", "channel"], record.classification.values_at(
      :category, :category_source, :priority, :priority_source)
    assert_equal 1, record.messages.count
    assert_equal 1, record.turns.count
    attempt = request.attempts.sole
    assert_equal "applied", attempt.disposition
    assert_equal "jev-fixture", attempt.evidence.fetch("model")
    assert_equal ["category"], attempt.evidence.fetch("answers").keys
  end

  test "classificação completa e entrada inválida não criam pedidos Jev" do
    complete = receive(body(text: "Pix", category: "pix", priority: "basic"))
    invalid = receive(body(text: "Pix", category: "fora", priority: "basic"))

    assert_equal "ai_active", complete.status
    assert_equal "classification_review", invalid.status
    assert_equal "invalid_input", invalid.blocking_reason
    assert_equal "basic", invalid.priority
    refute Classification::Request.exists?(support_case: [complete, invalid])
    assert_empty invalid.turns
  end

  test "abstenção vai à revisão com evidência" do
    record = receive(body(text: "Olá", priority: "basic"))
    request = Classification::Request.find_by!(support_case: record)
    Classification::CompleteRequestJob.perform_now(request.id)

    assert_equal "classification_review", record.reload.status
    assert_equal "insufficient_information", record.blocking_reason
    assert_equal "informacao_insuficiente", request.attempts.sole.evidence.dig("answers", "category", "choice")
    assert_empty record.turns
  end

  test "retry after persiste até a segunda tentativa e a falha definitiva vai à revisão" do
    record = receive(body(text: "Pix", priority: "basic"))
    request = Classification::Request.find_by!(support_case: record)
    classifier = ->(**) do
      Classification::Jev::Classifier::Result.new(status: :review, classification: {},
        issues: { provider: :http_error }, evidence: { http_status: 429 },
        retryable: true, retry_after_seconds: 75)
    end
    service = Classification::CompleteRequest.new(request.id, classifier: classifier)

    freeze_time(with_usec: true) do
      service.call
      assert_equal 75.seconds.from_now, request.reload.available_at
      service.call
      assert_equal ["retry"], request.attempts.pluck(:disposition)
      travel_to 75.seconds.from_now, with_usec: true
      service.call
    end

    assert_equal "classification_review", record.reload.status
    assert_equal "http_error", record.blocking_reason
    assert_equal %w[retry review], request.attempts.order(:number).pluck(:disposition)
    assert request.reload.completed_at
  end

  test "recuperação de lease vencido respeita o orçamento de tentativas" do
    record = receive(body(text: "Qual é o prazo do Pix?", priority: "basic"))
    request = Classification::Request.find_by!(support_case: record)
    request.attempts.create!(number: 1)
    adapter = Classification::CompleteRequestJob.queue_adapter
    adapter.enqueued_jobs.clear

    Classification::RecoverRequestsJob.perform_now
    assert adapter.enqueued_jobs.any? { |job| job[:job] == Classification::CompleteRequestJob && job[:args] == [request.id] }
    Classification::CompleteRequestJob.perform_now(request.id)

    assert_equal %w[expired applied], request.attempts.order(:number).pluck(:disposition)
    assert_equal "ai_active", record.reload.status
  end

  test "supervisão corrige com CSRF, versão, idempotência e auditoria" do
    record = receive(body(text: "Pix", category: "fora", priority: "basic"))
    payload = { expected_version: record.version, category: "pix", priority: "urgent", reason: "Operação parada" }
    csrf = login("bia@example.test")
    correct(record, payload, csrf, "revision")
    assert_response 403

    csrf = login("supervisor@example.test")
    correct(record, payload, nil, "revision")
    assert_response 403
    correct(record, payload, csrf, "revision")
    assert_response 200
    original = response.parsed_body
    correct(record, payload, csrf, "revision")
    assert_response 200
    assert_equal original, response.parsed_body
    correct(record, payload.merge(reason: "outro motivo"), csrf, "revision")
    assert_response 409
    correct(record, payload, csrf, "new-key")
    assert_response 409

    assert_equal 1, record.turns.count
    assert_equal 1, record.command_receipts.count
    audit = record.audits.find_by!(event_type: "case.classification.corrected")
    assert_equal "Operação parada", audit.reason
    assert_equal "urgent", audit.details.dig("classification", "priority")
  end

  private

  def body(**data)
    { external_customer_id: SecureRandom.uuid, external_conversation_id: SecureRandom.uuid,
      source_event_id: SecureRandom.uuid }.merge(data).to_json
  end

  def receive(raw)
    post "/webhooks/v1/channels/#{@channel.id}/messages", params: raw,
      headers: WebhookV1::Signature.headers(WebhookV1::Signature.channel_secret(@channel), raw)
        .merge("Content-Type" => "application/json")
    assert_response 202
    Attendances::SupportCase.find(response.parsed_body.fetch("case_id"))
  end

  def login(email)
    get "/api/v1/session"
    post "/api/v1/session", params: { email: email, password: "test" }, as: :json,
      headers: { "X-CSRF-Token" => response.parsed_body.fetch("csrf_token") }
    assert_response 200
    response.parsed_body.fetch("csrf_token")
  end

  def correct(record, payload, csrf, key)
    post "/api/v1/cases/#{record.id}/classification", params: payload, as: :json,
      headers: { "Idempotency-Key" => key, "X-CSRF-Token" => csrf }.compact
  end
end
