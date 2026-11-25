brand_definitions = [
  ["11111111-1111-4111-8111-111111111111", "aurora", "Aurora Pagamentos"],
  ["22222222-2222-4222-8222-222222222222", "horizonte", "Horizonte Negócios"]
]

ActiveRecord::Base.transaction do
  brands = brand_definitions.map do |id, code, name|
    Operations::Brand.find_or_create_by!(code: code) do |brand|
      brand.id = id
      brand.name = name
    end
  end

  team_definitions = {
    "shared" => "Suporte compartilhado",
    "aurora_specialists" => "Especialistas Aurora",
    "horizonte_specialists" => "Especialistas Horizonte"
  }
  teams = team_definitions.to_h do |code, name|
    [code, Operations::Team.find_or_create_by!(code: code) { |team| team.name = name }]
  end

  brands.each do |brand|
    authorized_teams = [teams.fetch("shared"), teams.fetch("#{brand.code}_specialists")]
    brand_teams = authorized_teams.map do |team|
      Operations::BrandTeam.find_or_create_by!(brand: brand, team: team)
    end

    %w[general specialist].each do |code|
      queue = Operations::SupportQueue.find_or_create_by!(brand: brand, code: code) do |record|
        record.name = code == "general" ? "Atendimento geral" : "Especialistas"
        record.is_default = code == "general"
      end
      brand_teams.each do |brand_team|
        Operations::QueueTeam.find_or_create_by!(support_queue: queue, brand_team: brand_team) do |link|
          link.brand = brand
        end
      end
    end

    { "chat" => "Chat", "whatsapp" => "WhatsApp simulado", "email" => "E-mail simulado" }.each do |kind, name|
      Operations::Channel.find_or_create_by!(brand: brand, kind: kind) { |channel| channel.name = name }
    end
    { "pix" => "Pix", "payouts" => "Repasses", "terminal" => "Maquininha" }.each do |code, name|
      Operations::Category.find_or_create_by!(brand: brand, code: code) { |category| category.name = name }
    end
  end

  alternatives = [
    [{ priority: "urgent", category: "pix", limit: 1 }],
    [{ priority: "urgent", category: "terminal", limit: 1 }, { priority: "basic", category: "terminal", limit: 1 }],
    [{ priority: "basic", category: "pix", limit: 3 }, { priority: "intermediate", category: "payouts", limit: 1 }],
    [{ priority: "advanced", category: "payouts", limit: 1 }, { priority: "intermediate", category: "payouts", limit: 1 }]
  ]
  %w[basic intermediate advanced urgent].product(%w[pix payouts terminal]).each do |priority, category|
    alternatives << [{ priority: priority, category: category, limit: 1 }]
  end
  alternatives.uniq!

  analyst_definitions = [
    ["Alex", %w[shared aurora_specialists], brands.first],
    ["Bia", %w[aurora_specialists], brands.first],
    ["Cris", %w[shared], brands.last]
  ]
  analyst_definitions.each do |name, team_codes, active_brand|
    user = Operations::User.find_or_create_by!(email: "#{name.downcase()}@example.test") do |record|
      record.name = name
      record.role = "analyst"
      record.active_brand = active_brand
      record.available = true
    end
    team_codes.each do |team_code|
      Operations::TeamMembership.find_or_create_by!(user: user, team: teams.fetch(team_code))
    end
    Operations::Attendant.find_or_create_by!(code: "human_#{name.downcase()}") do |record|
      record.kind = "human"
      record.user = user
    end
    Operations::CapacityProfile.find_or_create_by!(user: user, version: 1) do |profile|
      profile.portfolio_limit = 6
      profile.alternatives = alternatives
    end
  end

  supervisor = Operations::User.find_or_create_by!(email: "supervisor@example.test") do |record|
    record.name = "Supervisão de demonstração"
    record.role = "supervisor"
  end
  brands.each { |brand| Operations::SupervisorBrand.find_or_create_by!(user: supervisor, brand: brand) }
  Operations::Attendant.find_or_create_by!(code: "mock") { |record| record.kind = "ai" }
end

puts "Seed pronto: #{Operations::Brand.count} marcas, #{Operations::SupportQueue.count} filas e #{Operations::User.count} usuários sintéticos."
