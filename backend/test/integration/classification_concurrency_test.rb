require "test_helper"
require "timeout"

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
