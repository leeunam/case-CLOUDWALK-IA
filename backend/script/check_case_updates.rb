# Ensaio com API e PostgreSQL reais, em uma pilha de demonstração sem worker ativo.
require "json"
require "net/http"
require "rbconfig"
require "securerandom"
require "socket"
require "websocket/driver"

class DemoBrowser
  attr_reader :cookie, :origin

  def initialize(url)
    @url = URI(url)
    @origin = @url.to_s.delete_suffix("/")
  end

  def request(method, path, status:, data: nil, key: nil)
    headers = { "Cookie" => @cookie, "X-CSRF-Token" => @csrf, "Origin" => @origin,
                "Idempotency-Key" => key }.compact
    request = Net::HTTPGenericRequest.new(method, !data.nil?, method != "HEAD", path, headers)
    if data
      request["Content-Type"] = "application/json"
      request.body = JSON.generate(data)
    end
    response = Net::HTTP.start(@url.host, @url.port, open_timeout: 5, read_timeout: 5) { |http| http.request(request) }
    @cookie = response["Set-Cookie"]&.split(";", 2)&.first || @cookie
    raise "#{method} #{path}: HTTP #{response.code} (esperado #{status})" unless response.code.to_i == status

    result = JSON.parse(response.body) if response.body && !response.body.empty?
    @csrf = result["csrf_token"] if result.is_a?(Hash) && result.key?("csrf_token")
    result
  end

  def start_simulator
    request("GET", "/api/v1/session", status: 200)
    request("POST", "/api/v1/simulator/session", status: 201)
  end
end

class DemoCable
  attr_reader :url

  def initialize(browser)
    origin = URI(browser.origin)
    @url = "ws://#{origin.host}:#{origin.port}/cable"
    @socket = Socket.tcp(origin.host, origin.port, connect_timeout: 5)
    @messages = []
    @driver = WebSocket::Driver.client(self, protocols: ["actioncable-v1-json"])
    @driver.set_header("Origin", browser.origin)
    @driver.set_header("Cookie", browser.cookie) if browser.cookie
    @driver.on(:message) { |event| @messages << JSON.parse(event.data) }
    @driver.start
  end

  def write(data)
    @socket.write(data)
  end

  def subscribe(case_id, audience)
    identifier = JSON.generate(channel: "CaseUpdatesChannel", case_id: case_id, audience: audience)
    @driver.text(JSON.generate(command: "subscribe", identifier: identifier))
    identifier
  end

  def expect(timeout: 10, &condition)
    wait_for(timeout, &condition) || raise("Mensagem WebSocket esperada não recebida")
  end

  def expect_no_update(identifier)
    message = wait_for(2) { |frame| frame["identifier"] == identifier && frame.key?("message") }
    raise "Aviso entregue após logout" if message
  end

  def close
    @socket.close
  end

  private

  def wait_for(timeout, &condition)
    deadline = Process.clock_gettime(Process::CLOCK_MONOTONIC) + timeout
    loop do
      index = @messages.index(&condition)
      return @messages.delete_at(index) if index

      remaining = deadline - Process.clock_gettime(Process::CLOCK_MONOTONIC)
      return if remaining <= 0 || !IO.select([@socket], nil, nil, remaining)

      @driver.parse(@socket.readpartial(4096))
    end
  end
end

def expect_update(connection, identifier, case_id, timeout: 10)
  frame = connection.expect(timeout: timeout) { |item| item["identifier"] == identifier && item.key?("message") }
  expected = { "type" => "case.updated", "case_id" => case_id }
  raise "Aviso fora do contrato" unless frame.fetch("message") == expected
end

def send_message(browser, channel_id, data)
  browser.request("POST", "/api/v1/simulator/channels/#{channel_id}/messages", status: 202,
    data: data, key: SecureRandom.uuid)
end

owner = DemoBrowser.new(ENV.fetch("CLOUDWALK_CABLE_TEST_API", "http://api:3000"))
guest = DemoBrowser.new(owner.origin)
begin
  anonymous = DemoCable.new(owner)
  anonymous.expect { |frame| frame["type"] == "disconnect" && frame["reason"] == "unauthorized" }
  owner.start_simulator
  guest.start_simulator
  channels = owner.request("GET", "/api/v1/channels", status: 200).fetch("items")
  channel_id = channels.find { |channel| channel.fetch("type") == "chat" }.fetch("id")
  receipt = send_message(owner, channel_id, { text: "Qual é o prazo de um Pix?", priority: "basic" })
  case_id = receipt.fetch("case_id")
  case_path = "/api/v1/simulator/cases/#{case_id}"
  pending = owner.request("GET", case_path, status: 200)
  raise "Use uma pilha isolada sem worker ativo" unless pending.fetch("status") == "classification_pending"

  guest.request("GET", case_path, status: 404)
  owner_socket = DemoCable.new(owner)
  guest_socket = DemoCable.new(guest)
  [owner_socket, guest_socket].each { |connection| connection.expect { |frame| frame["type"] == "welcome" } }
  identifier = owner_socket.subscribe(case_id, "simulator")
  owner_socket.expect { |frame| frame["type"] == "confirm_subscription" && frame["identifier"] == identifier }
  rejected = guest_socket.subscribe(case_id, "simulator")
  guest_socket.expect { |frame| frame["type"] == "reject_subscription" && frame["identifier"] == rejected }
  staff = owner_socket.subscribe(case_id, "staff")
  owner_socket.expect { |frame| frame["type"] == "reject_subscription" && frame["identifier"] == staff }

  conversation = receipt.fetch("external_conversation_id")
  send_message(owner, channel_id, { text: "Ainda preciso de orientação.", external_conversation_id: conversation })
  expect_update(owner_socket, identifier, case_id)

  worker = Process.spawn({ "CLOUDWALK_JEV_MODE" => "fixture" }, RbConfig.ruby, "bin/jobs",
                         pgroup: true, out: File::NULL, err: File::NULL)
  expect_update(owner_socket, identifier, case_id, timeout: 20)
  classified = owner.request("GET", case_path, status: 200)
  raise "Classificação não aplicada pelo worker" unless classified.fetch("status") == "ai_active"

  owner.request("DELETE", "/api/v1/session", status: 204)
  owner.request("GET", case_path, status: 401)
  # A mutação abaixo usa outra conexão/processo, com a assinatura antiga ainda aberta.
  code = "record = Attendances::SupportCase.find(ARGV.fetch(0)); record.with_lock { record.advance! }"
  result = system(RbConfig.ruby, "bin/rails", "runner", code, case_id, out: File::NULL)
  raise "Falha na mutação após logout" unless result
  owner_socket.expect_no_update(identifier)
  puts "Cable PostgreSQL verificado: aviso da API e do worker, isolamento REST/audiência e logout."
ensure
  [anonymous, owner_socket, guest_socket].compact.each(&:close)
  if worker
    begin
      Process.kill("TERM", -worker)
    rescue Errno::ESRCH
      # O supervisor já encerrou.
    end
    Process.wait(worker)
  end
end
