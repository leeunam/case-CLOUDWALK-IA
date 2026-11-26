require "net/http"
require "timeout"

module Classification
  class SetfitClient
    PATH = "/internal/classification/v1/complete"
    DEADLINE = 6
    MAX_BYTES = 65_536

    def initialize(url: ENV.fetch("SETFIT_URL", "http://setfit:8080"), deadline: DEADLINE)
      @url = url
      @deadline = deadline
    end

    def call(id:, snapshot:, text:)
      started = Process.clock_gettime(Process::CLOCK_MONOTONIC)
      result = classify_with_deadline(id, snapshot, text)
      elapsed = Process.clock_gettime(Process::CLOCK_MONOTONIC) - started
      result = Result.review(:timeout) if elapsed >= @deadline
      result.with(evidence: (result.evidence || {}).merge("client_elapsed_ms" => (elapsed * 1000).round(3)))
    end

    private

    def classify_with_deadline(id, snapshot, text)
      Timeout.timeout(@deadline) { classify(id, snapshot, text) }
    rescue Timeout::Error
      Result.review(:timeout)
    rescue SetfitContract::Invalid, JSON::ParserError, EncodingError, Net::HTTPBadResponse, Net::HTTPHeaderSyntaxError, Net::ProtocolError
      Result.review(:invalid_response)
    rescue URI::InvalidURIError, SetfitContract::Unavailable
      Result.review(:invalid_classifier_mode)
    rescue SocketError, IOError, SystemCallError
      Result.review(:network_error)
    end

    def classify(id, snapshot, text)
      contract = SetfitContract.current
      catalog = snapshot.fetch("catalog")
      received = snapshot.fetch("received").transform_values { |value| value == "" ? nil : value }
      return Result.review(:invalid_input) unless received.all? { |field, value| value.nil? || catalog.fetch(field).key?(value) }
      return contract.complete(received, {}) if received.values.none?(&:nil?)
      return Result.review(:unsupported_catalog) unless contract.compatible?(catalog)
      return Result.review(:invalid_classifier_mode) unless snapshot.fetch("identities") == contract.identities
      return Result.review(:invalid_request) unless SetfitContract.catalog_sha256(catalog) == snapshot.fetch("catalog_sha256")

      request = { "contract_version" => contract.identities.fetch("contract_version"), "id" => id,
                  "text" => text, "catalog" => catalog, "received" => received, "catalog_version" => snapshot.fetch("catalog_version") }
      return Result.review(:invalid_request) unless request["catalog_version"].is_a?(Integer) && contract.valid_schema?("Request", request)
      encoded = JSON.generate(request)
      return Result.review(:invalid_request) if encoded.bytesize > MAX_BYTES

      status, bytes = post(encoded)
      contract.decode(status, bytes, request, snapshot)
    end

    def post(body)
      uri = URI.parse(@url)
      raise URI::InvalidURIError unless uri.is_a?(URI::HTTP) && uri.scheme == "http" && uri.host.present? &&
        !uri.userinfo && !uri.query && !uri.fragment && ["", "/"].include?(uri.path)

      http = Net::HTTP.new(uri.host, uri.port, nil)
      http.max_retries = 0
      http.ignore_eof = false
      http.open_timeout = http.read_timeout = http.write_timeout = @deadline
      request = Net::HTTP::Post.new(PATH, "Content-Type" => "application/json", "Accept-Encoding" => "identity")
      request.body = body
      http.start do |connection|
        connection.request(request) do |response|
          raise SetfitContract::Invalid unless response.content_type == "application/json"
          bytes = +"".b
          response.read_body do |chunk|
            raise SetfitContract::Invalid if bytes.bytesize + chunk.bytesize > MAX_BYTES
            bytes << chunk
          end
          return response.code.to_i, bytes
        end
      end
    end
  end
end
