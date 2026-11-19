module Classification
  module ConfiguredJev
    def self.call(categories:, **input)
      client = case ENV.fetch("CLOUDWALK_JEV_MODE", "disabled")
      when "fixture" then Jev::DemoFixture.new
      when "http" then Jev::HttpClient.new(model: ENV.fetch("CLOUDWALK_JEV_MODEL", "jev-latest"))
      when "disabled" then return review(:classifier_disabled)
      else return review(:invalid_classifier_mode)
      end

      classifier = build(client, categories)
      return review(:invalid_catalog) unless classifier

      classifier.call(**input)
    end

    def self.build(client, categories)
      Jev::Classifier.new(client: client, categories: categories, priorities: Catalog::PRIORITIES)
    rescue ArgumentError
      # Um catálogo incompatível com Choice exige revisão operacional.
      nil
    end

    def self.review(reason)
      Jev::Classifier::Result.new(status: :review, classification: {}, issues: { provider: reason },
                                  evidence: nil, retryable: false, retry_after_seconds: nil)
    end

    private_class_method :build, :review
  end
end
