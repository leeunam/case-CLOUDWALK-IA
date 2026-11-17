# frozen_string_literal: true

require "json"
require "pathname"
require "yaml"
require "json_schemer"

contracts = Pathname.new(__dir__).join("../docs/contratos").realpath
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

documents.each { |file, data| check_refs(data, file, documents) }
report_errors(JSONSchemer.openapi(api).validate.to_a, api_path.basename)
report_errors(JSONSchemer.validate_schema(schema).to_a, schema_path.basename)

validator = JSONSchemer.schema(schema_path, format: true)
fixtures = contracts.glob("fixtures/*.json").sort
abort "Nenhuma fixture encontrada" if fixtures.empty?

invalid_examples = 0
fixtures.each do |file|
  fixture = JSON.parse(file.read)
  reference = fixture.fetch("schema")
  match = %r{\A\.\./schemas/v1\.json(#/\$defs/[A-Za-z][A-Za-z0-9]*)\z}.match(reference)
  abort "#{file.basename}: declaração de schema inválida" unless match
  pointer = match[1]
  check_refs({ "$ref" => pointer }, schema_path, documents)

  expected_valid = fixture.fetch("valid", true)
  abort "#{file.basename}: valid deve ser booleano" unless [true, false].include?(expected_valid)

  errors = validator.ref(pointer).validate(fixture.fetch("data")).to_a
  if expected_valid
    report_errors(errors, file.basename)
  else
    abort "#{file.basename}: exemplo inválido foi aceito" if errors.empty?
    invalid_examples += 1
  end
end

puts "OpenAPI 3.1, JSON Schema 2020-12 e #{fixtures.size} fixtures verificados (#{invalid_examples} inválidas esperadas)."
