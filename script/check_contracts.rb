# frozen_string_literal: true

require "json"
require "pathname"
require "yaml"
require "json_schemer"
require_relative "../contracts/classification-http/check_fixtures"

contracts = Pathname.new(__dir__).join("../contracts").realpath
api_path = contracts.join("openapi.yaml")
schema_path = contracts.join("schemas/v1.json")
api = YAML.safe_load_file(api_path)
schema = JSON.parse(schema_path.read)
documents = { api_path => api, schema_path => schema }

def check_refs(node, current_file, documents)
  case node
  when Hash
    if (ref = node["$ref"])
      file, pointer = ref.split("#", 2)
      target_file = file.empty? ? current_file : current_file.dirname.join(file).cleanpath
      target = documents.fetch(target_file) { abort "#{current_file.basename}: arquivo fora do contrato em #{ref}" }
      unless pointer.nil? || pointer.empty?
        abort "#{current_file.basename}: JSON Pointer inválido em #{ref}" unless pointer.start_with?("/")
        pointer[1..].split("/", -1).each do |segment|
          key = segment.gsub("~1", "/").gsub("~0", "~")
          key = Integer(key, 10) if target.is_a?(Array)
          target = target.fetch(key)
        end
      end
    end
    node.each_value { |value| check_refs(value, current_file, documents) }
  when Array
    node.each { |value| check_refs(value, current_file, documents) }
  end
rescue KeyError, IndexError, ArgumentError, NoMethodError
  abort "#{current_file.basename}: referência sem destino em #{ref}"
end

def report_errors(errors, label)
  errors.each { |error| warn "#{label} #{error.fetch('data_pointer')}: #{error.fetch('error')}" }
  abort "Contrato inválido em #{label}" unless errors.empty?
end

def check_scenario(condition, description)
  abort "Cenário de fixtures inválido: #{description}" unless condition
end

def check_simulator(example)
  receipt = example.call("simulator-accepted")
  recovered = example.call("simulator-recovered-case")
  list = example.call("simulator-recovered-list").fetch("items")
  followup = example.call("simulator-followup")
  followup_receipt = example.call("simulator-followup-accepted")
  conversation = %w[channel_id external_conversation_id]

  check_scenario(recovered.fetch("id") == receipt.fetch("case_id") && list.include?(recovered),
                 "o detalhe recuperado precisa pertencer à mesma conversa da listagem e do recibo inicial")
  check_scenario(recovered.slice(*conversation) == receipt.slice(*conversation),
                 "recarregar precisa preservar o canal da rota e a identidade externa da conversa")
  check_scenario(followup.fetch("external_conversation_id") == recovered.fetch("external_conversation_id"),
                 "a solicitação de continuação deve manter o ID externo recuperado")
  check_scenario(followup_receipt == receipt,
                 "a continuação precisa confirmar o mesmo caso, correlação e conversa")
end

def check_analyst_controls(example)
  session = example.call("analyst-session")
  user = session.fetch("user")
  own_case = example.call("case-human-owned")
  coworker_case = example.call("case-human-coworker")
  scope = example.call("case-filters")
  analysts = example.call("analyst-list").fetch("items")
  profile = example.call("capacity-profile")

  [own_case, coworker_case].each do |item|
    check_scenario(item.values_at("status", "brand_id") == ["human_active", session.dig("operation", "active_brand_id")] &&
                   item.dig("assignee", "type") == "human",
                   "os dois casos usados para comparar controles precisam estar ativos na marca em operação")
  end

  brand_ids = scope.fetch("brands").map { |brand| brand.fetch("id") }
  queues_per_brand = scope.fetch("queues").map { |queue| queue.values_at("id", "brand_id") }
  visible_cases = example.call("case-list").fetch("items") + [own_case, coworker_case]
  visible_cases.each do |item|
    check_scenario(brand_ids.include?(item.fetch("brand_id")) &&
                   queues_per_brand.include?(item.values_at("queue_id", "brand_id")),
                   "os filtros precisam identificar a marca e a fila dos casos visíveis")
  end

  attendant_id = user.fetch("attendant_id")
  check_scenario(user.fetch("id") != attendant_id && own_case.dig("assignee", "id") == attendant_id &&
                 coworker_case.dig("assignee", "id") != attendant_id,
                 "os controles usam a identidade do atendente para distinguir o responsável do colega")
  directory_user = analysts.find { |analyst| analyst.fetch("user_id") == user.fetch("id") }
  check_scenario(directory_user&.values_at("attendant_id", "name") == user.values_at("attendant_id", "name") &&
                 analysts.any? { |analyst| analyst.fetch("attendant_id") == coworker_case.dig("assignee", "id") } &&
                 profile.fetch("analyst_id") == user.fetch("id"),
                 "a lista de analistas precisa ligar os responsáveis ao ID de usuário usado ao editar o perfil")
