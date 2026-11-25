require "test_helper"
require "timeout"

class HumanAssignmentConcurrencyTest < ActiveSupport::TestCase
  self.use_transactional_tests = false

  setup do
    code = "f03_#{SecureRandom.hex(6)}"
    @brand = Operations::Brand.create!(code: code, name: code)
    @team = Operations::Team.create!(code: code, name: code)
    @brand_team = Operations::BrandTeam.create!(brand: @brand, team: @team)
    @queue = Operations::SupportQueue.create!(brand: @brand, code: "test", name: "Fila de teste", is_default: true)
    Operations::QueueTeam.create!(brand: @brand, support_queue: @queue, brand_team: @brand_team)
    @channel = Operations::Channel.create!(brand: @brand, name: "Chat de teste", kind: "chat")
    @user = Operations::User.create!(email: "#{code}@example.test", name: code, role: "analyst",
                                    active_brand: @brand, available: true)
    Operations::TeamMembership.create!(user: @user, team: @team)
    @attendant = Operations::Attendant.create!(code: code, kind: "human", user: @user)
    @user.capacity_profiles.create!(version: 1, portfolio_limit: 2,
                                    alternatives: [[{ priority: "basic", category: "pix", limit: 2 }]])
  end

  teardown do
    if @brand
      cases = Attendances::SupportCase.where(brand: @brand)
      Attendances::CaseAudit.where(support_case: cases).delete_all
      cases.delete_all
      Attendances::ChannelConversation.where(channel: @channel).delete_all
    end
    @attendant&.destroy!
    if @user
      Operations::CapacityProfile.where(user: @user).delete_all
      Operations::TeamMembership.where(user: @user).delete_all
      @user.destroy!
    end
    Operations::QueueTeam.where(brand: @brand).delete_all if @brand
    @queue&.destroy!
    @channel&.destroy!
    @brand_team&.destroy!
    @team&.destroy!
    @brand&.destroy!
  end

  test "duas atribuições concorrentes disputam a última vaga do mesmo analista" do
    create_case("human_active", assignee: @attendant)
    first = create_case("waiting_human", queued_at: 2.minutes.ago)
    second = create_case("waiting_human", queued_at: 1.minute.ago)
    ready = Queue.new
    threads = []

    @user.with_lock do
      [first, second].each do |record|
        threads << Thread.new do
          ActiveRecord::Base.connection_pool.with_connection do |connection|
            ready << connection.select_value("SELECT pg_backend_pid()").to_i
            # Cada transação tenta um caso diferente, com o mesmo protocolo da distribuição.
            Attendances::DistributeHumanWork.new(@brand.id).assign_pending(record.id)
          end
        end
      end
      pids = Timeout.timeout(5) { 2.times.map { ready.pop } }
      Timeout.timeout(5) do
        loop do
          connection = ActiveRecord::Base.lease_connection
          connection.execute("SELECT pg_stat_clear_snapshot()")
          waiting = connection.select_value(<<~SQL).to_i
            SELECT count(*) FROM pg_stat_activity
              WHERE pid IN (#{pids.join(",")}) AND wait_event_type = 'Lock'
          SQL
          break if waiting == 2

          sleep 0.01
        end
      end
    end
    threads.each(&:value)

    contenders = [first.reload, second.reload]
    assert_equal %w[human_active waiting_human], contenders.map(&:status).sort
    assert_equal 2, Attendances::HumanEligibility.portfolio(@attendant).count
    assert_equal 1, Attendances::CaseAudit.where(support_case: contenders, event_type: "case.human.assigned").count
    assert_equal "portfolio_limit", contenders.find { |record| record.status == "waiting_human" }.blocking_reason
  ensure
    threads&.each(&:join)
  end

  private

  def create_case(status, assignee: nil, queued_at: nil)
    conversation = Attendances::ChannelConversation.create!(channel: @channel, external_conversation_id: SecureRandom.uuid,
                                                            external_customer_id: "cliente")
    conversation.support_cases.create!(brand: @brand, channel: @channel, queue: @queue, status: status, assignee: assignee,
                                       priority: "basic", priority_source: "channel", category: "pix", category_source: "channel",
                                       correlation_id: SecureRandom.uuid, human_queue_since: queued_at)
  end
end
