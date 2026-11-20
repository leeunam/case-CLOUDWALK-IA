require "test_helper"
require "timeout"

class ConfigurationDomainRacesTest < ActiveSupport::TestCase
  self.use_transactional_tests = false

  setup do
    @code = "f06_race_#{SecureRandom.hex(6)}"
    @brand = Operations::Brand.create!(code: @code, name: @code)
    @queue = @brand.support_queues.create!(code: "original", name: "Fila original", is_default: true)
    @channel = @brand.channels.create!(kind: "chat", name: "Chat")
    @brand.categories.create!(code: "pix", name: "Pix")
    @supervisor = Operations::User.create!(email: "#{@code}_supervisor@example.test", role: "supervisor", name: "Supervisão")
    Operations::SupervisorBrand.create!(user: @supervisor, brand: @brand)
    @configuration = Operations::Configuration.new(@supervisor)
  end

  teardown do
    next unless @brand

    cases = Attendances::SupportCase.where(brand: @brand)
    turns = AgentIntegration::AgentTurn.where(support_case: cases)
    AgentIntegration::AgentOutbox.where(agent_turn: turns).delete_all
    turns.delete_all
    Attendances::CaseCommandReceipt.where(support_case: cases).delete_all
    Attendances::CaseAudit.where(support_case: cases).delete_all
    Attendances::CaseMessage.where(support_case: cases).delete_all
    Attendances::ChannelEntry.where(support_case: cases).delete_all
    cases.delete_all
    Attendances::ChannelConversation.where(channel: @channel).delete_all
    @created_ai&.destroy!
    Operations::ConfigurationAudit.where(brand: @brand).delete_all
    Operations::RoutingRule.where(brand: @brand).delete_all
    Operations::SupervisorBrand.where(brand: @brand).delete_all
    @supervisor&.destroy!
    @attendant&.destroy!
    if @analyst
      Operations::CapacityProfile.where(user: @analyst).delete_all
      Operations::TeamMembership.where(user: @analyst).delete_all
      Operations::AnalystOperationAudit.where(user: @analyst).delete_all
      @analyst.destroy!
    end
    Operations::QueueTeam.where(brand: @brand).delete_all
    Operations::BrandTeam.where(brand: @brand).delete_all
    Operations::Team.where(code: ["#{@code}_original", "#{@code}_retida"]).delete_all
    Operations::SupportQueue.where(brand: @brand).delete_all
    Operations::Channel.where(brand: @brand).delete_all
    Operations::Category.where(brand: @brand).delete_all
    @brand.destroy!
  end

  test "revogar equipe da fila durante a última atribuição mantém acesso e histórico consistentes" do
    original = queue_team("original")
    retained = queue_team("retida")
    @analyst = Operations::User.create!(email: "#{@code}_analyst@example.test", name: "Analista", role: "analyst",
                                       active_brand: @brand, available: true)
    original.team_memberships.create!(user: @analyst)
    @attendant = Operations::Attendant.create!(code: @code, user: @analyst, kind: "human")
    @analyst.capacity_profiles.create!(version: 1, portfolio_limit: 2,
      alternatives: [[{ priority: "basic", category: "pix", limit: 1 }]])
    waiting = create_human_case("waiting_customer", assignee: @attendant)
    contender = create_human_case("waiting_human")

    distribute = -> { Attendances::DistributeHumanWork.new(@brand.id).call }
    revoke = lambda do
      @configuration.save_queue(@brand.id, @queue.id, {
        "name" => @queue.name, "active" => true, "team_ids" => [retained.id], "expected_version" => 1
      })
    end
    race_behind(@analyst, distribute, revoke)

    assert_equal ["waiting_human", nil, "queue_access_revoked", 3],
      contender.reload.attributes.values_at("status", "assignee_id", "blocking_reason", "assignment_generation")
    assert_equal ["waiting_customer", nil, nil], waiting.reload.attributes.values_at("status", "assignee_id", "human_queue_since")
    assert_equal [@queue.id, @queue.id], [contender.queue_id, waiting.queue_id]
    assert_empty Attendances::HumanEligibility.portfolio(@attendant)
    refute Attendances::RevokeQueueAccess.allowed?(@analyst, contender)

    assigned = contender.audits.find_by!(event_type: "case.human.assigned")
    assert_equal [@attendant.id, @queue.id, 1], assigned.details.values_at("assignee_id", "queue_id", "profile_version")
    [contender, waiting].each do |record|
      revoked = record.audits.where(event_type: "case.human.unassigned").sole
      assert_equal "queue_access_revoked", revoked.reason
      assert_equal [@attendant.id, @queue.id], revoked.details.values_at("previous_assignee_id", "queue_id")
    end
    change = Operations::ConfigurationAudit.find_by!(brand: @brand, resource_type: "queue", resource_id: @queue.id)
    assert_equal [original.id, retained.id].sort, change.before.fetch("team_ids")
    assert_equal [2, [retained.id]], [change.version, change.after.fetch("team_ids")]
  end

  test "correção inicial concorrente espera a publicação e registra a fila e a versão da regra vencedora" do
    @created_ai = Operations::Attendant.create!(code: "mock", kind: "ai") unless Operations::Attendant.exists?(code: "mock")
    destination = @brand.support_queues.create!(code: "destino", name: "Fila de destino")
    rule_data = { "queue_id" => @queue.id, "category" => "pix", "priority" => "basic", "active" => true }
    current = @configuration.save_rule(@brand.id, nil, rule_data.merge("position" => 10))
    successor = @configuration.save_rule(@brand.id, nil, rule_data.merge("position" => 20))
    successor_record = Operations::RoutingRule.find(successor.fetch(:id))
    existing_case = receive("pix")
    review = receive("categoria_invalida")
    assert_equal "classification_review", review.status

    publish = lambda do
      @configuration.save_rule(@brand.id, successor_record.id, rule_data.merge(
        "position" => 5, "queue_id" => destination.id, "expected_version" => 1
      ))
    end
    correct = lambda do
      Attendances::ApplyCaseCommand.new(user: @supervisor, case_id: review.id, operation: "classification",
        key: SecureRandom.uuid, data: { "expected_version" => review.version, "category" => "pix",
          "priority" => "basic", "reason" => "Categoria confirmada" }).call
    end
    race_behind(successor_record, publish, correct)

    assert_routing existing_case.reload, @queue, current.fetch(:id), 1
    assert_equal "ai_active", review.reload.status
    assert_equal 1, review.turns.count
    assert_routing review, destination, successor_record.id, 2
    assert_routing receive("pix"), destination, successor_record.id, 2

    change = Operations::ConfigurationAudit.find_by!(brand: @brand, resource_type: "routing_rule",
                                                     resource_id: successor_record.id, version: 2)
    assert_equal [20, @queue.id, 1], change.before.values_at("position", "queue_id", "version")
    assert_equal [5, destination.id, 2], change.after.values_at("position", "queue_id", "version")
  end

  private

  def queue_team(suffix)
    team = Operations::Team.create!(code: "#{@code}_#{suffix}", name: suffix)
    link = @brand.brand_teams.create!(team: team)
    @queue.queue_teams.create!(brand: @brand, brand_team: link)
    team
  end

  def create_human_case(status, assignee: nil)
    conversation = Attendances::ChannelConversation.create!(channel: @channel, external_conversation_id: SecureRandom.uuid,
                                                            external_customer_id: "cliente")
    conversation.support_cases.create!(brand: @brand, channel: @channel, queue: @queue, status: status, assignee: assignee,
      category: "pix", category_source: "channel", priority: "basic", priority_source: "channel",
      correlation_id: SecureRandom.uuid, human_queue_since: (Time.current if status == "waiting_human"))
  end

  def receive(category)
    data = { "external_customer_id" => SecureRandom.uuid, "external_conversation_id" => SecureRandom.uuid,
      "source_event_id" => SecureRandom.uuid, "category" => category, "priority" => "basic", "text" => "Dúvida de Pix" }
    receipt = Attendances::ReceiveChannelMessage.new(@channel, data, JSON.generate(data)).call
    Attendances::SupportCase.find(receipt.fetch(:case_id))
  end

  def assert_routing(record, queue, rule_id, version)
    event = record.audits.where(event_type: "case.routing.applied").sole
    assert_equal [queue.id, queue.id, rule_id, version], [record.queue_id, *event.details.values_at("queue_id", "rule_id", "rule_version")]
  end

  def race_behind(held_record, first, second)
    ready = Queue.new
    workers = []
    held_record.with_lock do
      connection = ActiveRecord::Base.lease_connection
      blocker = connection.select_value("SELECT pg_backend_pid()").to_i
      [first, second].each do |operation|
        workers << Thread.new do
          ActiveRecord::Base.connection_pool.with_connection do |worker_connection|
            ready << worker_connection.select_value("SELECT pg_backend_pid()").to_i
            operation.call
          end
        end
        pid = Timeout.timeout(5) { ready.pop }
        Timeout.timeout(5) do
          until connection.select_value("SELECT #{blocker} = ANY(pg_blocking_pids(#{pid}))")
            sleep 0.01
          end
        end
        blocker = pid
      end
    end
    Timeout.timeout(10) { workers.each(&:value) }
  ensure
    workers&.each(&:join)
  end
end
