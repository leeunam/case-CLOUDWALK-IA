require "json"
require_relative "../../../../app/services/classification/jev/http_client"
require_relative "../../../../app/services/classification/jev/fixture_client"
require_relative "../../../../app/services/classification/jev/classifier"

module JevSamples
  CATEGORIES = {
    "pix" => "Transferências ou pagamentos via Pix, incluindo prazo, estorno e falha.",
    "payouts" => "Repasse ou recebimento de valores das vendas.",
    "terminal" => "Instalação, uso ou falha da maquininha de cartão."
  }.freeze
  PRIORITIES = {
    "basic" => "Orientação de rotina, sem operação prejudicada.",
    "intermediate" => "Impacto moderado que permite continuar a operação.",
    "advanced" => "Impacto relevante sem necessidade de ação imediata.",
    "urgent" => "Problema que exige ação imediata, como operação totalmente interrompida."
  }.freeze

  def classifier(client, categories: CATEGORIES, priorities: PRIORITIES)
    Classification::Jev::Classifier.new(client: client, categories: categories, priorities: priorities)
  end

  def channel_input(fixture)
    roots = [File.expand_path("../../../../../contracts", __dir__), "/workspace/contracts"]
    path = roots.map { |root| File.join(root, "fixtures", "#{fixture}.json") }.find { |file| File.file?(file) }
    raise "Fixture contratual #{fixture}.json não encontrada em #{roots.join(' ou ')}." unless path

    JSON.parse(File.read(path)).fetch("data").slice("text", "category", "priority").transform_keys(&:to_sym)
  end

  def choice(field, value, confidence: 1.0)
    catalog = { category: CATEGORIES, priority: PRIORITIES }.fetch(field)
    options = catalog.keys + [Classification::Jev::Classifier::ABSTENTION]
    { "type" => "choice", "choice" => value, "confidence" => confidence,
      "probabilities" => options.to_h { |option| [option, option == value ? 1.0 : 0.0] } }
  end
end
