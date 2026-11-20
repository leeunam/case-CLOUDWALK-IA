require_relative "dataset"
require_relative "../../../backend/app/services/classification/jev/http_client"

module F08Jev
  # Observa a chamada efetiva. Perguntas vêm do adaptador, não dos rótulos.
  class ObservedClient
    attr_reader :requests

    def initialize(client)
      @client = client
      @requests = []
    end

    def model = @client.model
    def mode = @client.mode

    def call(state:, questions:)
      @requests << questions.keys
      @client.call(state: state, questions: questions)
    end
  end

  class Evaluation
    TRANSPORT_ERRORS = %i[http_error network_error timeout].freeze

    def initialize(catalog:, mode:)
      @catalog = catalog
      @mode = mode
    end

    def observe(entry, client)
      observed = ObservedClient.new(client)
      classifier = Classification::Jev::Classifier.new(
        client: observed, categories: @catalog.fetch("category"), priorities: @catalog.fetch("priority")
      )
      received = entry.fetch("received")
      result = classifier.call(text: entry.fetch("text"), **received.transform_keys(&:to_sym))
      evidence = result.evidence || {}
      provider_issue = result.issues[:provider]
      fields = entry.fetch("expected").to_h do |field, expected|
        key = field.to_sym
        answer = evidence.dig(:answers, key) || {}
        issue = result.issues[key]
        raw_status = raw_status(answer, issue, provider_issue)
        applied = result.classification[key] if result.classification[:"#{key}_source"] == "jev"
        [field, { expected: expected, observed_choice: answer[:choice], raw_status: raw_status, applied: applied }]
      end
      provided = received.filter_map do |field, value|
        next unless @catalog.fetch(field).key?(value)

        key = field.to_sym
        [field, result.classification[key] == value && result.classification[:"#{key}_source"] == "channel"]
      end.to_h

      {
        id: entry.fetch("id"), stratum: entry["stratum"], missing: entry.fetch("missing"), fields: fields,
        channel_preservation: provided, status: result.status, issues: result.issues,
        outcome: outcome(fields, result), request_count: observed.requests.size,
        questions: observed.requests.flatten, model: evidence[:model], http_status: evidence[:http_status],
        provider_latency_ms: (@mode == "live" ? evidence[:latency_ms] : nil)
      }
    end

    def summarize(rows)
      {
        by_field: FIELDS.to_h { |field| [field, field_metrics(rows.filter_map { |row| row.fetch(:fields)[field] })] },
        urgent_priority: urgent_metrics(rows),
        cases: {
          total: rows.size, automatic: rate(rows.count { |row| row[:status] == :complete }, rows.size),
          review: rows.count { |row| row[:status] == :review }, outcomes: rows.map { |row| row[:outcome] }.tally
        },
        channel_fields_preserved: rate(rows.sum { |row| row.fetch(:channel_preservation).values.count(true) },
                                       rows.sum { |row| row.fetch(:channel_preservation).size }),
        requests: rows.sum { |row| row.fetch(:request_count) },
        questions: rows.sum { |row| row.fetch(:questions).size },
        returned_models: rows.filter_map { |row| row[:model] }.uniq.sort,
        provider_latency_ms: latency(rows),
        provider_cost: { status: @mode == "live" ? "unavailable" : "not_measured", amount: nil, currency: nil }
      }
    end

    private

    def raw_status(answer, issue, provider_issue)
      return :transport_failure if TRANSPORT_ERRORS.include?(provider_issue)
      return :invalid_response if issue == :invalid_response || (answer.empty? && provider_issue == :invalid_response)
      return :abstention if issue == :insufficient_information
      return :choice if answer.key?(:choice)

      :unavailable
    end

    def outcome(fields, result)
      return :complete if result.status == :complete
      return :transport_failure if TRANSPORT_ERRORS.include?(result.issues[:provider])
      return :invalid_response if result.issues.value?(:invalid_response)
      return :abstention if fields.values.any? { |field| field[:raw_status] == :abstention }

      :other_review
    end

    def field_metrics(fields)
      labeled, abstention_targets = fields.partition { |field| field[:expected] != ABSTENTION }
      applied = fields.reject { |field| field[:applied].nil? }
      choices = labeled.select { |field| field[:raw_status] == :choice }
      correct = choices.count { |field| field[:observed_choice] == field[:expected] }
      applied_matches = labeled.count { |field| field[:applied] == field[:expected] }
      {
        missing: fields.size, labeled: labeled.size, expected_abstentions: abstention_targets.size,
        raw_accuracy: rate(correct, labeled.size),
        raw_accuracy_given_choice: rate(correct, choices.size),
        applied_accuracy: rate(applied_matches, labeled.size),
        automatic_coverage: rate(applied.size, fields.size),
        coverage_blocked_after_choice: fields.count { |field| field[:raw_status] == :choice && field[:applied].nil? },
        abstentions: rate(fields.count { |field| field[:raw_status] == :abstention }, fields.size),
        correct_abstentions: rate(abstention_targets.count { |field| field[:raw_status] == :abstention },
                                  abstention_targets.size),
        undue_abstentions: rate(labeled.count { |field| field[:raw_status] == :abstention }, labeled.size),
        automatic_on_expected_abstention: rate(abstention_targets.count { |field| field[:applied] },
                                               abstention_targets.size),
        invalid_responses: rate(fields.count { |field| field[:raw_status] == :invalid_response }, fields.size),
        transport_failures: rate(fields.count { |field| field[:raw_status] == :transport_failure }, fields.size),
        unavailable: rate(fields.count { |field| field[:raw_status] == :unavailable }, fields.size)
      }
    end

    def urgent_metrics(rows)
      urgent = rows.select { |row| row.dig(:fields, "priority", :expected) == "urgent" }
      outcomes = urgent.map do |row|
        case row.dig(:fields, "priority", :applied)
        when "urgent" then :automatic_urgent
        when nil
          if %i[transport_failure invalid_response].include?(row[:outcome])
            row[:outcome]
          else
            :abstention_or_review
          end
        else :automatic_non_urgent
        end
      end.tally
      %i[automatic_urgent automatic_non_urgent abstention_or_review invalid_response transport_failure].to_h do |key|
        [key, rate(outcomes.fetch(key, 0), urgent.size)]
      end
    end

    def latency(rows)
      values = rows.filter_map { |row| row[:provider_latency_ms] }.sort
      return { samples: 0, p50: nil, p95: nil } if values.empty?

      { samples: values.size, p50: values.fetch((values.size * 0.50).ceil - 1),
        p95: values.fetch((values.size * 0.95).ceil - 1) }
    end

    def rate(count, denominator)
      { count: count, denominator: denominator, fraction: denominator.positive? ? count.fdiv(denominator) : nil }
    end
  end
end