end

def check_configuration_audit(example)
  supervisor = example.call("supervisor-session").fetch("user")
  rule = example.call("routing-rule-brand")
  latest, creation = example.call("configuration-audit").fetch("items")
  check_scenario(latest && creation, "a auditoria precisa mostrar a criação e a edição da regra")

  [latest, creation].each do |event|
    check_scenario(supervisor.fetch("brand_ids").include?(event.fetch("brand_id")) &&
                   event.fetch("actor").values_at("type", "id") == supervisor.values_at("role", "id"),
                   "a auditoria precisa identificar o supervisor autorizado na marca da alteração")
    snapshot = event.fetch("after")
    check_scenario(event.fetch("resource_type") == "routing_rule" &&
                   event.values_at("resource_id", "brand_id") == rule.values_at("id", "brand_id") &&
                   snapshot.values_at("id", "brand_id", "version") == event.values_at("resource_id", "brand_id", "version"),
                   "a auditoria precisa identificar o recurso da marca e a versão publicada")
  end

  check_scenario(creation.fetch("before").nil? && creation.fetch("after") == rule &&
                 latest.fetch("before") == creation.fetch("after") &&
                 latest.fetch("version") == creation.fetch("version") + 1 &&
                 latest.dig("before", "priority") != latest.dig("after", "priority"),
                 "a edição precisa partir da regra criada, avançar a versão e registrar a alteração de prioridade")
end

documents.each { |file, data| check_refs(data, file, documents) }
report_errors(JSONSchemer.openapi(api).validate.to_a, api_path.basename)
report_errors(JSONSchemer.validate_schema(schema).to_a, schema_path.basename)

validator = JSONSchemer.schema(schema_path, format: true)
fixtures = contracts.glob("fixtures/*.json").sort
abort "Nenhuma fixture encontrada" if fixtures.empty?

invalid_examples = 0
examples = {}
fixtures.each do |file|
  fixture = JSON.parse(file.read)
  reference = fixture.fetch("schema")
  match = %r{\A\.\./schemas/v1\.json(#/\$defs/[A-Za-z][A-Za-z0-9]*)\z}.match(reference)
  abort "#{file.basename}: declaração de schema inválida" unless match
  pointer = match[1]
  check_refs({ "$ref" => pointer }, schema_path, documents)

  expected_valid = fixture.fetch("valid", true)
  abort "#{file.basename}: valid deve ser booleano" unless [true, false].include?(expected_valid)

  data = fixture.fetch("data")
  errors = validator.ref(pointer).validate(data).to_a
  if expected_valid
    report_errors(errors, file.basename)
    examples[file.basename(".json").to_s] = data
  else
    abort "#{file.basename}: exemplo inválido foi aceito" if errors.empty?
    invalid_examples += 1
  end
end

example = ->(name) { examples.fetch(name) { abort "Fixture obrigatória para os cenários: #{name}.json" } }
check_simulator(example)
check_analyst_controls(example)
check_configuration_audit(example)
check_scenario(api.dig("info", "version") == "1.1.0", "versão REST staff")
mixed_case = example.call("case-setfit-mixed")
check_scenario(!validator.ref("#/$defs/Case").valid?(mixed_case) &&
               validator.ref("#/$defs/CaseV11").valid?(example.call("case-human-owned")),
               "leitura histórica e discriminação das origens por campo")
check_scenario(!validator.ref("#/$defs/AgentTurnRequestedV10").valid?(example.call("agent-setfit-request")) &&
               validator.ref("#/$defs/AgentTurnRequestedV11").valid?(example.call("agent-setfit-request")),
               "versões Kafka da origem SetFit")
ClassificationHttpFixtures.new(contracts.join("classification-http")).check
puts "Contrato HTTP privado, pins, vetor Ruby, respostas R1 e recusas por status verificados."

puts "OpenAPI 3.1, JSON Schema 2020-12 e #{fixtures.size} fixtures verificados (#{invalid_examples} inválidas esperadas)."
puts "Cenários de retomada do simulador, controles do analista e auditoria de configuração verificados."
