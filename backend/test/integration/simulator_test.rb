require "test_helper"

class SimulatorTest < ActionDispatch::IntegrationTest
  setup do
    Rails.application.load_seed
    @aurora = Operations::Brand.find_by!(code: "aurora")
    @horizonte = Operations::Brand.find_by!(code: "horizonte")
    @chat = @aurora.channels.find_by!(kind: "chat")
    @whatsapp = @horizonte.channels.find_by!(kind: "whatsapp")
    @email = @horizonte.channels.find_by!(kind: "email")
    @old_brands = ENV["CLOUDWALK_SIMULATOR_BRANDS"]
    @old_passwords = ENV["CLOUDWALK_DEMO_PASSWORDS"]
    @forgery_protection = Api::V1::BrowserController.allow_forgery_protection
    ENV["CLOUDWALK_SIMULATOR_BRANDS"] = "aurora,horizonte"
    ENV["CLOUDWALK_DEMO_PASSWORDS"] = { "bia@example.test" => "test" }.to_json
    Api::V1::BrowserController.allow_forgery_protection = true
  end

  teardown do
    ENV["CLOUDWALK_SIMULATOR_BRANDS"] = @old_brands
    ENV["CLOUDWALK_DEMO_PASSWORDS"] = @old_passwords
    Api::V1::BrowserController.allow_forgery_protection = @forgery_protection
  end

  test "sessão renova CSRF e seus IDs não permitem assumir conversa de outro cliente" do
    owner = open_session
    guest = open_session
    owner.get "/api/v1/session"
    anonymous_csrf = json(owner).fetch("csrf_token")
    owner.post "/api/v1/simulator/session"
    assert_equal 403, owner.response.status
    owner_csrf = start_simulator(owner, csrf: anonymous_csrf)
    guest_csrf = start_simulator(guest)

    send_message(owner, @chat, anonymous_csrf, key: "new")
    assert_equal 403, owner.response.status
    send_message(owner, @chat, owner_csrf, key: "new")
    assert_equal 202, owner.response.status
    receipt = json(owner)
    assert WebhookV1::Contract.valid?("SimulatorReceipt", receipt)

    owner.get "/api/v1/cases/#{receipt.fetch("case_id")}"
    assert_equal 401, owner.response.status
    guest.get "/api/v1/simulator/cases/#{receipt.fetch("case_id")}"
    assert_equal 404, guest.response.status
    guest.get "/api/v1/simulator/cases/#{receipt.fetch("case_id")}/messages"
    assert_equal 404, guest.response.status
    guest.get "/api/v1/simulator/cases"
    assert_empty json(guest).fetch("items")
    send_message(guest, @chat, guest_csrf, key: "spoof", conversation: receipt.fetch("external_conversation_id"))
    assert_equal 404, guest.response.status
    send_message(owner, @whatsapp, owner_csrf, key: "wrong-channel", conversation: receipt.fetch("external_conversation_id"))
    assert_equal 404, owner.response.status

    cookie = owner.cookies["_cloudwalk_session"]
    owner.delete "/api/v1/session", headers: { "X-CSRF-Token" => owner_csrf }
    assert_equal 204, owner.response.status
    replay = open_session
    replay.cookies["_cloudwalk_session"] = cookie
    replay.get "/api/v1/simulator/cases/#{receipt.fetch("case_id")}"
    assert_equal 401, replay.response.status
  end

  test "três canais, paginação, reentrega e continuação usam o histórico canônico" do
    client = open_session
    csrf = start_simulator(client)
    receipts = [@chat, @email, @whatsapp].map do |channel|
      send_message(client, channel, csrf, key: "opening")
      assert_equal 202, client.response.status
      receipt = json(client)
      send_message(client, channel, csrf, key: "opening")
      assert_equal receipt, json(client)
      receipt
    end
    assert_equal 3, receipts.map { |receipt| receipt.fetch("case_id") }.uniq.size

    chat = receipts.first
    conversation = chat.fetch("external_conversation_id")
    send_message(client, @chat, csrf, key: "opening", text: "Outro conteúdo")
    assert_equal 409, client.response.status
    send_message(client, @chat, csrf, key: "follow-up", conversation: conversation, text: "Continuo com dúvida")
    assert_equal chat, json(client)
    record = Attendances::SupportCase.find(chat.fetch("case_id"))
    assert_equal 2, record.messages.count
    assert_equal 1, record.turns.count

    client.get "/api/v1/simulator/cases", params: { limit: 2 }
    page = json(client)
    assert WebhookV1::Contract.valid?("SimulatorCaseList", page)
    assert_equal 2, page.fetch("items").size
    client.get "/api/v1/simulator/cases", params: { limit: 2, cursor: page.fetch("next_cursor") }
    assert_equal 1, json(client).fetch("items").size
    client.get "/api/v1/simulator/cases/#{record.id}"
    assert WebhookV1::Contract.valid?("SimulatorCase", json(client))
    client.get "/api/v1/simulator/cases/#{record.id}/messages", params: { limit: 1 }
    assert_equal 1, json(client).fetch("next_after_sequence")
    client.get "/api/v1/simulator/cases/#{record.id}/messages", params: { after_sequence: 1 }
    assert_equal "Continuo com dúvida", json(client).fetch("items").sole.fetch("text")
  end

  test "identidades operacional e sintética coexistem com escopos próprios" do
    client = open_session
    client.get "/api/v1/session"
    client.post "/api/v1/session", params: { email: "bia@example.test", password: "test" }, as: :json,
      headers: { "X-CSRF-Token" => json(client).fetch("csrf_token") }
    assert_equal 200, client.response.status
    client.get "/api/v1/simulator/cases"
    assert_equal 401, client.response.status
    csrf = start_simulator(client)
    send_message(client, @whatsapp, csrf, key: "another-brand")
    receipt = json(client)
    client.get "/api/v1/cases/#{receipt.fetch("case_id")}"
    assert_equal 404, client.response.status
    client.get "/api/v1/simulator/cases/#{receipt.fetch("case_id")}"
    assert_equal 200, client.response.status
  end

  test "catálogo paginado inclui nomes somente das marcas autorizadas" do
    client = open_session
    client.get "/api/v1/channels"
    assert_equal 401, client.response.status
    ENV["CLOUDWALK_SIMULATOR_BRANDS"] = "aurora"
    csrf = start_simulator(client)

    client.get "/api/v1/channels", params: { limit: 2 }
    first = json(client)
    assert WebhookV1::Contract.valid?("ChannelList", first)
    assert_equal 2, first.fetch("items").size
    client.get "/api/v1/channels", params: { cursor: first.fetch("next_cursor") }
    second = json(client)
    channels = first.fetch("items") + second.fetch("items")
    assert_equal 3, channels.size
    assert_equal [@aurora.name], channels.pluck("brand_name").uniq
    assert_equal [@aurora.id], channels.pluck("brand_id").uniq
    send_message(client, @whatsapp, csrf, key: "outside-scope")
    assert_equal 404, client.response.status
  end

  private

  def start_simulator(client, csrf: nil)
    unless csrf
      client.get "/api/v1/session"
      csrf = json(client).fetch("csrf_token")
    end
    client.post "/api/v1/simulator/session", headers: { "X-CSRF-Token" => csrf }
    assert_equal 201, client.response.status
    assert_equal "simulator", json(client).dig("user", "role")
    json(client).fetch("csrf_token")
  end

  def send_message(client, channel, csrf, key:, text: "Dúvida sobre Pix", conversation: nil)
    client.post "/api/v1/simulator/channels/#{channel.id}/messages", as: :json,
      params: { text: text, category: "pix", priority: "basic", external_conversation_id: conversation }.compact,
      headers: { "X-CSRF-Token" => csrf, "Idempotency-Key" => key }
  end

  def json(client)
    client.response.parsed_body
  end
end
