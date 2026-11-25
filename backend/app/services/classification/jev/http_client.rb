require "json"
require "net/http"
require "time"
require "timeout"
require "zlib"

module Classification
  module Jev
    class HttpClient
      ENDPOINT = URI("https://api.typesafe.ai/v1/systemone").freeze

      class Error < StandardError
        attr_reader :reason, :http_status, :retry_after_seconds

        def initialize(reason, http_status: nil, retryable: false, retry_after_seconds: nil)
          super(reason.to_s)
          @reason = reason
          @http_status = http_status
          @retryable = retryable
          @retry_after_seconds = retry_after_seconds
        end

        def retryable?
          @retryable
        end
      end

      attr_reader :model

      def initialize(api_key: ENV["TYPESAFE_API_KEY"], model: "jev-latest", timeout_seconds: 5,
                     connection_factory: Net::HTTP.method(:new))
        unless timeout_seconds.is_a?(Numeric) && timeout_seconds.finite? && timeout_seconds.positive?
          raise ArgumentError, "timeout_seconds deve ser um número positivo"
        end

        @api_key = api_key.to_s.strip
        @model = model
        @timeout_seconds = timeout_seconds
        @connection_factory = connection_factory
      end

      def mode
        :http
      end

      def call(state:, questions:)
        raise Error.new(:missing_credentials) if @api_key.empty?

        request = Net::HTTP::Post.new(ENDPOINT)
        request["Authorization"] = "Bearer #{@api_key}"
        request["Content-Type"] = "application/json"
        request.body = JSON.generate(model: model, state: state, questions: questions)

        read_response(request)
      end

      private

      def read_response(request)
        response = Timeout.timeout(@timeout_seconds) { send_request(request) }
        status = response.code.to_i
        raise http_error(response, status) unless status == 200

        body = response.body.to_s.dup.force_encoding(Encoding::UTF_8)
        raise Error.new(:invalid_response, http_status: status) unless body.valid_encoding?

        JSON.parse(body)
      rescue JSON::ParserError, EncodingError, Net::ProtocolError, Net::HTTPBadResponse, Zlib::Error
        raise Error.new(:invalid_response, http_status: status)
      rescue Timeout::Error
        raise Error.new(:timeout, retryable: true)
      rescue SocketError, IOError, SystemCallError, OpenSSL::SSL::SSLError
        raise Error.new(:network_error, retryable: true)
      end

      def send_request(request)
        http = @connection_factory.call(ENDPOINT.host, ENDPOINT.port)
        http.use_ssl = true
        http.open_timeout = http.read_timeout = http.write_timeout = @timeout_seconds
        http.max_retries = 0
        http.start { |connection| connection.request(request) }
      end

      def http_error(response, status)
        retryable = status == 429 || status.between?(500, 599)
        Error.new(:http_error, http_status: status, retryable: retryable,
                  retry_after_seconds: retryable ? retry_after(response["Retry-After"]) : nil)
      end

      def retry_after(value)
        return if value.nil?
        return value.to_i if value.match?(/\A[0-9]+\z/)

        [(Time.httpdate(value) - Time.now).ceil, 0].max
      rescue ArgumentError
        nil
      end
    end
  end
end
