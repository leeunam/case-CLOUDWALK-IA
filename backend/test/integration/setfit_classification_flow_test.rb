require "test_helper"
require_relative "../support/setfit_endpoint"

class SetfitClassificationFlowTest < ActiveSupport::TestCase
  include ActiveJob::TestHelper

  setup do
    Rails.application.load_seed
    @brand = Operations::Brand.find_by!(code: "aurora")
    @channel = @brand.channels.find_by!(kind: "chat")
    @endpoint = SetfitEndpoint.new
    @previous = %w[CLASSIFICATION_PROVIDER CLOUDWALK_JEV_MODE SETFIT_URL].index_with { |key| ENV[key] }
    ENV.update("CLASSIFICATION_PROVIDER" => "setfit", "SETFIT_URL" => @endpoint.url, "CLOUDWALK_JEV_MODE" => "fixture")
  end

  teardown do
    @endpoint.close
    @previous.each { |key, value| ENV[key] = value }
  end

  test "um ou dois ausentes gravam snapshot e uma rodada por caso mesmo após reentrega ou mudança de provedor" do
    [{ "category" => "pix", "priority" => "" }, { "priority" => "basic" }, {}].each do |fields|
      ENV["CLASSIFICATION_PROVIDER"] = "setfit"
      data = channel_payload.merge(fields)
      record = receive(data)
      request = request_for(record)
      assert_equal "classification_setfit", request.job_queue
      assert_equal record.id, receive(data).id
      assert_raises(WebhookV1::Error) { receive(data.merge("text" => "outro")) }
      ENV["CLASSIFICATION_PROVIDER"] = "jev"
      2.times { Classification::CompleteRequestJob.perform_now(request.id) }
      attempt = request.attempts.sole
      assert_equal "applied", attempt.disposition
      assert_equal %w[setfit http], attempt.snapshot.values_at("provider", "provider_mode")
      assert_equal @brand.catalog_version, attempt.snapshot.fetch("catalog_version")
      assert_equal record.messages.sole.id, attempt.snapshot.fetch("message_id")
      received = fields.values_at("category", "priority").map(&:presence)
      assert_equal received, attempt.snapshot.fetch("received").values_at("category", "priority")
      assert_equal Classification::SetfitContract.current.identities, attempt.snapshot.fetch("identities")
      assert_equal attempt.id, @endpoint.requests.last.fetch("id")
      assert_equal attempt.id, attempt.evidence.fetch("id")
      assert_equal attempt.snapshot.fetch("catalog_sha256"), attempt.evidence.fetch("catalog_sha256")
      assert_equal received.map { |value| value ? 0 : 1 }, attempt.evidence.fetch("calls").values_at("category", "priority")
      assert_equal [received[0] || "pix", received[1] || "urgent"], record.reload.classification.values_at(:category, :priority)
      assert_equal 1, record.turns.count
      assert_equal 1, AgentIntegration::AgentOutbox.where(agent_turn: record.turns).count
      assert_equal received.map { |value| value ? "channel" : "setfit" }, record.classification.values_at(:category_source, :priority_source)
      assert_equal "1.1", JSON.parse(record.turns.sole.outbox.body).fetch("schema_version")
      audit = record.audits.where(event_type: "case.classification.completed").sole
      assert_equal attempt.id, audit.details.fetch("attempt_id")
      refute_includes [attempt.snapshot, attempt.evidence, audit.details].to_json, data.fetch("text")
    end
    assert_equal 3, @endpoint.requests.size
  end

  test "completa com catálogo operacional e inválidas não criam job; incompatível recusa antes do HTTP" do
    @brand.categories.create!(code: "extra", name: "Categoria operacional")
    record = receive(channel_payload.merge("category" => "extra", "priority" => "basic"))
    assert_equal "ai_active", record.status
    refute Classification::Request.exists?(support_case: record)
    [" ", 1, false, {}, "inexistente"].each do |invalid|
      record = receive(channel_payload.merge("category" => invalid))
      assert_equal "invalid_input", record.blocking_reason
      refute Classification::Request.exists?(support_case: record)
      assert_empty record.turns
    end
    %w[pix extra].each do |valid|
      record = receive(channel_payload.merge("category" => valid))
      request = request_for(record)
      Classification::CompleteRequestJob.perform_now(request.id)
      assert_equal "unsupported_catalog", record.reload.blocking_reason
      assert_equal [valid, nil], record.classification.values_at(:category, :priority)
      assert_empty record.turns
    end
    assert_empty @endpoint.requests
  end

  test "busy e not_ready só repetem uma vez na fila fixada e mantêm a primeira evidência" do
    @endpoint.reply = ->(_) { [503, SetfitEndpoint.fixture("503-busy")] }
    record = receive(channel_payload.merge("category" => "pix"))
    request = request_for(record)
    Classification::CompleteRequestJob.perform_now(request.id)
    first = request.attempts.sole
    assert_equal ["retry", "busy", 503], [first.disposition, first.issues["provider"], first.evidence["http_status"]]
    ENV["CLASSIFICATION_PROVIDER"] = "jev"
    travel_to(request.reload.available_at + 1.second) do
      assert_enqueued_with(job: Classification::CompleteRequestJob, args: [request.id], queue: "classification_setfit") do
        Classification::RecoverRequestsJob.perform_now
      end
      @endpoint.reply = ->(_) { [503, SetfitEndpoint.fixture("503-not-ready")] }
      2.times { Classification::CompleteRequestJob.perform_now(request.id) }
    end
    assert_equal %w[retry review], request.attempts.order(:number).pluck(:disposition)
    assert_equal "not_ready", record.reload.blocking_reason
    assert_equal first.attributes, first.reload.attributes
    assert_equal 2, @endpoint.requests.size
    assert_empty record.turns
  end

  test "recusas 422 falha e resposta parcial encerram sem repetir nem preencher" do
    replies = [
      [->(_) { [422, SetfitEndpoint.fixture("422-text-out-of-scope")] }, "text_out_of_scope"],
      [->(_) { [502, SetfitEndpoint.fixture("502-worker-failure")] }, "worker_failure"],
      [->(_) { [503, { "error" => "busy" }] }, "invalid_response"],
      [lambda { |r|
        status, body = @endpoint.complete(r)
        body["applied"].delete("priority")
        [status, body]
      }, "invalid_response"]
    ]
    replies.each do |reply, reason|
      @endpoint.reply = reply
      record = receive(channel_payload)
      request = request_for(record)
      2.times { Classification::CompleteRequestJob.perform_now(request.id) }
      assert_equal reason, record.reload.blocking_reason
      assert_equal [nil, nil], record.classification.values_at(:category, :priority)
      assert_empty record.turns
      assert_equal "review", request.attempts.sole.disposition
    end
    assert_equal replies.size, @endpoint.requests.size
  end

  test "recuperação legada usa evidência do Jev e envia origem ambígua para revisão" do
    [true, false].each do |known|
      record = receive(channel_payload.merge("priority" => "basic"))
      request = request_for(record)
      request.update!(provider: nil, provider_mode: nil)
      if known
        request.attempts.create!(number: 1, disposition: "retry", finished_at: Time.current,
                                 evidence: { mode: "fixture" }, issues: { provider: "http_error" })
      end
      ENV["CLOUDWALK_JEV_MODE"] = "disabled"
      Classification::CompleteRequestJob.perform_now(request.id)
      if known
        assert_equal %w[jev fixture], request.reload.attributes.values_at("provider", "provider_mode")
        assert_equal "jev", record.reload.category_source
        assert_equal 1, record.turns.count
      else
        assert_equal "unknown", request.reload.provider
        assert_equal "invalid_classifier_mode", record.reload.blocking_reason
        assert_empty record.turns
      end
    end
    assert_empty @endpoint.requests
  end

  test "origem legada no teto preserva tentativa vencida e encerra com motivo controlado" do
    [%w[fixture jev worker_lease_expired], [nil, "unknown", "invalid_classifier_mode"]].each do |mode, provider, reason|
      record = receive(channel_payload)
      request = request_for(record)
      request.update!(provider: nil, provider_mode: nil)
      first = request.attempts.create!(number: 1, disposition: "retry", finished_at: 1.minute.ago,
        evidence: { "mode" => mode }.compact, issues: { provider: "marcador-sintetico-privado" })
      last = request.attempts.create!(number: 2, lease_expires_at: 1.second.ago, evidence: { http_status: 503 })
      2.times { Classification::CompleteRequestJob.perform_now(request.id) }

      assert_equal [provider, mode], request.reload.attributes.values_at("provider", "provider_mode")
      assert request.completed_at
      assert_equal first.attributes, first.reload.attributes
      assert_equal [first.id, last.id], request.attempts.order(:number).ids
      assert_equal ["expired", { "http_status" => 503 }], [last.reload.disposition, last.evidence]
      audit = record.audits.where(event_type: "case.classification.review").sole
      assert_equal [reason, reason, last.id], [record.reload.blocking_reason, audit.reason, audit.details["attempt_id"]]
      refute_includes audit.attributes.to_s, "marcador-sintetico-privado"
      assert_empty record.turns
      assert_empty AgentIntegration::AgentOutbox.where(agent_turn: record.turns)
    end
    assert_empty @endpoint.requests
  end

  test "motivo livre no histórico legado não chega à auditoria" do
    record = receive(channel_payload)
    request = request_for(record)
    request.update!(provider: nil, provider_mode: nil)
    last = request.attempts.create!(number: 2, finished_at: Time.current, evidence: { mode: "fixture" },
                                    issues: { provider: "marcador-sintetico-privado" })
    Classification::CompleteRequestJob.perform_now(request.id)
    assert_equal %w[jev fixture], request.reload.attributes.values_at("provider", "provider_mode")
    audit = record.audits.where(event_type: "case.classification.review").sole
    assert_equal ["invalid_response", last.id], [audit.reason, audit.details["attempt_id"]]
    refute_includes audit.attributes.to_s, "marcador-sintetico-privado"
    assert_empty @endpoint.requests
  end

  test "origem legada é fixada mesmo se faltar a mensagem inicial" do
    [[{ mode: "fixture" }, "jev", "missing_classification_text"], [{}, "unknown", "invalid_classifier_mode"]].each do |evidence, provider, reason|
      record = receive(channel_payload)
      request = request_for(record)
      request.update!(provider: nil, provider_mode: nil)
      last = request.attempts.create!(number: 1, finished_at: Time.current, evidence: evidence)
      record.messages.sole.destroy!
      Classification::CompleteRequestJob.perform_now(request.id)
      assert_equal [provider, evidence[:mode]], request.reload.attributes.values_at("provider", "provider_mode")
      assert_equal reason, record.reload.blocking_reason
      assert_equal last.id, record.audits.where(event_type: "case.classification.review").sole.details["attempt_id"]
      assert_equal last.attributes, request.attempts.sole.attributes
    end
    assert_empty @endpoint.requests
  end

  test "JSONB mantém score abaixo do corte e margem decimal exata da resposta" do
    @endpoint.reply = lambda do |request|
      status, body = @endpoint.complete(request)
      body.merge!("outcome" => "review", "applied" => {})
      field = body.fetch("fields").fetch("priority")
      field.merge!("decision" => "review", "reason" => "below_tau", "margin" => JSON::Fragment.new("0.59999999999999999"))
      field.fetch("vector")["scores"] = [0.1, 0.1, 0.05, 0.05, JSON::Fragment.new("0.69999999999999999")]
      [status, body]
    end
    record = receive(channel_payload.merge("category" => "pix"))
    request = request_for(record)
    Classification::CompleteRequestJob.perform_now(request.id)
    assert_equal "below_tau", record.reload.blocking_reason
    assert_empty record.turns

    persisted = Classification::Attempt.where(id: request.attempts.sole.id).pick(
      Arel.sql("evidence #>> '{fields,priority,vector,scores,4}'"),
      Arel.sql("evidence #>> '{fields,priority,margin}'"),
      Arel.sql("jsonb_typeof(evidence #> '{fields,priority,vector,scores,4}')"),
      Arel.sql("jsonb_typeof(evidence #> '{fields,priority,margin}')"),
      Arel.sql("(evidence #> '{fields,priority,vector,scores,4}')::numeric < (evidence #> '{fields,priority,cut,tau}')::numeric")
    )
    assert_equal ["0.69999999999999999", "0.59999999999999999", "number", "number", true], persisted
    field = request.attempts.sole.reload.evidence.dig("fields", "priority")
    assert_equal BigDecimal("0.59999999999999999"), field.fetch("margin")
    assert_operator field.fetch("vector").fetch("scores").last, :<, field.dig("cut", "tau")
  end

  test "supervisão corrige a marca autorizada e não altera a outra" do
    supervisor = Operations::User.create!(name: "Supervisão", email: "c06b@example.test", role: "supervisor")
    Operations::SupervisorBrand.create!(user: supervisor, brand: @brand)
    other = Operations::Brand.find_by!(code: "horizonte").channels.find_by!(kind: "chat")
    denied = receive(channel_payload, channel: other)
    allowed = receive(channel_payload)
    correct = lambda do |record|
      Attendances::ApplyCaseCommand.new(user: supervisor, case_id: record.id, operation: "classification",
        key: SecureRandom.uuid, data: { "expected_version" => record.version, "category" => "pix", "priority" => "urgent",
                                       "reason" => "Classificação conferida" }).call
    end
    assert_raises(ActiveRecord::RecordNotFound) { correct.call(denied) }
    assert_equal "classification_pending", denied.reload.status
    assert_empty denied.turns
    correct.call(allowed)
    assert_equal %w[supervisor supervisor], allowed.reload.classification.values_at(:category_source, :priority_source)
    assert_equal 1, allowed.turns.count
    assert_empty @endpoint.requests
  end

  private

  def channel_payload
    { "source_event_id" => SecureRandom.uuid, "external_conversation_id" => SecureRandom.uuid,
      "external_customer_id" => SecureRandom.uuid, "text" => "  Qual o prazo de um Pix?  " }
  end

  def receive(data, channel: @channel)
    receipt = Attendances::ReceiveChannelMessage.new(channel, data, JSON.generate(data)).call
    Attendances::SupportCase.find(receipt.fetch(:case_id))
  end

  def request_for(record)
    Classification::Request.find_by!(support_case: record)
  end
end
