require "date"

module AgentIntegration
  module E01
    class Preflight
      PROVIDER = "feita"
      MODEL = "openai/gpt-5.6-luna"
      ROUTE = "https://api.feita.ai/gateway/v1/chat/completions"
      CAPS = %w[input_cap output_cap].freeze
      INPUT_RATE = "input_rate_usd_per_million"
      CACHE_RATE = "cache_rate_usd_per_million"
      OUTPUT_RATE = "output_rate_usd_per_million"
      RATES = [INPUT_RATE, CACHE_RATE, OUTPUT_RATE].freeze
      EVIDENCE = %w[input_cap output_cap input_rate cache_rate output_rate billing_terms billable_failures].freeze
      FIELDS = (%w[mode provider model route account_ref policy_version documented_on billing_terms evidence] + CAPS + RATES).freeze
      MAX_BYTES = 16.kilobytes

      attr_reader :data

      def self.load!
        path = ENV["CLOUDWALK_E01_PREFLIGHT_PATH"].presence
        raise Error, "preflight_missing" unless path && File.file?(path)

        bytes = File.binread(path, MAX_BYTES + 1)
        raise Error, "preflight_missing" if bytes.bytesize > MAX_BYTES

        snapshot = new(Contract.parse_object(bytes))
        raise Error, "preflight_missing" unless snapshot.valid?

        snapshot
      rescue SystemCallError, IOError, JSON::ParserError, EncodingError, ArgumentError
        raise Error, "preflight_missing"
      end

      def initialize(data)
        @data = data
      end

      def valid?
        return false unless @data.keys.sort == FIELDS.sort
        return false unless @data.values_at("provider", "model", "route") == [PROVIDER, MODEL, ROUTE]
        return false unless @data["mode"] == "feita_verified" || (Rails.env.test? && @data["mode"] == "offline_test")
        return false unless reference?(@data["account_ref"]) && documented?
        return false unless @data["policy_version"].is_a?(String) && @data["policy_version"].match?(/\A[a-z][a-z0-9._-]{0,79}\z/)
        return false unless CAPS.all? { |field| @data[field].is_a?(Integer) && (1..2_147_483_647).cover?(@data[field]) }
        return false unless RATES.all? { |field| @data[field].is_a?(String) && @data[field].match?(/\A[0-9]+(?:\.[0-9]+)?\z/) }
        return false unless Contract.valid?("billing_terms", @data["billing_terms"])

        evidence = @data["evidence"]
        evidence.is_a?(Hash) && evidence.keys.sort == EVIDENCE.sort && evidence.values.all? { |value| reference?(value) } &&
          cache_rate <= input_rate && reserve.positive?
      end

      def reserve
        usd(@data.fetch("input_cap") * input_rate + @data.fetch("output_cap") * output_rate)
      end

      def cost!(usage)
        input, cached, output = usage.values_at("input_tokens", "cached_input_tokens", "output_tokens")
        unless [input, cached, output].all?(Integer) && cached.between?(0, input) &&
               input.between?(0, @data.fetch("input_cap")) && output.between?(0, @data.fetch("output_cap")) &&
               !usage.fetch("provider_response_id").include?("\0")
          raise Error, "invalid_body"
        end

        usd((input - cached) * input_rate + cached * cache_rate + output * output_rate)
      end

      private

      def documented?
        value = @data["documented_on"]
        value.is_a?(String) && value.match?(/\A[0-9]{4}-[0-9]{2}-[0-9]{2}\z/) && Date.iso8601(value) <= Time.current.to_date
      end

      def reference?(value)
        value.is_a?(String) && (1..500).cover?(value.length) && value.match?(/\S/) && !value.match?(/[[:cntrl:]]/)
      end

      def input_rate = BigDecimal(@data.fetch(INPUT_RATE))
      def cache_rate = BigDecimal(@data.fetch(CACHE_RATE))
      def output_rate = BigDecimal(@data.fetch(OUTPUT_RATE))

      def usd(microdollars)
        (microdollars / 1_000_000).ceil(12)
      end
    end
  end
end
