require "minitest/autorun"
require_relative "samples"

class JevClassifierTest < Minitest::Test
  include JevSamples

  class RecordingFixture < Classification::Jev::FixtureClient
    attr_reader :calls

    def initialize(**options)
      super
      @calls = []
    end

    def call(state:, questions:)
      @calls << { state: state, questions: questions }
      super
    end
  end

  def setup
    @input = channel_input("channel-entry")
    @fixture = RecordingFixture.new(answers: {
      "category" => choice(:category, "pix"),
      "priority" => choice(:priority, "basic")
    })
  end

  def test_valid_channel_classification_needs_no_call
    result = classifier(@fixture).call(**@input)

    assert_equal :complete, result.status
    assert_equal({ category: "pix", priority: "basic", category_source: "channel", priority_source: "channel" },
                 result.classification)
    assert_empty @fixture.calls
    assert_nil result.evidence
  end

  def test_missing_category_preserves_priority_and_uses_brand_options
    categories = { "pix" => CATEGORIES.fetch("pix") }
    @fixture = RecordingFixture.new(answers: {
      "category" => choice(:category, "pix").merge("probabilities" => { "pix" => 0.95, abstention => 0.05 }),
      "priority" => choice(:priority, "urgent")
    })
    result = classifier(@fixture, categories: categories).call(text: @input.fetch(:text), priority: "basic")

    assert_equal :complete, result.status
    assert_equal "jev", result.classification.fetch(:category_source)
    assert_equal "basic", result.classification.fetch(:priority)
    assert_equal "channel", result.classification.fetch(:priority_source)
    call = @fixture.calls.fetch(0)
    assert_equal @input.fetch(:text), call.fetch(:state)
    assert_equal ["category"], call.fetch(:questions).keys
    question = call.fetch(:questions).fetch("category")
    assert_equal "choice", question.fetch(:type)
    assert_equal ["pix", abstention], question.fetch(:criteria).keys
    assert_equal [:category], result.evidence.fetch(:answers).keys
  end

  def test_missing_priority_preserves_category
    result = classifier(@fixture).call(**@input.merge(priority: ""))

    assert_equal :complete, result.status
    assert_equal({ category: "pix", priority: "basic", category_source: "channel", priority_source: "jev" },
                 result.classification)
    assert_equal ["priority"], @fixture.calls.fetch(0).fetch(:questions).keys
  end

  def test_contract_fixture_with_two_missing_fields_uses_one_request_and_records_evidence
    result = classifier(@fixture).call(**channel_input("channel-missing-fields"))

    assert_equal :complete, result.status
    assert_equal 1, @fixture.calls.length
    assert_equal %w[category priority], @fixture.calls.fetch(0).fetch(:questions).keys
    assert_equal({ category: "pix", priority: "basic", category_source: "jev", priority_source: "jev" },
                 result.classification)
    assert_equal :fixture, result.evidence.fetch(:mode)
    assert_equal "jev-fixture", result.evidence.fetch(:requested_model)
    assert_equal "jev-fixture", result.evidence.fetch(:model)
    assert_operator result.evidence.fetch(:latency_ms), :>=, 0
    assert_equal 1.0, result.evidence.dig(:answers, :category, :confidence)
    assert_equal 1.0, result.evidence.dig(:answers, :priority, :probabilities, "basic")
  end

  def test_invalid_channel_fields_and_types_do_not_call_provider
    result = classifier(@fixture).call(**channel_input("channel-invalid-classification"))

    assert_equal :review, result.status
    assert_equal({ category: :invalid_input, priority: :invalid_input }, result.issues)
    assert result.classification.values.all?(&:nil?)

    [false, 3, {}, [], "   ", "PIX"].each do |value|
      result = classifier(@fixture).call(text: @input.fetch(:text), category: value, priority: nil)
      assert_equal({ category: :invalid_input }, result.issues)
    end
    assert_empty @fixture.calls
  end

  def test_invalid_field_preserves_other_valid_input
    result = classifier(@fixture).call(**@input.merge(priority: "unknown"))

    assert_equal({ priority: :invalid_input }, result.issues)
    assert_equal "pix", result.classification.fetch(:category)
    assert_equal "channel", result.classification.fetch(:category_source)
    assert_empty @fixture.calls
  end

  def test_empty_brand_catalog_requires_review_without_calling_provider
    result = classifier(@fixture, categories: {}).call(text: @input.fetch(:text))

    assert_equal :review, result.status
    assert_equal({ category: :catalog_unavailable }, result.issues)
    assert_empty @fixture.calls
  end

  def test_reserved_abstention_cannot_be_an_operational_category
    assert_raises(ArgumentError) { classifier(@fixture, categories: { abstention => "Rótulo reservado" }) }
  end

  def test_abstention_leaves_both_missing_fields_unapplied_and_keeps_model_evidence
    fixture = RecordingFixture.new(answers: {
      "category" => choice(:category, "pix"),
      "priority" => choice(:priority, abstention)
    })
    result = classifier(fixture).call(text: @input.fetch(:text))

    assert_equal :review, result.status
    assert_equal({ priority: :insufficient_information }, result.issues)
    assert result.classification.values.all?(&:nil?)
    assert_equal "pix", result.evidence.dig(:answers, :category, :choice)
    assert_equal abstention, result.evidence.dig(:answers, :priority, :choice)
    assert_equal 1.0, result.evidence.dig(:answers, :priority, :probabilities, abstention)
    refute result.retryable
  end

  def test_low_confidence_is_recorded_without_a_calibration_threshold
    probabilities = { "pix" => 0.27, "payouts" => 0.25, "terminal" => 0.24, abstention => 0.24 }
    answer = choice(:category, "pix", confidence: 0.03).merge("probabilities" => probabilities)
    fixture = RecordingFixture.new(answers: { "category" => answer })
    result = classifier(fixture).call(**@input.merge(category: nil))

    assert_equal :complete, result.status
    assert_equal 0.03, result.evidence.dig(:answers, :category, :confidence)
    assert_equal 0.27, result.evidence.dig(:answers, :category, :probabilities, "pix")
    assert_equal "pix", result.classification.fetch(:category)
  end

  def test_available_confidence_is_kept_for_an_incomplete_response
    answer = { "type" => "choice", "choice" => "pix", "confidence" => 0.36 }
    result = classifier(RecordingFixture.new(answers: { "category" => answer })).call(**@input.merge(category: nil))

    assert_equal :review, result.status
    assert_equal({ category: :invalid_response }, result.issues)
    assert_nil result.classification.fetch(:category)
    assert_equal({ choice: "pix", confidence: 0.36 }, result.evidence.dig(:answers, :category))
  end

  def test_invalid_or_missing_choice_preserves_valid_channel_input
    valid = choice(:category, "pix")
    [
      nil, "pix", valid.merge("type" => "noul"), valid.merge("choice" => "another_brand"),
      valid.merge("choice" => "terminal"), valid.merge("confidence" => 1.5),
      valid.merge("confidence" => Float::NAN),
      valid.merge("probabilities" => valid.fetch("probabilities").merge("terminal" => Float::INFINITY)),
      valid.merge("probabilities" => { "pix" => 1.0 }),
      valid.merge("probabilities" => valid.fetch("probabilities").merge("terminal" => 0.5))
    ].each do |answer|
      fixture = RecordingFixture.new(answers: answer.nil? ? {} : { "category" => answer })
      result = classifier(fixture).call(**@input.merge(category: nil))

      assert_equal :review, result.status, answer.inspect
      assert_equal({ category: :invalid_response }, result.issues)
      assert_nil result.classification.fetch(:category)
      assert_equal "basic", result.classification.fetch(:priority)
      assert_equal "channel", result.classification.fetch(:priority_source)
    end
  end

  private

  def abstention
    Classification::Jev::Classifier::ABSTENTION
  end
end
