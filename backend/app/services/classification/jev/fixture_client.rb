module Classification
  module Jev
    class FixtureClient
      attr_reader :model

      # Recebe respostas no formato Choice do System One, por ID de pergunta.
      def initialize(answers:, model: "jev-fixture")
        @answers = answers
        @model = model
      end

      def mode
        :fixture
      end

      def call(state:, questions:)
        { "model" => model, "answers" => @answers.slice(*questions.keys) }
      end
    end
  end
end
