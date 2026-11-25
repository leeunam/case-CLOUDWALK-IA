require "minitest/autorun"
require "stringio"
require_relative "samples"

class JevHttpClientTest < Minitest::Test
  include JevSamples

  class Connection
    attr_accessor :use_ssl, :open_timeout, :read_timeout, :write_timeout, :max_retries
    attr_reader :requests

    def initialize(&exchange)
      @exchange = exchange
      @requests = []
    end

    def start
      yield self
    end

    def request(request)
      @requests << request
      @exchange.call(request)
    end
  end

  Response = Struct.new(:code, :body, :headers) do
    def [](name)
      headers[name]
    end
  end

  def setup
    @input = channel_input("channel-entry").merge(category: nil)
  end

  def test_official_http_shape_and_model_evidence
    answer = choice(:category, "pix")
    body = JSON.generate(model: "jev-1.13.0", answers: { category: answer, priority: choice(:priority, "urgent") },
                         ignored: "classificação").b.freeze
    connection = Connection.new { Response.new("200", body, {}) }

    result = classifier(http_client(connection)).call(**@input)

    assert_equal :complete, result.status
    assert_equal "basic", result.classification.fetch(:priority)
    assert_equal "channel", result.classification.fetch(:priority_source)
    assert_equal :http, result.evidence.fetch(:mode)
    assert_equal "jev-latest", result.evidence.fetch(:requested_model)
    assert_equal "jev-1.13.0", result.evidence.fetch(:model)
    assert_equal [:category], result.evidence.fetch(:answers).keys
    assert_equal 1, connection.requests.length
    request = connection.requests.fetch(0)
    assert_equal "POST", request.method
    assert_equal "/v1/systemone", request.path
    assert_equal "Bearer chave-sintetica", request["Authorization"]
    assert_equal "application/json", request["Content-Type"]
    sent = JSON.parse(request.body)
    assert_equal %w[model state questions], sent.keys
    assert_equal "jev-latest", sent.fetch("model")
    assert_equal @input.fetch(:text), sent.fetch("state")
    assert_equal ["category"], sent.fetch("questions").keys
    question = sent.fetch("questions").fetch("category")
    assert_equal %w[type instructions criteria], question.keys
    assert_equal "choice", question.fetch("type")
    assert_equal CATEGORIES.keys + ["informacao_insuficiente"], question.fetch("criteria").keys
    assert connection.use_ssl
    assert_equal [5, 5, 5, 0], [connection.open_timeout, connection.read_timeout, connection.write_timeout,
                               connection.max_retries]
  end

  def test_missing_key_requires_review_without_network
    client = Classification::Jev::HttpClient.new(
      api_key: " ", connection_factory: ->(*) { flunk("não deve abrir conexão sem chave") }
    )
    result = classifier(client).call(**@input)

    assert_equal :review, result.status
    assert_equal({ provider: :missing_credentials }, result.issues)
    assert_equal "basic", result.classification.fetch(:priority)
    refute result.retryable
  end

  def test_timeout_bounds_the_entire_attempt_and_keeps_channel_data
    connection = Connection.new { sleep 0.25 }

    result = classifier(http_client(connection, timeout_seconds: 0.02)).call(**@input)

    assert_equal :review, result.status
    assert_equal({ provider: :timeout }, result.issues)
    assert_equal "basic", result.classification.fetch(:priority)
    assert result.retryable
    assert_equal 1, connection.requests.length
    assert_equal 0.02, connection.read_timeout
  end

  def test_reports_network_failure_as_retryable
    connection = Connection.new { raise SocketError, "conteúdo bruto do erro" }
    result = classifier(http_client(connection)).call(**@input)

    assert_equal :review, result.status
    assert_equal({ provider: :network_error }, result.issues)
    assert result.retryable
    refute_includes result.to_s, "conteúdo bruto do erro"
  end

  def test_classifies_http_errors_and_keeps_retry_after
    [
      ["401", "30", false, nil],
      ["429", "17", true, 17],
      ["503", "malformado", true, nil],
      ["302", nil, false, nil]
    ].each do |status, retry_after, retryable, delay|
      connection = Connection.new { Response.new(status, "corpo bruto do erro", { "Retry-After" => retry_after }) }
      result = classifier(http_client(connection)).call(**@input)

      assert_equal :review, result.status
      assert_equal({ provider: :http_error }, result.issues)
      assert_equal status.to_i, result.evidence.fetch(:http_status)
      assert_equal retryable, result.retryable
      if delay
        assert_equal delay, result.retry_after_seconds
      else
        assert_nil result.retry_after_seconds
      end
      assert_equal 1, connection.requests.length
      refute_includes result.to_s, "corpo bruto do erro"
    end
  end

  def test_understands_retry_after_as_http_date
    expired_date = Time.utc(2000, 1, 1).httpdate
    connection = Connection.new { Response.new("503", "", { "Retry-After" => expired_date }) }
    result = classifier(http_client(connection)).call(**@input)

    assert_equal 0, result.retry_after_seconds
  end

  def test_invalid_json_and_wrong_top_level_shape_require_review
    ["html", "[]", '{"model":"jev-1.13.0","answers":[]}'].each do |body|
      connection = Connection.new { Response.new("200", body, {}) }
      result = classifier(http_client(connection)).call(**@input)

      assert_equal :review, result.status
      assert_equal :invalid_response, result.issues.fetch(:provider)
      assert_nil result.classification.fetch(:category)
      assert_equal "basic", result.classification.fetch(:priority)
      refute result.retryable
    end
  end

  def test_invalid_utf8_body_requires_review
    body = "{\"model\":\"jev-\xFF\",\"answers\":#{JSON.generate(category: choice(:category, "pix"))}}".b
    connection = Connection.new { Response.new("200", body, {}) }

    result = classifier(http_client(connection)).call(**@input)

    assert_equal :review, result.status
    assert_equal({ provider: :invalid_response }, result.issues)
    assert_equal({ category: nil, category_source: nil, priority: "basic", priority_source: "channel" },
                 result.classification)
    assert_equal 200, result.evidence.fetch(:http_status)
    refute result.evidence.key?(:model)
    refute result.retryable
  end

  def test_corrupted_gzip_body_requires_review
    wire_response = "HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Length: 4\r\n\r\nboom"
    connection = Connection.new do |request|
      socket = Net::BufferedIO.new(StringIO.new(wire_response))
      response = Net::HTTPResponse.read_new(socket)
      response.decode_content = request.decode_content
      response.reading_body(socket, true) { response.body }
      response
    end

    result = classifier(http_client(connection)).call(**@input)

    assert_equal :review, result.status
    assert_equal({ provider: :invalid_response }, result.issues)
    assert_equal({ category: nil, category_source: nil, priority: "basic", priority_source: "channel" },
                 result.classification)
    assert_equal :http, result.evidence.fetch(:mode)
    assert_equal "jev-latest", result.evidence.fetch(:requested_model)
    refute result.retryable
  end

  def test_missing_model_identity_prevents_completion_and_keeps_the_available_answer
    body = JSON.generate(answers: { category: choice(:category, "pix") })
    connection = Connection.new { Response.new("200", body, {}) }
    result = classifier(http_client(connection)).call(**@input)

    assert_equal :review, result.status
    assert_equal({ provider: :invalid_response }, result.issues)
    assert_nil result.classification.fetch(:category)
    assert_equal "jev-latest", result.evidence.fetch(:requested_model)
    refute result.evidence.key?(:model)
    assert_equal "pix", result.evidence.dig(:answers, :category, :choice)
  end

  private

  def http_client(connection, **options)
    factory = lambda do |host, port|
      assert_equal "api.typesafe.ai", host
      assert_equal 443, port
      connection
    end
    Classification::Jev::HttpClient.new(api_key: "chave-sintetica", connection_factory: factory, **options)
  end
end
