module Classification
  module Jev
    class Classifier
      Result = Data.define(:status, :classification, :issues, :evidence, :retryable, :retry_after_seconds)

      ABSTENTION = "informacao_insuficiente"
      ABSTENTION_DESCRIPTION = "O relato não permite escolher com segurança entre as demais opções."
      PRIORITY_CODES = %w[basic intermediate advanced urgent].freeze
      INSTRUCTIONS = {
        category: "Qual é o assunto principal do atendimento relatado?",
        priority: "Que urgência o atendimento exige, considerando o impacto e a necessidade de ação imediata?"
      }.freeze
      PROBABILITY_TOLERANCE = 0.01

      # Catálogos ativos e já filtrados pelo chamador, em mapas de código para descrição.
      def initialize(client:, categories:, priorities:)
        priorities = validate_catalog(priorities)
        unknown_priorities = priorities.keys - PRIORITY_CODES
        if unknown_priorities.any?
          raise ArgumentError, "prioridades fora do contrato v1: #{unknown_priorities.join(', ')}"
        end

        @client = client
        @catalogs = { category: validate_catalog(categories), priority: priorities }
      end

      def call(text:, category: nil, priority: nil)
        input = { category: category, priority: priority }
        classification = {}
        issues = {}
        missing = []

        input.each do |field, value|
          set_field(classification, field, nil, nil)
          if value.nil? || value == ""
            missing << field
          elsif value.is_a?(String) && @catalogs.fetch(field).key?(value)
            set_field(classification, field, value, "channel")
          else
            issues[field] = :invalid_input
          end
        end

        return result(classification, issues) if issues.any? || missing.empty?

        missing.each { |field| issues[field] = :catalog_unavailable if @catalogs.fetch(field).empty? }
        return result(classification, issues) if issues.any?

        complete(text, missing, classification)
      end

      private

      def validate_catalog(catalog)
        if catalog.is_a?(Hash) && catalog.size < 255
          valid_options = catalog.all? do |code, description|
            code.is_a?(String) && code.match?(/\A[a-z][a-z0-9_]*\z/) && code != ABSTENTION &&
              description.is_a?(String) && !description.strip.empty?
          end
          return catalog.dup.freeze if valid_options
        end

        raise ArgumentError, "catálogo Choice inválido: use até 254 códigos com descrições e sem a opção reservada"
      end

      def complete(text, missing, classification)
        questions = missing.to_h do |field|
          criteria = @catalogs.fetch(field).merge(ABSTENTION => ABSTENTION_DESCRIPTION)
          [field.to_s, { type: "choice", instructions: INSTRUCTIONS.fetch(field), criteria: criteria }]
        end
        started = Process.clock_gettime(Process::CLOCK_MONOTONIC)
        response = @client.call(state: text, questions: questions)
        evidence = provider_evidence(started)

        model, answers = response.values_at("model", "answers") if response.is_a?(Hash)
        model = model_name(model)
        evidence[:model] = model if model
        issues = {}
        unless evidence.key?(:model) && answers.is_a?(Hash)
          issues[:provider] = :invalid_response
          answers = {} unless answers.is_a?(Hash)
        end

        missing.each do |field|
          options = questions.fetch(field.to_s).fetch(:criteria).keys
          evidence[:answers][field], issue = check_answer(answers[field.to_s], options)
          issues[field] = issue if issue
        end

        if issues.empty?
          missing.each do |field|
            set_field(classification, field, evidence[:answers].fetch(field).fetch(:choice), "jev")
          end
        end

        result(classification, issues, evidence: evidence)
      rescue HttpClient::Error => error
        evidence = provider_evidence(started)
        evidence[:http_status] = error.http_status if error.http_status
        result(classification, { provider: error.reason }, evidence: evidence,
               retryable: error.retryable?, retry_after_seconds: error.retry_after_seconds)
      end

      def check_answer(answer, options)
        return [{}, :invalid_response] unless answer.is_a?(Hash) && answer["type"] == "choice"

        choice, confidence, probabilities = answer.values_at("choice", "confidence", "probabilities")
        observed = {}
        observed[:choice] = choice if options.include?(choice)
        observed[:confidence] = confidence if unit_number?(confidence)
        observed[:probabilities] = probabilities if valid_distribution?(probabilities, options)

        issue = if observed.size != 3 || probabilities.fetch(choice) < probabilities.values.max
          :invalid_response
        elsif choice == ABSTENTION
          :insufficient_information
        end

        [observed, issue]
      end

      def unit_number?(value)
        (value.is_a?(Integer) || value.is_a?(Float)) && value.finite? && value.between?(0, 1)
      end

      def valid_distribution?(values, options)
        values.is_a?(Hash) && values.size == options.size &&
          options.all? { |option| unit_number?(values[option]) } &&
          (values.values.sum - 1).abs <= PROBABILITY_TOLERANCE
      end

      def provider_evidence(started)
        elapsed = Process.clock_gettime(Process::CLOCK_MONOTONIC) - started
        { mode: @client.mode, requested_model: model_name(@client.model), latency_ms: (elapsed * 1000).round, answers: {} }
      end

      def model_name(value)
        return unless value.is_a?(String)

        name = value.encode(Encoding::UTF_8)
        name if name.valid_encoding? && !name.strip.empty?
      rescue EncodingError
        nil
      end

      def set_field(classification, field, value, source)
        classification[field] = value
        classification[:"#{field}_source"] = source
      end

      def result(classification, issues, evidence: nil, retryable: false, retry_after_seconds: nil)
        Result.new(status: issues.empty? ? :complete : :review, classification: classification, issues: issues,
                   evidence: evidence, retryable: retryable, retry_after_seconds: retry_after_seconds)
      end
    end
  end
end
