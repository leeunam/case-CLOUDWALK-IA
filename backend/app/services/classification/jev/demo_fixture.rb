module Classification
  module Jev
    class DemoFixture < FixtureClient
      def initialize
        super(answers: {})
      end

      def call(state:, questions:)
        choices = {
          "category" => fixture_category(state),
          "priority" => fixture_priority(state)
        }
        answers = questions.to_h do |field, question|
          criteria = question.fetch(:criteria)
          choice = choices[field]
          choice = Classifier::ABSTENTION unless criteria.key?(choice)
          probabilities = criteria.keys.to_h { |option| [option, option == choice ? 1.0 : 0.0] }
          [field, { "type" => "choice", "choice" => choice, "confidence" => 1.0, "probabilities" => probabilities }]
        end
        { "model" => model, "answers" => answers }
      end

      private

      def fixture_category(text)
        return "pix" if /\bpix\b/i.match?(text)
        return "payouts" if /\brepasse/i.match?(text)
        return "terminal" if /maquininha|terminal/i.match?(text)
      end

      def fixture_priority(text)
        return "urgent" if /urgente|totalmente interrompid/i.match?(text)
        return "advanced" if /apagou|fora do ar|não liga|parou/i.match?(text)
        return "intermediate" if /atrasad|impacto moderado/i.match?(text)
        return "basic" if /prazo|como|quanto tempo|orientação/i.match?(text)
      end
    end
  end
end
