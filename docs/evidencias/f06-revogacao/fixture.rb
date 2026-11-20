require "json"
require "securerandom"

raise "O ensaio usa o banco de desenvolvimento da pilha de integração" unless Rails.env.development?
result = ApplicationRecord.transaction do
  marker = "f06_revogacao_#{SecureRandom.hex(6)}"
  brand = Operations::Brand.find_by!(code: "aurora")
  channel = brand.channels.find_by!(kind: "chat", active: true)
  bia = Operations::User.find_by!(email: "bia@example.test", role: "analyst")
  supervisor = Operations::User.find_by!(email: "supervisor@example.test", role: "supervisor")
  Operations::SupervisorBrand.find_by!(user: supervisor, brand: brand)
  %w[pix payouts].each { |code| brand.categories.find_by!(code: code, active: true) }

  queue = brand.support_queues.create!(code: marker, name: marker, active: true, is_default: false)
  grant, retained = %w[bia retida].map do |suffix|
    team = Operations::Team.create!(code: "#{marker}_#{suffix}", name: "#{marker}_#{suffix}")
    link = brand.brand_teams.create!(team: team)
    queue.queue_teams.create!(brand: brand, brand_team: link)
    team
  end
  grant.team_memberships.create!(user: bia)
  conversation = Attendances::ChannelConversation.create!(channel: channel,
    external_conversation_id: marker, external_customer_id: marker)
  record = conversation.support_cases.create!(brand: brand, channel: channel, queue: queue, status: "ai_active",
    assignee: Operations::Attendant.find_by!(kind: "ai", code: "mock"), category: "pix", category_source: "channel",
    priority: "basic", priority_source: "channel", correlation_id: SecureRandom.uuid)
  {
    marker: marker, case_id: record.id, brand_id: brand.id, queue_id: queue.id, queue_name: queue.name,
    queue_version: queue.version, team_bia: grant.id, team_retained: retained.id,
    bia_id: bia.id, supervisor_id: supervisor.id
  }
end
File.write("/tmp/cloudwalk-f06-admin-fixture.json", JSON.generate(result))
