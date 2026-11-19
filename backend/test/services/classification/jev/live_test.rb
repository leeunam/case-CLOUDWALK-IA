require "minitest/autorun"
require_relative "samples"

class JevLiveTest < Minitest::Test
  include JevSamples

  def test_complements_missing_category_on_typesafe
    skip "habilite com JEV_LIVE_TEST=1" unless ENV["JEV_LIVE_TEST"] == "1"
    refute_empty ENV["TYPESAFE_API_KEY"].to_s.strip, "carregue TYPESAFE_API_KEY para executar o ensaio real"

    client = Classification::Jev::HttpClient.new
    result = classifier(client).call(
      text: "Quero saber quanto tempo demora para confirmar um pagamento feito por Pix.",
      priority: "basic"
    )

    puts JSON.generate(status: result.status, classification: result.classification, issues: result.issues,
                       evidence: result.evidence)
    assert_equal :complete, result.status
    assert_equal "pix", result.classification.fetch(:category)
    assert_equal "jev", result.classification.fetch(:category_source)
    assert_equal "basic", result.classification.fetch(:priority)
    assert_equal "channel", result.classification.fetch(:priority_source)
    assert_equal [:category], result.evidence.fetch(:answers).keys
  end
end
