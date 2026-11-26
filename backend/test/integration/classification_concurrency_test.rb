require "test_helper"
require "timeout"
require_relative "../support/setfit_endpoint"

class ClassificationConcurrencyTest < ActiveSupport::TestCase
  self.use_transactional_tests = false

  test "worker concorrente e resultado atrasado não duplicam nem sobrescrevem correção" do
    Rails.application.load_seed
    brand = Operations::Brand.find_by!(code: "aurora")
    channel = brand.channels.find_by!(kind: "chat")
    data = { "external_customer_id" => SecureRandom.uuid, "external_conversation_id" => SecureRandom.uuid,
      "source_event_id" => SecureRandom.uuid, "priority" => "basic", "text" => "Qual é o prazo de um Pix?" }
    receipt = Attendances::ReceiveChannelMessage.new(channel, data, JSON.generate(data)).call
    record = Attendances::SupportCase.find(receipt.fetch(:case_id))
    request = Classification::Request.find_by!(support_case: record)
    started = Queue.new
    resumed = Queue.new
    classifier = lambda do |categories:, **input|
      started << true
      Timeout.timeout(5) { resumed.pop }
      Classification::Jev::Classifier.new(client: Classification::Jev::DemoFixture.new,
        categories: categories, priorities: Classification::Catalog::PRIORITIES).call(**input)
    end

    worker = Thread.new do
      ActiveRecord::Base.connection_pool.with_connection do
        Classification::CompleteRequest.new(request.id, classifier: classifier).call
      end
    end
    Timeout.timeout(5) { started.pop }
    Classification::CompleteRequest.new(request.id, classifier: ->(**) { flunk "tentativa duplicada" }).call
    supervisor = Operations::User.find_by!(email: "supervisor@example.test")
    Attendances::ApplyCaseCommand.new(user: supervisor, case_id: record.id, operation: "classification",
      key: "classification-race", data: { "expected_version" => record.version, "category" => "terminal",
      "priority" => "urgent", "reason" => "Corrigido durante a classificação" }).call
    invalidated = request.attempts.sole
    assert_equal "discarded", invalidated.disposition
    assert invalidated.finished_at
    assert_empty invalidated.evidence
    resumed << true
    worker.value

    assert_equal %w[terminal urgent], record.reload.classification.values_at(:category, :priority)
    assert_equal 1, record.turns.count
    assert_equal 2, record.classification_version
    attempt = request.attempts.sole
    assert_equal "discarded", attempt.disposition
    assert_equal invalidated.finished_at, attempt.finished_at
    assert_equal "supervisor_correction", attempt.issues.fetch("provider")
    assert_equal "pix", attempt.evidence.dig("answers", "category", "choice")
  ensure
    resumed << true if resumed && worker&.alive?
    worker&.join
    clean_case(record, request)
  end

  test "SetFit liquida sob o catálogo, campos, correção e lease atuais depois do retorno HTTP" do
    Rails.application.load_seed
    brand = Operations::Brand.find_by!(code: "aurora")
    channel = brand.channels.find_by!(kind: "chat")
    previous_provider, previous_url = ENV.values_at("CLASSIFICATION_PROVIDER", "SETFIT_URL")
    endpoint = SetfitEndpoint.new
    ENV.update("CLASSIFICATION_PROVIDER" => "setfit", "SETFIT_URL" => endpoint.url)
    %i[version hash channel lease correction].each do |change|
      in_flight = Queue.new
      release = Queue.new
      endpoint.reply = lambda do |http_request|
        in_flight << true
        Timeout.timeout(5) { release.pop }
        endpoint.complete(http_request)
      end
      data = { "external_customer_id" => SecureRandom.uuid, "external_conversation_id" => SecureRandom.uuid,
        "source_event_id" => SecureRandom.uuid, "category" => "pix", "text" => "Mensagem sintética para a prioridade." }
      receipt = Attendances::ReceiveChannelMessage.new(channel, data, JSON.generate(data)).call
      record = Attendances::SupportCase.find(receipt.fetch(:case_id))
      request = Classification::Request.find_by!(support_case: record)
      worker = Thread.new do
        ActiveRecord::Base.connection_pool.with_connection { Classification::CompleteRequestJob.perform_now(request.id) }
      end
      Timeout.timeout(4) { in_flight.pop }
      attempt = request.attempts.sole
      version = brand.reload.catalog_version
      case change
      when :version
        brand.with_lock { brand.update!(catalog_version: version + 1) }
      when :hash
        extra = brand.categories.create!(code: "test_c06b", name: "Alteração em voo")
      when :channel
        record.with_lock { record.update!(category: "payouts") }
      when :correction
        supervisor = Operations::User.find_by!(email: "supervisor@example.test")
        Attendances::ApplyCaseCommand.new(user: supervisor, case_id: record.id, operation: "classification",
          key: "setfit-race", data: { "expected_version" => record.version, "category" => "terminal",
            "priority" => "basic", "reason" => "Correto após verificação" }).call
      end
      finish = -> { release << true; Timeout.timeout(5) { worker.value } }
      if change == :lease
        travel_to(attempt.lease_expires_at + 1.second) { finish.call }
      else
        finish.call
      end

      assert_equal "discarded", attempt.reload.disposition
      assert_equal "urgent", attempt.evidence.dig("fields", "priority", "raw")
      assert_equal version, attempt.snapshot.fetch("catalog_version")
      assert_equal "pix", attempt.snapshot.dig("received", "category")
      assert request.reload.completed_at
      if change == :correction
        assert_equal "supervisor_correction", attempt.issues.fetch("provider")
        assert_equal %w[terminal basic supervisor supervisor], record.reload.classification.values_at(:category, :priority, :category_source, :priority_source)
        assert_equal 1, AgentIntegration::AgentOutbox.where(agent_turn: record.turns).count
      else
        assert_equal "classification_review", record.reload.status
        reason = { version: "catalog_changed", hash: "catalog_changed", channel: "invalid_input", lease: "worker_lease_expired" }.fetch(change)
        assert_equal reason, record.blocking_reason
        assert_nil record.priority
        assert_empty record.turns
        assert_equal attempt.id, record.audits.find_by!(event_type: "case.classification.review").details["attempt_id"]
      end
    ensure
      release << true if release && worker&.alive?
      worker&.join
      extra&.destroy!
      brand.update!(catalog_version: version) if change == :version && version
      clean_case(record, request)
    end
    assert_equal 5, endpoint.requests.size
  ensure
    endpoint&.close
    ENV.update("CLASSIFICATION_PROVIDER" => previous_provider, "SETFIT_URL" => previous_url)
  end

  private

  def clean_case(record, request)
    if record
      if request
        Classification::Attempt.where(classification_request_id: request.id).delete_all
        request.destroy!
      end
      AgentIntegration::AgentOutbox.where(agent_turn_id: record.turns.ids).delete_all
      AgentIntegration::AgentTurn.where(support_case: record).delete_all
      Attendances::CaseCommandReceipt.where(support_case: record).delete_all
      Attendances::CaseAudit.where(support_case: record).delete_all
      Attendances::CaseMessage.where(support_case: record).delete_all
      Attendances::ChannelEntry.where(support_case: record).delete_all
      conversation = record.channel_conversation
      record.destroy!
      conversation.destroy!
    end
  end
end
