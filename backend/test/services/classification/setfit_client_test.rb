require "test_helper"
require_relative "../../support/setfit_endpoint"

class SetfitClientTest < ActiveSupport::TestCase
  setup do
    @endpoint = SetfitEndpoint.new
    @client = Classification::SetfitClient.new(url: @endpoint.url)
    @request = SetfitEndpoint.fixture("request")
    @contract = Classification::SetfitContract.current
  end

  teardown { @endpoint.close }

  test "aceita os envelopes de um e dois ausentes e preserva texto e evidência numérica" do
    result = classify
    assert_equal :complete, result.status
    assert_equal %w[pix channel urgent setfit], result.classification.values_at(:category, :category_source, :priority, :priority_source)
    assert_equal 0.85, result.evidence.dig("fields", "priority", "margin")
    assert_equal @request, @endpoint.requests.sole

    @request = SetfitEndpoint.fixture("request-both")
    assert_equal %w[setfit setfit], classify.classification.values_at(:category_source, :priority_source)
    assert_equal @request, @endpoint.requests.last
    %w[review error].each do |name|
      @request = SetfitEndpoint.fixture("request")
      @endpoint.reply = ->(_) { [200, SetfitEndpoint.fixture("response-#{name}")] }
      result = classify
      assert_equal :review, result.status
      assert_empty result.classification
      refute result.retryable
      assert_equal name, result.evidence["outcome"]
    end
  end

  test "controles locais dispensam HTTP para entrada completa inválida ou catálogo incompatível" do
    @request["received"]["priority"] = "basic"
    assert_equal :complete, classify.status
    @request["received"]["priority"] = nil
    [" ", 1, {}, false, ["pix"], "extra"].each do |invalid|
      @request["received"]["category"] = invalid
      assert_equal :invalid_input, classify.issues[:provider]
    end
    @request["received"]["category"] = "pix"
    @request["catalog"]["category"]["pix"] += " alterado"
    assert_equal :unsupported_catalog, classify.issues[:provider]
    assert_empty @endpoint.requests
  end

  test "o hash compara os mesmos mapas incluindo descrições literais em qualquer ordem" do
    catalog = @request.fetch("catalog")
    expected = "0cadca6fc5e2291b3e471df649d098123bf01cb8b422803c45b6cb9f22d63807"
    assert_equal expected, Classification::SetfitContract.catalog_sha256(catalog)
    reversed = catalog.to_a.reverse.to_h.transform_values { |items| items.to_a.reverse.to_h }
    assert_equal expected, Classification::SetfitContract.catalog_sha256(reversed)
    reversed["category"]["pix"] += "."
    refute_equal expected, Classification::SetfitContract.catalog_sha256(reversed)
  end

  test "recusas validadas distinguem pré e pós admissão" do
    %w[422-invalid-request 422-text-out-of-scope 422-unsupported-catalog 502-worker-failure
       502-invalid-worker-frame 503-busy 503-not-ready 504-processing-timeout].each do |name|
      status = name.to_i
      body = SetfitEndpoint.fixture(name)
      @endpoint.reply = ->(_) { [status, body] }
      result = classify
      assert_equal body.fetch("error"), result.issues[:provider]
      assert_equal status == 503, result.retryable
      assert_empty result.classification
    end
    busy = SetfitEndpoint.fixture("503-busy")
    ["", "NaN", busy.merge("contract_version" => "other"), busy.merge("extra" => "private-test"),
      JSON.generate(busy).sub('"busy"', '"busy","error":"busy"')].each do |bad|
      @endpoint.reply = ->(_) { [503, bad] }
      assert_rejected
    end
  end

  test "rejeita divergências de envelope e relações R1 mesmo com schema válido" do
    mutations = [
      ->(r) { r["id"] = SecureRandom.uuid }, ->(r) { r["catalog_version"] = 7.0 },
      ->(r) { r["catalog_version"] += 1 }, ->(r) { r["catalog_sha256"] = "0" * 64 },
      ->(r) { r["contract_version"] = "other" }, ->(r) { r["package_sha256"] = "0" * 64 },
      ->(r) { r["model_sha256"]["priority"] = "0" * 64 }, ->(r) { r["decision_policy_sha256"] = "0" * 64 },
      ->(r) { r["capture_policy_sha256"] = "0" * 64 }, ->(r) { r["raw_frame_sha256"] = "x" * 64 },
      ->(r) { r["calls"]["category"] = 1 }, ->(r) { r["calls"]["priority"] = 1.0 },
      ->(r) { r["fields"]["priority"]["raw"] = "advanced" }, ->(r) { r["fields"]["priority"]["margin"] = 0.2 },
      ->(r) { r["fields"]["priority"]["cut"]["tau"] = 0.6 }, ->(r) { r["fields"]["priority"]["vector"]["scores"][0] = 0.2 },
      ->(r) { r["fields"]["priority"]["vector"]["classes"].reverse! }, ->(r) { r["applied"]["priority"] = "basic" },
      ->(r) { r["applied"]["category"] = "payouts" }, ->(r) { r["fields"]["category"]["source"] = "channel" },
      ->(r) { r["elapsed_ms"] = 5001 }, ->(r) { r["debug"] = "private-test" },
      ->(r) { r.merge!("outcome" => "review", "applied" => {}) },
      ->(r) { r["fields"]["priority"].merge!("decision" => "review", "reason" => "below_tau") },
      ->(r) { r["fields"]["priority"]["vector"]["scores"][0] = "0.01" }
    ]
    mutations.each_with_index do |mutate, index|
      body = SetfitEndpoint.fixture("response-complete")
      mutate.call(body)
      @endpoint.reply = ->(_) { [200, body] }
      assert_rejected("mutação #{index + 1}")
    end
    @request = SetfitEndpoint.fixture("request-both")
    partial = SetfitEndpoint.fixture("response-complete-both")
    partial["applied"].delete("category")
    assert @contract.valid_schema?("Response", partial)
    @endpoint.reply = ->(_) { [200, partial] }
    assert_rejected
  end

  test "corpo grande e stream contínuo terminam sem repetição ou payload na evidência" do
    @endpoint.reply = ->(_) { [200, "private-test" * 6600] }
    assert_rejected
    @client = Classification::SetfitClient.new(url: @endpoint.url, deadline: 0.2)
    @endpoint.reply = ->(_) { [503, SetfitEndpoint.fixture("503-busy"), 0.02] }
    result = classify
    assert_equal :timeout, result.issues[:provider]
    refute result.retryable
    assert_equal ["client_elapsed_ms"], result.evidence.keys
    assert_operator result.evidence.fetch("client_elapsed_ms"), :>=, 195
    assert_equal 2, @endpoint.requests.size
  end

  private

  def classify
    snapshot = @request.slice("received", "catalog_version", "catalog").merge(
      "identities" => @contract.identities, "catalog_sha256" => Classification::SetfitContract.catalog_sha256(@request.fetch("catalog")))
    @client.call(id: @request.fetch("id"), text: @request.fetch("text"), snapshot: snapshot)
  end

  def assert_rejected(message = nil)
    result = classify
    assert_equal :invalid_response, result.issues[:provider], message
    refute result.retryable
    assert_empty result.classification
    refute_includes result.inspect, "private-test"
  end
end
