require "test_helper"
require "open3"
require "tempfile"
require "timeout"

class AgentPilotLedgerTest < ActionDispatch::IntegrationTest
  self.use_transactional_tests = false

  Pilot = AgentIntegration::Pilot
  SECRET = "e01-test-contract-key"
  ENV_KEYS = %w[CLOUDWALK_E01_LEDGER_SECRET CLOUDWALK_E01_PREFLIGHT_PATH].freeze

  setup do
    @saved_env = ENV.to_h.slice(*ENV_KEYS)
    @file = Tempfile.new("e01-offline")
    ENV.update(ENV_KEYS.zip([SECRET, @file.path]).to_h)
    configure_preflight

    code = "e01_#{SecureRandom.hex(6)}"
    @brand = Operations::Brand.create!(code: code, name: code)
    @queue = @brand.support_queues.create!(code: "test", name: "Fila de teste", is_default: true)
    @channel = @brand.channels.create!(kind: "chat", name: "Chat")
    @ai = Operations::Attendant.create!(code: code, kind: "ai")
  end

  teardown do
    if @brand
      cases = Attendances::SupportCase.where(brand: @brand)
      turns = AgentIntegration::AgentTurn.where(support_case: cases)
      outboxes = AgentIntegration::AgentOutbox.where(agent_turn: turns)
      Pilot::Execution.where(request_event_id: outboxes.select(:event_id)).delete_all
      outboxes.delete_all
      turns.delete_all
      Attendances::CaseMessage.where(support_case: cases).delete_all
      Attendances::CaseAudit.where(support_case: cases).delete_all
      cases.delete_all
      Attendances::ChannelConversation.where(channel: @channel).delete_all
      @ai.destroy!
      @human&.destroy!
      Operations::ConfigurationAudit.where(brand: @brand).delete_all
      Operations::SupervisorBrand.where(brand: @brand).delete_all
      Operations::QueueTeam.where(brand: @brand).delete_all
      Operations::BrandTeam.where(brand: @brand).delete_all
      Operations::TeamMembership.where(team: @teams).delete_all if @teams
      Operations::AnalystOperationAudit.where(user: @analyst).delete_all if @analyst
      @supervisor&.destroy!
      @analyst&.destroy!
      @teams&.each(&:destroy!)
      @queue.destroy!
      @channel.destroy!
      @brand.destroy!
    end
    Pilot::Pilot.delete_all
    Pilot::Nonce.delete_all
    @file&.close!
    ENV_KEYS.each { |key| ENV[key] = @saved_env[key] }
  end

  test "autentica o vetor de bytes do contrato e mantém o nonce durante toda a janela" do
    vector = fixture("signature.json")
    ENV["CLOUDWALK_E01_LEDGER_SECRET"] = vector.fetch("fixture_key")
    headers = {
      "Content-Type" => "application/json", "X-E01-Timestamp" => vector.fetch("timestamp"),
      "X-E01-Nonce" => vector.fetch("nonce"), "X-E01-Signature" => vector.fetch("signature")
    }
    instant = Time.at(Integer(vector.fetch("timestamp")))
    travel_to(instant - 30.seconds) do
      post vector.fetch("path"), params: vector.fetch("body_utf8"), headers: headers
      assert_http [404, { "error" => "not_found" }]
      assert_equal instant + 31.seconds, Pilot::Nonce.find(vector.fetch("nonce")).expires_at
    end
    travel_to(instant + 30.seconds) do
      post vector.fetch("path"), params: vector.fetch("body_utf8"), headers: headers
      assert_http [409, { "error" => "nonce_reused" }]
    end
    travel_to(instant + 31.seconds) do
      post vector.fetch("path"), params: vector.fetch("body_utf8"), headers: headers
      assert_http [401, { "error" => "unauthenticated" }]
    end
  end

  test "recusa assinatura divergente, tempo inválido e cabeçalhos duplicados sem gravar nonce" do
    outbox = prepare_round
    raw = JSON.generate(claim_body(outbox))
    route = path(outbox, "claim")
    valid = headers(route, raw)
    variants = [
      valid.merge("X-E01-Signature" => "0" * 64),
      valid.merge("X-E01-Timestamp" => "0#{valid.fetch('X-E01-Timestamp')}"),
      valid.merge("X-E01-Nonce" => "#{valid.fetch('X-E01-Nonce')}, #{SecureRandom.uuid}"),
      valid.merge("X-E01-Signature" => "#{valid.fetch('X-E01-Signature')}, #{valid.fetch('X-E01-Signature')}"),
      valid.merge("X-E01-Timestamp" => "#{valid.fetch('X-E01-Timestamp')}, #{valid.fetch('X-E01-Timestamp')}"),
      headers(route, raw, timestamp: (Time.current.to_i - 31).to_s),
      headers(route, raw, nonce: "00000000-0000-3000-8000-000000000000"),
      valid.except("X-E01-Nonce")
    ]
    variants.each do |candidate|
      post route, params: raw, headers: candidate
      assert_http [401, { "error" => "unauthenticated" }]
    end
    post route, params: raw + " ", headers: valid
    assert_http [401, { "error" => "unauthenticated" }]
    assert_equal 0, Pilot::Nonce.count
    assert_equal 0, Pilot::Execution.count
  end

  test "rejeita transporte fora do contrato e consome nonce de corpo autenticado inválido" do
    outbox = prepare_round
    body = claim_body(outbox)
    valid = JSON.generate(body)
    invalid = [
      "[#{valid}]", valid + "{}", "{", "\xFF".b, "{\"x\":NaN}",
      valid.sub("{", "{\"owner_id\":null,"), JSON.generate(body.merge("extra" => true)),
      JSON.generate(body.merge("owner_id" => "a" * 36)), JSON.generate(body.merge("request_sha256" => "0" * 63))
    ]
    invalid.each { |bytes| assert_equal [422, { "error" => "invalid_body" }], send_op(outbox, "claim", bytes) }
    nonce = SecureRandom.uuid
    assert_equal [422, { "error" => "invalid_body" }], send_op(outbox, "claim", "{", nonce: nonce)
    assert_equal [409, { "error" => "nonce_reused" }], send_op(outbox, "claim", body, nonce: nonce)
    assert_equal [413, { "error" => "too_large" }], send_op(outbox, "claim", " " * (128.kilobytes + 1))

    route = path(outbox, "claim")
    post "#{route}?ignored=1", params: valid, headers: headers(route, valid)
    assert_http [422, { "error" => "invalid_body" }]
    post route, params: valid, headers: headers(route, valid).merge("Content-Encoding" => "gzip")
    assert_http [422, { "error" => "invalid_body" }]
    assert_equal 0, Pilot::Execution.count
  end

  test "nonces concorrentes para os mesmos e para diferentes bytes produzem somente um efeito" do
    outbox = prepare_round
    body = claim_body(outbox)
    Pilot::Pilot.create!(id: 1)

    [body, body.merge("request_sha256" => "0" * 64)].each do |duplicate|
      nonce = SecureRandom.uuid
      first = after_lock(Pilot::Pilot.find(1), -> { send_op(outbox, "claim", body, nonce: nonce) }) do
        second = Thread.new { send_op(outbox, "claim", duplicate, nonce: nonce) }
        assert_equal [409, { "error" => "nonce_reused" }], Timeout.timeout(5) { second.value }
      end.sole
      assert_equal 200, first.first
      assert_equal "reserved", first.last.fetch("state")
    end
    assert_equal 2, Pilot::Nonce.count
    assert_equal 1, Pilot::Execution.count
  end

  test "exige bytes originários vinculados à outbox antes e após uma execução" do
    outbox = prepare_round(published: false)
    body = claim_body(outbox)
    assert_equal [409, { "error" => "publication_pending" }], send_op(outbox, "claim", body)
    assert_equal [409, { "error" => "request_mismatch" }],
                 send_op(outbox, "claim", body.merge("request_sha256" => "0" * 64))
    assert_equal 0, Pilot::Execution.count

    outbox.update!(published_at: Time.current)
    assert_equal [409, { "error" => "publication_pending" }], send_op(outbox, "claim", body)
    outbox.agent_turn.update!(result_due_at: 60.seconds.from_now)
    lease = reserve(outbox, body)
    original = outbox.body
    outbox.update!(body: original + " ")
    assert_equal [409, { "error" => "request_mismatch" }], send_op(outbox, "start", lease)
    assert_equal [409, { "error" => "request_mismatch" }], send_op(outbox, "claim", claim_body(outbox))
    outbox.update!(body: original)
    assert_equal true, assert_success(send_op(outbox, "start", lease), "start_response").fetch("dispatch")
  end

  test "não reserva para marca, rodada ou geração incompatíveis" do
    outbox = prepare_round
    original = outbox.body
    %w[brand_id correlation_id case_id turn_id].each do |field|
      outbox.update!(body: JSON.generate(JSON.parse(original).merge(field => SecureRandom.uuid)))
      assert_equal [409, { "error" => "request_mismatch" }], send_op(outbox, "claim", claim_body(outbox))
    end
    outbox.update!(body: original)
    record = outbox.agent_turn.support_case
    record.update!(assignment_generation: record.assignment_generation + 1)
    assert_equal [409, { "error" => "turn_stale" }], send_op(outbox, "claim", claim_body(outbox))
    assert_equal 0, Pilot::Execution.count
  end

  test "pré-voo ausente, incompatível ou alterado bloqueia e sinaliza a operação" do
    no_path = prepare_round
    ENV.delete("CLOUDWALK_E01_PREFLIGHT_PATH")
    assert_equal [503, { "error" => "preflight_missing" }], send_op(no_path, "claim", claim_body(no_path))
    assert_failure(no_path, "preflight_missing")

    ENV["CLOUDWALK_E01_PREFLIGHT_PATH"] = @file.path
    configure_preflight("billing_terms" => fixture("billing-terms.json").merge("tariff_tiers" => "multiple"))
    unsupported = prepare_round
    assert_equal [503, { "error" => "preflight_missing" }], send_op(unsupported, "claim", claim_body(unsupported))
    assert_failure(unsupported, "preflight_missing")

    configure_preflight
    changed = prepare_round
    lease = reserve(changed)
    configure_preflight("input_rate_usd_per_million" => "11")
    assert_equal [503, { "error" => "preflight_missing" }], send_op(changed, "start", lease)
    assert_failure(changed, "preflight_missing")
    assert_equal ["expired", "10"], [execution(changed).state, execution(changed).snapshot.fetch("input_rate_usd_per_million")]
    assert_equal 0, Pilot::Pilot.find(1).dispatch_count
  end

  test "configuração sintética só passa no ambiente de teste" do
    linear = Pilot::Preflight.load!
    configure_bounded
    bounded = Pilot::Preflight.load!
    environment = Rails.env
    Rails.env = "production"
    refute linear.valid?
    refute bounded.valid?
  ensure
    Rails.env = environment if environment
  end

  test "vincula o modo financeiro às premissas e exige cobertura documentada de toda a faixa" do
    configure_preflight("mode" => "feita_verified")
    flat = Pilot::Preflight.load!
    assert_equal BigDecimal("0.0061"), flat.cost!(usage)
    refute Pilot::Preflight.new(flat.data.merge("mode" => "feita_bounded_public")).valid?

    configure_bounded
    bounded = Pilot::Preflight.load!.data
    refute Pilot::Preflight.new(bounded.merge("mode" => "feita_verified")).valid?
    assert Pilot::Preflight.new(bounded.merge("mode" => "feita_bounded_public")).valid?
    [
      { "input_cap" => 1_049_999 }, { "output_cap" => 127_999 },
      { "input_rate_usd_per_million" => "0.49999", "cache_rate_usd_per_million" => "0.49999" },
      { "output_rate_usd_per_million" => "1.79999" }, { "cache_rate_usd_per_million" => "0.02" },
      { "evidence" => bounded.fetch("evidence").except("per_request_extras") },
      { "evidence" => bounded.fetch("evidence").except("billable_usage_coverage") },
      { "evidence" => bounded.fetch("evidence").merge("account_tariff_scope" => " ") }
    ].each { |change| refute Pilot::Preflight.new(bounded.merge(change)).valid?, change.inspect }

    configure_bounded("output_cap" => 32_000)
    outbox = prepare_round
    assert_equal [503, { "error" => "preflight_missing" }], send_op(outbox, "claim", claim_body(outbox))
    assert_equal 0, Pilot::Execution.count
  end

  test "dois pedidos disputam a reserva conservadora no último saldo e no último despacho" do
    configure_bounded
    contend_for_last(spent: "0.244600000000", prior_dispatches: 23,
                     final_usage: usage.merge("input_tokens" => 1_050_000, "cached_input_tokens" => 1_050_000,
                                              "output_tokens" => 128_000))
    assert_equal BigDecimal("1"), Pilot::Pilot.find(1).spent_usd
    assert_equal 24, Pilot::Pilot.find(1).dispatch_count
    assert_equal BigDecimal("0.7554"), Pilot::Execution.sole.cost_usd
  end

  test "contabiliza toda entrada pelo teto, soma adicionais por chamada e arredonda para cima" do
    terms = fixture("billing-terms-bounded.json").merge("per_request_extra_cap_usd" => "0.010000000000")
    configure_bounded("billing_terms" => terms, "input_rate_usd_per_million" => "0.5000001",
                      "cache_rate_usd_per_million" => "0.5000001")
    [1, 0].each do |count|
      outbox = prepare_round
      lease = start_round(outbox)
      assert_equal BigDecimal("0.765400105000"), execution(outbox).reserved_usd
      reported = usage.merge("input_tokens" => count, "cached_input_tokens" => count, "output_tokens" => count)
      body = completed(outbox, lease).merge("usage" => reported)
      assert_equal "result_saved", assert_success(send_op(outbox, "complete", body), "complete_response").fetch("state")
      expected = count == 1 ? "0.010002300001" : "0.010000000000"
      assert_equal BigDecimal(expected), execution(outbox).cost_usd
    end
    assert_equal BigDecimal("0.020002300001"), Pilot::Pilot.find(1).spent_usd
  end

  test "um adicional acima do saldo por um picodólar impede o despacho" do
    terms = fixture("billing-terms-bounded.json")
    configure_bounded("billing_terms" => terms.merge("per_request_extra_cap_usd" => "0.244600000001"))
    refused = prepare_round
    assert_equal [409, { "error" => "budget_exhausted" }], send_op(refused, "claim", claim_body(refused))
    assert_equal 0, Pilot::Pilot.find(1).dispatch_count

    configure_bounded("billing_terms" => terms.merge("per_request_extra_cap_usd" => "0.244600000000"))
    accepted = prepare_round
    lease = start_round(accepted)
    assert_equal BigDecimal("1"), execution(accepted).reserved_usd
    configure_preflight
    body = completed(accepted, lease)
    assert_success(send_op(accepted, "complete", body), "complete_response")
    assert_equal BigDecimal("0.245030000000"), execution(accepted).cost_usd
  end

  test "uso sem identidade válida conserva a reserva conservadora inteira e pausa o piloto" do
    configure_bounded
    outbox = prepare_round
    lease = start_round(outbox)
    body = completed(outbox, lease)
    [nil, usage.except("provider_response_id"), usage.merge("input_tokens" => 1_050_001),
     usage.merge("output_tokens" => 128_001)].each do |invalid|
      assert_equal [422, { "error" => "invalid_body" }], send_op(outbox, "complete", body.merge("usage" => invalid))
    end
    assert_success(send_op(outbox, "unknown", lease.merge("reason" => "usage_invalid")), "unknown_response")
    assert_nil execution(outbox).cost_usd
    assert_equal BigDecimal("0.7554"), execution(outbox).reserved_usd
    assert_equal BigDecimal("0"), Pilot::Pilot.find(1).spent_usd
    blocked = prepare_round
    assert_equal [409, { "error" => "pilot_paused" }], send_op(blocked, "claim", claim_body(blocked))
  end

  test "o mesmo dono recupera a reserva sem prorrogação, e start concorrente despacha uma vez" do
    outbox = prepare_round
    body = claim_body(outbox)
    reservation = assert_success(send_op(outbox, "claim", body), "claim_response")
    assert_equal "0.020000000000", reservation.fetch("reserved_usd")
    assert_equal reservation, assert_success(send_op(outbox, "claim", body), "claim_response")
    assert_equal [409, { "error" => "busy" }], send_op(outbox, "claim", claim_body(outbox))
    lease = body.slice("owner_id").merge(reservation.slice("lease_token"))

    worker = -> { send_op(outbox, "start", lease) }
    responses = after_lock(Pilot::Pilot.find(1), worker, worker)
    assert_equal [false, true], responses.map { |result| assert_success(result, "start_response").fetch("dispatch") }.sort_by(&:to_s)
    assert_equal 1, Pilot::Pilot.find(1).dispatch_count
    assert_equal({ "state" => "started", "dispatch" => false }, assert_success(send_op(outbox, "claim", claim_body(outbox)), "claim_response"))
  end

  test "duas transações HTTP disputam de fato o último saldo e só uma pode despachar" do
    contend_for_last(spent: "0.980000000000", prior_dispatches: 8)
    assert_equal BigDecimal("1"), Pilot::Pilot.find(1).spent_usd
    assert_equal 9, Pilot::Pilot.find(1).dispatch_count
  end

  test "duas transações HTTP disputam de fato a última autorização mesmo com saldo remanescente" do
    contend_for_last(spent: "0", prior_dispatches: 23)
    assert_equal BigDecimal("0.020000000000"), Pilot::Pilot.find(1).spent_usd
    assert_equal 24, Pilot::Pilot.find(1).dispatch_count
  end

  test "expiração de reserved libera e cerca o dono anterior sem gastar despacho" do
    travel_to(Time.current) do
      outbox = prepare_round
      old = reserve(outbox)
      travel 11.seconds
      new_lease = reserve(outbox)
      refute_equal old.fetch("lease_token"), new_lease.fetch("lease_token")
      assert_equal [409, { "error" => "lease_lost" }], send_op(outbox, "start", old)
      assert_equal 0, Pilot::Pilot.find(1).dispatch_count
      assert_equal true, assert_success(send_op(outbox, "start", new_lease), "start_response").fetch("dispatch")
    end
  end

  test "sweeper da entrega expira started e mantém pausa durável após reconectar" do
    travel_to(Time.current) do
      outbox = prepare_round
      lease = start_round(outbox)
      travel 41.seconds
      # Nenhum envio elegível. O loop usa run_once e ainda assim recupera a posse abandonada.
      delivery = AgentIntegration::DeliverOutbox.new(url: "http://127.0.0.1.invalid", secret: "unused")
      refute delivery.run_once
      ActiveRecord::Base.connection_pool.disconnect!

      assert_equal "unknown", execution(outbox).state
      assert_equal BigDecimal("0.02"), execution(outbox).reserved_usd
      assert_equal 1, Pilot::Pilot.find(1).dispatch_count
      assert_equal BigDecimal("0"), Pilot::Pilot.find(1).spent_usd
      assert_failure(outbox, "dispatch_uncertain")
      assert_equal [409, { "error" => "lease_lost" }], send_op(outbox, "complete", completed(outbox, lease))
      next_outbox = prepare_round
      assert_equal [409, { "error" => "pilot_paused" }], send_op(next_outbox, "claim", claim_body(next_outbox))
      assert_failure(next_outbox, "pilot_paused")
      assert_equal({ "state" => "unknown" }, assert_success(send_op(outbox, "claim", claim_body(outbox)), "claim_response"))
    end
  end

  test "limita a posse a cinco segundos antes do prazo da rodada" do
    travel_to(Time.current) do
      outbox = prepare_round
      turn = outbox.agent_turn
      turn.update!(result_due_at: 8.seconds.from_now)
      body = claim_body(outbox)
      held = assert_success(send_op(outbox, "claim", body), "claim_response")
      expected = 3.seconds.from_now
      assert_equal expected, Time.iso8601(held.fetch("lease_expires_at"))
      dispatch = assert_success(send_op(outbox, "start", body.slice("owner_id").merge(held.slice("lease_token"))), "start_response")
      assert_equal expected, Time.iso8601(dispatch.fetch("lease_expires_at"))

      too_late = prepare_round
      too_late.agent_turn.update!(result_due_at: 5.seconds.from_now)
      assert_equal [409, { "error" => "turn_stale" }], send_op(too_late, "claim", claim_body(too_late))
    end
  end

  test "valida uso inteiro e teto antes de conciliar e só o dono marca unknown" do
    outbox = prepare_round
    lease = start_round(outbox)
    body = completed(outbox, lease)
    [{ "input_tokens" => 1001 }, { "output_tokens" => 501 }, { "cached_input_tokens" => 501 },
     { "output_tokens" => 1.0 }, { "provider_response_id" => "\0" }].each do |bad_usage|
      request = body.merge("usage" => body.fetch("usage").merge(bad_usage))
      assert_equal [422, { "error" => "invalid_body" }], send_op(outbox, "complete", request)
    end
    assert_equal "started", execution(outbox).state
    assert_equal [409, { "error" => "lease_lost" }],
                 send_op(outbox, "unknown", lease.merge("owner_id" => SecureRandom.uuid, "reason" => "usage_invalid"))
    assert_equal({ "state" => "unknown" }, assert_success(send_op(outbox, "unknown", lease.merge("reason" => "usage_invalid")), "unknown_response"))
    assert_failure(outbox, "usage_invalid")
    assert_equal BigDecimal("0"), Pilot::Pilot.find(1).spent_usd
  end

  test "concilia o cache, mantém bytes imutáveis e aceita ACK repetido sem token" do
    outbox = prepare_round
    lease = start_round(outbox)
    body = completed(outbox, lease)
    expected = { "state" => "result_saved" }.merge(body.slice("result_b64", "result_sha256"))
    assert_equal expected, assert_success(send_op(outbox, "complete", body), "complete_response")
    assert_equal BigDecimal("0.0061"), Pilot::Pilot.find(1).spent_usd
    assert_equal Base64.strict_decode64(expected.fetch("result_b64")), execution(outbox).result_bytes

    # Novos pedidos dependem da configuração atual. Replay usa somente o snapshot persistido.
    ENV.delete("CLOUDWALK_E01_PREFLIGHT_PATH")
    ActiveRecord::Base.connection_pool.disconnect!
    assert_equal expected, assert_success(send_op(outbox, "claim", claim_body(outbox)), "claim_response")
    ack = body.slice("result_sha256")
    assert_equal [409, { "error" => "result_mismatch" }], send_op(outbox, "published", ack.merge("result_sha256" => "0" * 64))
    2.times { assert_equal({ "state" => "published" }, assert_success(send_op(outbox, "published", ack), "published_response")) }
    assert_equal({ "state" => "published" }, assert_success(send_op(outbox, "claim", claim_body(outbox)), "claim_response"))
    assert_equal expected, assert_success(send_op(outbox, "complete", body), "complete_response")
    assert_equal [409, { "error" => "result_mismatch" }], send_op(outbox, "complete", JSON.generate(body) + "\n")
    assert_equal BigDecimal("0.0061"), Pilot::Pilot.find(1).spent_usd
  end

  test "um novo processo Rails encontra pausa, reserva e contagem no PostgreSQL" do
    outbox = prepare_round
    lease = start_round(outbox)
    assert_success(send_op(outbox, "unknown", lease.merge("reason" => "dispatch_uncertain")), "unknown_response")

    script = <<~RUBY
      pilot = AgentIntegration::Pilot::Pilot.find(1)
      execution = AgentIntegration::Pilot::Execution.holding_slot.sole
      puts JSON.generate([pilot.dispatch_count, pilot.spent_usd.to_s("F"), execution.state, execution.reserved_usd.to_s("F")])
    RUBY
    stdout, stderr, status = Open3.capture3({ "CLOUDWALK_E01_PREFLIGHT_PATH" => nil }, RbConfig.ruby,
                                          "bin/rails", "runner", script, chdir: Rails.root)
    assert status.success?, stderr
    assert_equal [1, "0.0", "unknown", "0.02"], JSON.parse(stdout)
  end

  test "valida envelope, base64, origem de handoff e metadados privados antes de salvar" do
    outbox = prepare_round
    lease = start_round(outbox)
    body = completed(outbox, lease, "handoff")
    event = JSON.parse(Base64.strict_decode64(body.fetch("result_b64")))
    [
      body.merge("result_sha256" => "0" * 64),
      body.merge("policy_version" => "changed"),
      body.merge("handoff_rule" => nil),
      body.merge(encoded(event.merge("event_id" => SecureRandom.uuid))),
      body.merge(encoded(event.merge("occurred_at" => 1.day.ago.iso8601))),
      body.merge(encoded(event.deep_merge("payload" => { "summary" => "Alterado" }))),
      body.merge(encoded(event.deep_merge("payload" => { "message_ids" => [SecureRandom.uuid] })))
    ].each { |bad| assert_equal [409, { "error" => "result_mismatch" }], send_op(outbox, "complete", bad) }
    assert_equal [422, { "error" => "invalid_body" }], send_op(outbox, "complete", body.merge("result_b64" => "AB=="))
    assert_equal [422, { "error" => "invalid_body" }], send_op(outbox, "complete", body.merge("knowledge_version" => "1.0"))
    assert_equal [422, { "error" => "invalid_body" }], send_op(outbox, "complete", body.merge("handoff_rule" => { "id" => "aurora.test", "reason" => "other" }))
    assert_nil execution(outbox).cost_usd
    assert_equal "result_saved", assert_success(send_op(outbox, "complete", body), "complete_response").fetch("state")
    assert_equal body.fetch("handoff_rule"), execution(outbox).result_metadata.fetch("handoff_rule")
  end

  test "aceita 64 KiB e distingue excesso de tamanho de base64 malformado" do
    outbox = prepare_round
    lease = start_round(outbox)
    body = completed(outbox, lease)
    event_bytes = Base64.strict_decode64(body.fetch("result_b64"))
    at_limit = event_bytes.ljust(65_536, " ")

    [65_537, 65_539].each do |size|
      over_limit = body.merge(encoded_bytes(at_limit.ljust(size, " ")))
      assert_equal [413, { "error" => "too_large" }], send_op(outbox, "complete", over_limit)
      malformed = over_limit.fetch("result_b64").sub(/[A-Za-z0-9+\/]={1,2}\z/, "B==")
      assert_equal [422, { "error" => "invalid_body" }], send_op(outbox, "complete", over_limit.merge("result_b64" => malformed))
    end
    assert_nil execution(outbox).cost_usd

    # Preenche o JSON externo com espaços para atingir também o limite HTTP.
    at_http_limit = JSON.generate(body.merge(encoded_bytes(at_limit))).ljust(128.kilobytes, " ")
    assert_equal [413, { "error" => "too_large" }], send_op(outbox, "complete", at_http_limit + " ")
    saved = assert_success(send_op(outbox, "complete", at_http_limit), "complete_response")
    assert_equal at_limit, Base64.strict_decode64(saved.fetch("result_b64"))
  end

  test "texto com NUL é rejeitado antes da publicação e ainda permite conciliar o uso conhecido" do
    outbox = prepare_round
    lease = start_round(outbox)
    %w[reply resolve handoff].each do |action|
      body = completed(outbox, lease, action)
      event = JSON.parse(Base64.strict_decode64(body.fetch("result_b64")))
      event.fetch("payload")["text"] = "Texto\0inválido"
      assert WebhookV1::Contract.valid?("AgentResult", event)
      assert_equal [409, { "error" => "result_mismatch" }], send_op(outbox, "complete", body.merge(encoded(event)))
    end
    assert_equal ["started", nil, nil], execution(outbox).attributes.values_at("state", "cost_usd", "result_bytes")
    assert_equal BigDecimal("0"), Pilot::Pilot.find(1).spent_usd

    failed = lease.merge("outcome" => "failed", "reason" => "invalid_result", "usage" => usage)
    assert_equal({ "state" => "failed" }, assert_success(send_op(outbox, "complete", failed), "complete_response"))
    assert_equal BigDecimal("0.0061"), Pilot::Pilot.find(1).spent_usd
    assert_failure(outbox, "invalid_result")
  end

  test "falha de decisão com uso conhecido libera reserva e permite supervisão" do
    outbox = prepare_round
    lease = start_round(outbox)
    failed = lease.merge("outcome" => "failed", "reason" => "invalid_decision", "usage" => usage)
    2.times { assert_equal({ "state" => "failed" }, assert_success(send_op(outbox, "complete", failed), "complete_response")) }
    assert_failure(outbox, "invalid_decision")
    assert_equal({ "state" => "failed" }, assert_success(send_op(outbox, "claim", claim_body(outbox)), "claim_response"))
    assert_equal BigDecimal("0.0061"), Pilot::Pilot.find(1).spent_usd
    assert reserve(prepare_round).key?("lease_token")
  end

  test "complete concilia um caso tornado humano por outra transação sem alterá-lo" do
    outbox = prepare_round
    lease = start_round(outbox)
    record = outbox.agent_turn.support_case
    body = completed(outbox, lease, "handoff")
    record_after_transfer = nil
    transfer = -> { send_op(outbox, "complete", body) }
    result = after_lock(@brand, transfer) do
      record.lock!
      record.advance!(**record.handoff_attributes(summary: "Transferência humana", message_ids: record.messages.ids))
      record_after_transfer = record.attributes
    end.sole

    assert_equal({ "state" => "discarded" }, assert_success(result, "complete_response"))
    assert_equal record_after_transfer, record.reload.attributes
    assert_equal body.fetch("handoff_rule"), execution(outbox).result_metadata.fetch("handoff_rule")
    assert_nil execution(outbox).result_bytes
    assert_equal BigDecimal("0.0061"), Pilot::Pilot.find(1).spent_usd
    assert_equal "turn_stale", record.audits.where(event_type: "agent.execution.discarded").sole.reason
  end

  test "complete espera uma revogação real de acesso humano sem inverter travas" do
    outbox = prepare_round
    lease = start_round(outbox)
    @teams = %w[original remaining].map do |suffix|
      team = Operations::Team.create!(code: "#{@brand.code}_#{suffix}", name: suffix)
      link = @brand.brand_teams.create!(team: team)
      @queue.queue_teams.create!(brand: @brand, brand_team: link)
      team
    end
    @supervisor = Operations::User.create!(email: "#{@brand.code}_s@example.test", name: "Supervisor", role: "supervisor")
    Operations::SupervisorBrand.create!(brand: @brand, user: @supervisor)
    @analyst = Operations::User.create!(email: "#{@brand.code}_a@example.test", name: "Analista", role: "analyst",
                                       active_brand: @brand, available: true)
    @teams.first.team_memberships.create!(user: @analyst)
    @human = Operations::Attendant.create!(code: "#{@brand.code}_human", user: @analyst, kind: "human")
    human_case = create_case(status: "human_active", assignee: @human)
    assert Attendances::RevokeQueueAccess.allowed?(@analyst, human_case)

    operation = Operations::Configuration.new(@supervisor)
    revoke = -> { operation.save_queue(@brand.id, @queue.id, {
      "name" => @queue.name, "active" => true, "team_ids" => [@teams.last.id], "expected_version" => @queue.version
    }) }
    finish = -> { send_op(outbox, "complete", completed(outbox, lease)) }
    _, result = after_lock(human_case, revoke, finish)

    assert_equal "result_saved", assert_success(result, "complete_response").fetch("state")
    assert_equal ["waiting_human", nil, "queue_access_revoked"],
                 human_case.reload.attributes.values_at("status", "assignee_id", "blocking_reason")
    assert_equal "ai_active", outbox.agent_turn.support_case.reload.status
  end

  private

  def configure_preflight(overrides = {})
    snapshot = {
      "mode" => "offline_test", "provider" => "feita", "model" => "openai/gpt-5.6-luna",
      "route" => "https://api.feita.ai/gateway/v1/chat/completions", "account_ref" => "synthetic test",
      "policy_version" => "e01-v1", "documented_on" => "2026-01-01", "input_cap" => 1000, "output_cap" => 500,
      "input_rate_usd_per_million" => "10", "cache_rate_usd_per_million" => "1", "output_rate_usd_per_million" => "20",
      "billing_terms" => fixture("billing-terms.json"),
      "evidence" => %w[input_cap output_cap input_rate cache_rate output_rate billing_terms billable_failures].to_h do |field|
        [field, "Test evidence for #{field}"]
      end
    }
    File.write(@file.path, JSON.generate(snapshot.merge(overrides)))
  end

  def configure_bounded(overrides = {})
    evidence = JSON.parse(File.read(@file.path)).fetch("evidence")
    %w[account_tariff_scope billable_usage_coverage per_request_extras].each do |key|
      evidence[key] = "Synthetic test evidence for #{key}"
    end
    configure_preflight({
      "input_cap" => 1_050_000, "output_cap" => 128_000, "input_rate_usd_per_million" => "0.50",
      "cache_rate_usd_per_million" => "0.50", "output_rate_usd_per_million" => "1.80",
      "billing_terms" => fixture("billing-terms-bounded.json"), "evidence" => evidence
    }.merge(overrides))
  end

  def fixture(name)
    paths = [Rails.root.join("../contracts"), Pathname.new("/workspace/contracts")]
    fixture_path = paths.map { |path| path.join("agent-pilot/fixtures", name) }.find(&:file?)
    JSON.parse(fixture_path.read)
  end

  def prepare_round(published: true)
    record = create_case(status: "ai_active", assignee: @ai)
    record.with_lock do
      record.append_message!(type: "customer", author_id: record.channel_conversation_id, source_event_id: SecureRandom.uuid,
                             text: "Onde consulto o comprovante?")
      AgentIntegration::QueueTurn.call(record)
      turn = record.turns.in_flight.sole
      if published
        turn.update!(result_due_at: 60.seconds.from_now)
        turn.outbox.update!(published_at: Time.current)
      end
      turn.outbox
    end
  end

  def create_case(status:, assignee:)
    conversation = Attendances::ChannelConversation.create!(channel: @channel, external_conversation_id: SecureRandom.uuid,
                                                            external_customer_id: "cliente")
    conversation.support_cases.create!(brand: @brand, channel: @channel, queue: @queue, assignee: assignee,
      status: status, category: "pix", category_source: "channel", priority: "basic", priority_source: "channel",
      correlation_id: SecureRandom.uuid)
  end

  def claim_body(outbox)
    { "owner_id" => SecureRandom.uuid, "request_sha256" => Digest::SHA256.hexdigest(outbox.body) }
  end

  def path(outbox, operation)
    "/internal/v1/e01/executions/#{outbox.event_id}/#{operation}"
  end

  def headers(path, bytes, nonce: SecureRandom.uuid, timestamp: Time.current.to_i.to_s)
    message = "#{timestamp}\n#{nonce}\nPOST\n#{path}\n".b + bytes.b
    {
      "Content-Type" => "application/json", "X-E01-Timestamp" => timestamp, "X-E01-Nonce" => nonce,
      "X-E01-Signature" => OpenSSL::HMAC.hexdigest("SHA256", SECRET, message)
    }
  end

  def send_op(outbox, operation, body, nonce: SecureRandom.uuid)
    route = path(outbox, operation)
    bytes = body.is_a?(String) ? body.dup : JSON.generate(body)
    client = ActionDispatch::Integration::Session.new(Rails.application)
    client.post(route, params: bytes, headers: headers(route, bytes, nonce: nonce))
    [client.response.status, JSON.parse(client.response.body)]
  end

  def assert_http(expected)
    assert_equal expected, [response.status, JSON.parse(response.body)]
  end

  def assert_success(result, definition)
    status, body = result
    assert_equal 200, status, body.inspect
    assert Pilot::Contract.valid?(definition, body), "Resposta fora de #{definition}: #{body.inspect}"
    body
  end

  def reserve(outbox, body = claim_body(outbox))
    reservation = assert_success(send_op(outbox, "claim", body), "claim_response")
    body.slice("owner_id").merge(reservation.slice("lease_token"))
  end

  def start_round(outbox)
    reserve(outbox).tap do |lease|
      assert_equal true, assert_success(send_op(outbox, "start", lease), "start_response").fetch("dispatch")
    end
  end

  def execution(outbox)
    Pilot::Execution.find_by!(request_event_id: outbox.event_id)
  end

  def usage
    { "provider_response_id" => "fake-response", "input_tokens" => 500, "cached_input_tokens" => 100, "output_tokens" => 100 }
  end

  def completed(outbox, lease, action = "reply")
    request = JSON.parse(outbox.body)
    payload = { "request_event_id" => outbox.event_id, "text" => "Resposta sintética." }
    rule = nil
    if action == "handoff"
      history = request.dig("payload", "history")
      payload.merge!("summary" => history.map { |message| message.fetch("text") }.join("\n"),
                     "message_ids" => history.map { |message| message.fetch("id") })
      rule = { "id" => "aurora.human_requested", "reason" => "human_requested" }
    end
    event = request.merge("schema_version" => "1.0", "event_type" => "agent.#{action}.proposed", "payload" => payload,
      "event_id" => Digest::UUID.uuid_v5(Digest::UUID::URL_NAMESPACE, "cloudwalk:e01-luna-v1:#{outbox.event_id}"))
    lease.merge("outcome" => "result", "knowledge_version" => "1.0.0", "ontology_version" => "1.0.0",
                "policy_version" => "e01-v1", "source_refs" => [{ "id" => "aurora.manual", "version" => "1.0.0" }],
                "handoff_rule" => rule, "usage" => usage).merge(encoded(event))
  end

  def encoded(event)
    encoded_bytes(JSON.generate(event))
  end

  def encoded_bytes(bytes)
    { "result_b64" => Base64.strict_encode64(bytes), "result_sha256" => Digest::SHA256.hexdigest(bytes) }
  end

  def assert_failure(outbox, reason)
    turn = outbox.agent_turn.reload
    assert turn.completed_at
    assert_equal ["failed", "e01_#{reason}"], turn.support_case.reload.attributes.values_at("integration_status", "blocking_reason")
    assert_equal reason, turn.support_case.audits.where(event_type: "agent.execution.failed").sole.reason
  end

  def contend_for_last(spent:, prior_dispatches:, final_usage: usage.merge("input_tokens" => 1000, "output_tokens" => 500,
                                                                           "cached_input_tokens" => 0))
    pilot = Pilot::Pilot.create!(id: 1, spent_usd: spent, dispatch_count: prior_dispatches)
    outboxes = [prepare_round, prepare_round]
    contenders = outboxes.map do |outbox|
      lambda do
        body = claim_body(outbox)
        status, reserved = send_op(outbox, "claim", body)
        next [outbox, nil, [status, reserved]] unless status == 200

        lease = body.slice("owner_id").merge(reserved.slice("lease_token"))
        [outbox, lease, send_op(outbox, "start", lease)]
      end
    end
    first, second = after_lock(pilot, *contenders)
    winner, loser = [first, second].sort_by { |_, _, result| result.first }
    assert_equal true, assert_success(winner.last, "start_response").fetch("dispatch")
    assert_equal [409, { "error" => "busy" }], loser.last
    outbox, lease = winner
    last = completed(outbox, lease).merge("usage" => final_usage)
    assert_success(send_op(outbox, "complete", last), "complete_response")
    assert_equal [409, { "error" => "budget_exhausted" }], send_op(loser.first, "claim", claim_body(loser.first))
    assert_failure(loser.first, "budget_exhausted")
    assert_equal 1, Pilot::Execution.count
  end

  def after_lock(record, *operations)
    ready = Queue.new
    workers = []
    record.with_lock do
      raw_connection = ActiveRecord::Base.lease_connection.raw_connection
      blocker = raw_connection.backend_pid
      operations.each do |operation|
        workers << Thread.new do
          ActiveRecord::Base.connection_pool.with_connection do |connection|
            ready << connection.raw_connection.backend_pid
            operation.call
          end
        end
        pid = Timeout.timeout(5) { ready.pop }
        Timeout.timeout(5) do
          query = "SELECT 1 WHERE $1::integer = ANY(pg_blocking_pids($2::integer))"
          sleep 0.01 until raw_connection.exec_params(query, [blocker, pid]).ntuples == 1
        end
        blocker = pid
      end
      yield if block_given?
    end
    Timeout.timeout(10) { workers.map(&:value) }
  ensure
    workers&.each { |thread| thread.join(2) }
  end
end
