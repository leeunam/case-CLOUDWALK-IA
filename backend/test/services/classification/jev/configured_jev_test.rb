require "minitest/autorun"
require_relative "samples"
require_relative "../../../../app/services/classification/jev/demo_fixture"
require_relative "../../../../app/services/classification/catalog"
require_relative "../../../../app/services/classification/configured_jev"

class ConfiguredJevTest < Minitest::Test
  include JevSamples

  def setup
    @original_mode = ENV["CLOUDWALK_JEV_MODE"]
    @original_key = ENV["TYPESAFE_API_KEY"]
    ENV.delete("TYPESAFE_API_KEY")
  end

  def teardown
    ENV["CLOUDWALK_JEV_MODE"] = @original_mode
    ENV["TYPESAFE_API_KEY"] = @original_key
  end

  def test_fixture_complements_only_the_missing_field_without_a_key
    ENV["CLOUDWALK_JEV_MODE"] = "fixture"
    result = classify("Qual é o prazo para confirmar um Pix?", priority: "urgent")

    assert_equal :complete, result.status
    assert_equal ["pix", "urgent", "channel"], result.classification.values_at(:category, :priority, :priority_source)
    assert_equal :fixture, result.evidence.fetch(:mode)
    assert_equal [:category], result.evidence.fetch(:answers).keys
  end

  def test_fixture_uses_abstention_and_never_guesses_unknown_demo_values
    ENV["CLOUDWALK_JEV_MODE"] = "fixture"
    result = classify("Olá.", priority: "basic")

    assert_equal :review, result.status
    assert_equal({ category: :insufficient_information }, result.issues)
    assert_equal "informacao_insuficiente", result.evidence.dig(:answers, :category, :choice)
  end

  def test_modes_require_explicit_selection
    ENV.delete("CLOUDWALK_JEV_MODE")
    assert_equal({ provider: :classifier_disabled }, classify("Pix").issues)

    ENV["CLOUDWALK_JEV_MODE"] = "http"
    assert_equal({ provider: :missing_credentials }, classify("Pix").issues)

    ENV["CLOUDWALK_JEV_MODE"] = "fallback"
    assert_equal({ provider: :invalid_classifier_mode }, classify("Pix").issues)
  end

  def test_invalid_catalog_requires_review
    ENV["CLOUDWALK_JEV_MODE"] = "fixture"
    categories = { "informacao_insuficiente" => "Opção reservada" }
    assert_equal({ provider: :invalid_catalog }, classify("Pix", categories: categories).issues)
  end

  private

  def classify(text, categories: CATEGORIES, **input)
    Classification::ConfiguredJev.call(text: text, categories: categories, **input)
  end
end
