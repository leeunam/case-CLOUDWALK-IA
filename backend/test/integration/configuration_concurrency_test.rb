require "test_helper"
require "timeout"

class ConfigurationConcurrencyTest < ActiveSupport::TestCase
  self.use_transactional_tests = false

  setup do
    code = "f06_#{SecureRandom.hex(6)}"
    @brand = Operations::Brand.create!(code: code, name: code)
    @queue = @brand.support_queues.create!(code: code, name: "Destino", is_default: true)
    @supervisor = Operations::User.create!(email: "#{code}@example.test", name: code, role: "supervisor")
    Operations::SupervisorBrand.create!(brand: @brand, user: @supervisor)
    @data = { "queue_id" => @queue.id, "position" => 1, "priority" => "basic", "category" => nil, "active" => true }
    @rule = Operations::Configuration.new(@supervisor).save_rule(@brand.id, nil, @data)
  end

  teardown do
    Operations::ConfigurationAudit.where(brand: @brand).delete_all
    Operations::RoutingRule.where(brand: @brand).delete_all
    Operations::SupervisorBrand.where(user: @supervisor).delete_all
    @supervisor&.destroy!
    @queue&.destroy!
    @brand&.destroy!
  end

  test "duas publicações da mesma versão não perdem atualizações" do
    ready = Queue.new
    start = Queue.new
    threads = [5, 10].map do |position|
      Thread.new do
        ActiveRecord::Base.connection_pool.with_connection do
          ready << true
          start.pop
          data = @data.merge("position" => position, "expected_version" => 1)
          Operations::Configuration.new(@supervisor).save_rule(@brand.id, @rule.fetch(:id), data)
          200
        rescue WebhookV1::Error => error
          error.status
        end
      end
    end
    Timeout.timeout(5) { 2.times { ready.pop } }
    2.times { start << true }
    assert_equal [200, 409], Timeout.timeout(10) { threads.map(&:value).sort }
    rule = Operations::RoutingRule.find(@rule.fetch(:id))
    assert_equal 2, rule.version
    events = Operations::ConfigurationAudit.where(brand: @brand, resource_type: "routing_rule")
    assert_equal [1, 2], events.order(:version).pluck(:version)
    assert_equal rule.position, events.find_by!(version: 2).after.fetch("position")
  ensure
    2.times { start << true } if start
    threads&.each(&:join)
  end
end
