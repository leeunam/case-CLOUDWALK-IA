module Classification
  module ConfiguredProvider
    JEV_MODES = %w[fixture http disabled].freeze

    def self.selection
      case ENV.fetch("CLASSIFICATION_PROVIDER", "jev")
      when "setfit" then { provider: "setfit", provider_mode: "http" }
      when "jev"
        mode = ENV.fetch("CLOUDWALK_JEV_MODE", "disabled")
        { provider: "jev", provider_mode: JEV_MODES.include?(mode) ? mode : "invalid" }
      else { provider: "unknown", provider_mode: nil }
      end
    end

    # Pedidos anteriores à migração só podiam ter evidência do Jev.
    def self.pin_legacy!(request)
      return if request.provider

      modes = request.attempts.pluck(:evidence).filter_map { |evidence| evidence["mode"] }.uniq
      config = if modes.one? && JEV_MODES.include?(modes.first)
        { provider: "jev", provider_mode: modes.first }
      else
        { provider: "unknown", provider_mode: nil }
      end
      request.update!(config)
    end

    def self.call(attempt, text)
      snapshot = attempt.snapshot
      case snapshot.fetch("provider")
      when "setfit"
        SetfitClient.new.call(id: attempt.id, snapshot: snapshot, text: text)
      when "jev"
        ConfiguredJev.call(mode: snapshot.fetch("provider_mode"), categories: snapshot.dig("catalog", "category"),
                           text: text, **snapshot.fetch("received").symbolize_keys)
      else Result.review(:invalid_classifier_mode)
      end
    end
  end
end
