require_relative "evaluation"
require_relative "../../../backend/app/services/classification/jev/fixture_client"
require_relative "../../../backend/app/services/classification/jev/demo_fixture"

module F08Jev
  class Controls
    def initialize(catalog)
      @catalog = catalog
    end

    def run(evaluation)
      scenarios.map do |id, received, expected, client, status, issues, questions, applied|
        entry = { "id" => id, "text" => "Relato reservado ao controle offline.", "received" => received,
                  "missing" => expected.keys, "expected" => expected }
        row = evaluation.observe(entry, client)
        passed = row[:status] == status && row[:issues] == issues && row[:questions] == questions &&
                 row[:request_count] == (questions.empty? ? 0 : 1) && row[:channel_preservation].values.all? &&
                 row[:fields].transform_values { |field| field[:applied] }.compact == applied
        row.merge(passed: passed)
      end
    end

    def fixture(choices)
      answers = choices.to_h do |field, value|
        options = @catalog.fetch(field).keys + [ABSTENTION]
        [field, { "type" => "choice", "choice" => value, "confidence" => 1.0,
                  "probabilities" => options.to_h { |option| [option, option == value ? 1.0 : 0.0] } }]
      end
      Classification::Jev::FixtureClient.new(answers: answers)
    end

    private

    def scenarios
      category = { "category" => "pix" }
      priority = { "priority" => "basic" }
      [
        ["entrada-completa", category.merge(priority), {}, fixture({}), :complete, {}, [], {}],
        ["entrada-invalida", { "priority" => "fora_catalogo" }, category, fixture(category),
         :review, { priority: :invalid_input }, [], {}],
        ["campo-preservado", priority, category, fixture(category.merge("priority" => "urgent")),
         :complete, {}, ["category"], category],
        ["abstencao-parcial", {}, category.merge("priority" => ABSTENTION),
         fixture(category.merge("priority" => ABSTENTION)),
         :review, { priority: :insufficient_information }, FIELDS, {}],
        ["saida-invalida", priority, category, fixture("category" => "fora_catalogo"), :review,
         { category: :invalid_response }, ["category"], {}],
        ["erro-rede", priority, category, failing_http(SocketError), :review,
         { provider: :network_error }, ["category"], {}],
        ["timeout", priority, category, failing_http(Timeout::Error), :review,
         { provider: :timeout }, ["category"], {}]
      ]
    end

    def failing_http(error)
      Classification::Jev::HttpClient.new(api_key: "controle-offline", connection_factory: ->(*) { raise error })
    end
  end
end
