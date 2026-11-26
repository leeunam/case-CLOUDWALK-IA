require "socket"

# Transporte local controlado. Os corpos 200 vêm das fixtures aprovadas em C06-A.
class SetfitEndpoint
  attr_reader :url, :requests
  attr_accessor :reply

  def self.fixture(name)
    directory = ENV.fetch("CLASSIFICATION_CONTRACT_DIR", Rails.root.join("../docs/contratos/classification-http"))
    JSON.parse(File.read(File.join(directory, "fixtures", "#{name}.json")))
  end

  def initialize
    @server = TCPServer.new("127.0.0.1", 0)
    @url = "http://127.0.0.1:#{@server.local_address.ip_port}"
    @requests = []
    @reply = method(:complete)
    @thread = Thread.new do
      loop do
        socket = begin
          @server.accept
        rescue IOError, Errno::EBADF
          break if @server.closed?
          raise
        end
        begin
          respond(socket)
        rescue Errno::EPIPE, Errno::ECONNRESET
          # O cliente pode encerrar o socket ao expirar seu prazo absoluto.
        ensure
          socket.close
        end
      end
    end
  end

  def close
    @server.close
    @thread.value
  end

  def complete(request)
    fixture = request.fetch("received").values.all?(&:nil?) ? "response-complete-both" : "response-complete"
    body = self.class.fixture(fixture).merge(request.slice("id", "catalog_version"))
    body["catalog_sha256"] = Classification::SetfitContract.catalog_sha256(request.fetch("catalog"))
    [200, body]
  end

  private

  def respond(socket)
    raise "rota inesperada" unless socket.gets == "POST /internal/classification/v1/complete HTTP/1.1\r\n"
    headers = {}
    while (line = socket.gets) != "\r\n"
      name, value = line.chomp.split(": ", 2)
      headers[name.downcase] = value
    end
    raise "tipo inesperado" unless headers["content-type"] == "application/json"
    request = JSON.parse(socket.read(Integer(headers.fetch("content-length"))))
    @requests << request
    status, body, interval = @reply.call(request)
    bytes = body.is_a?(String) ? body : JSON.generate(body)
    socket.write("HTTP/1.1 #{status} Test\r\nContent-Type: application/json\r\nContent-Length: #{bytes.bytesize}\r\nConnection: close\r\n\r\n")
    if interval
      bytes.each_char { |char| socket.write(char); sleep interval }
    else
      socket.write(bytes)
    end
  end
end
