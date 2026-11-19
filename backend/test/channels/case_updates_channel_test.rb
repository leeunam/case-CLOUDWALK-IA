require "test_helper"

class CaseUpdatesChannelTest < ActionCable::Channel::TestCase
  setup do
    Rails.application.load_seed
    @brand = Operations::Brand.find_by!(code: "aurora")
    @channel = @brand.channels.find_by!(kind: "chat")
    @owner = BrowserAccess::Session.create!(audience: "simulator", expires_at: 1.hour.from_now)
    @supervisor = Operations::User.find_by!(email: "supervisor@example.test")
    @staff = BrowserAccess::Session.create!(audience: "staff", user: @supervisor, expires_at: 1.hour.from_now)
    receipt = BrowserAccess::SendSimulatorMessage.new(identity: @owner, channel_id: @channel.id,
      key: "test-cable", data: { "text" => "Dúvida", "category" => "pix", "priority" => "basic" }).call
    @case_id = receipt.fetch(:case_id)
    @payload = { "type" => "case.updated", "case_id" => @case_id }
  end

  test "simulador recebe somente o aviso da própria conversa enquanto a sessão for vigente" do
    browser_cookie(simulator_session_id: @owner.id)
    subscribe case_id: @case_id, audience: "simulator"
    assert subscription.confirmed?
    assert_has_stream CaseUpdatesChannel.stream_name(@case_id)
    subscription.send(:forward_update, @payload)
    assert_equal [@payload], transmissions

    @owner.revoke!
    subscription.send(:forward_update, @payload)
    assert_equal [@payload], transmissions
    assert_no_streams
  end

  test "staff deixa de receber após revogação de acesso à marca" do
    browser_cookie(staff_session_id: @staff.id)
    subscribe case_id: @case_id, audience: "staff"
    assert subscription.confirmed?
    subscription.send(:forward_update, @payload)
    assert_equal [@payload], transmissions

    Operations::SupervisorBrand.find_by!(user: @supervisor, brand: @brand).destroy!
    subscription.send(:forward_update, @payload)
    assert_equal [@payload], transmissions
    assert_no_streams
  end

  test "audiência declarada não troca o papel da sessão" do
    browser_cookie(simulator_session_id: @owner.id)
    subscribe case_id: @case_id, audience: "staff"
    assert subscription.rejected?
  end

  test "outro cliente não assina a conversa nem mesmo conhecendo o UUID" do
    other = BrowserAccess::Session.create!(audience: "simulator", expires_at: 1.hour.from_now)
    browser_cookie(simulator_session_id: other.id)
    subscribe case_id: @case_id, audience: "simulator"
    assert subscription.rejected?
  end

  test "sessão expirada perde acesso antes do próximo aviso" do
    browser_cookie(simulator_session_id: @owner.id)
    subscribe case_id: @case_id, audience: "simulator"
    assert subscription.confirmed?
    @owner.update!(expires_at: 1.second.ago)
    subscription.send(:forward_update, @payload)
    assert_empty transmissions
    assert_no_streams
  end

  test "rollback não publica aviso" do
    stream = CaseUpdatesChannel.stream_name(@case_id)
    assert_no_broadcasts(stream) do
      Attendances::SupportCase.transaction(requires_new: true) do
        Attendances::SupportCase.find(@case_id).advance!
        raise ActiveRecord::Rollback
      end
    end
  end

  private

  def browser_cookie(**cookie)
    stub_connection
    connection.define_singleton_method(:browser_identity) do |audience|
      BrowserAccess::Session.resolve(cookie, audience)
    end
  end
end
