require "test_helper"
require "open3"
require "tmpdir"

class HealthFailureTest < ActiveSupport::TestCase
  test "a pilha de desenvolvimento retorna JSON 503 quando o banco está inacessível" do
    request = <<~RUBY
      response = Rack::MockRequest.new(Rails.application).get(
        "/api/v1/health", "HTTP_HOST" => "localhost", "HTTP_ACCEPT" => "application/json"
      )
      puts JSON.generate(status: response.status, body: JSON.parse(response.body))
    RUBY

    Dir.mktmpdir("cloudwalk-no-postgres-") do |empty_socket_directory|
      output, errors, process = Open3.capture3(
        { "RAILS_ENV" => "development", "POSTGRES_HOST" => empty_socket_directory },
        RbConfig.ruby, "-r", "./config/environment", "-r", "rack/mock", "-r", "json",
        "-e", request, chdir: Rails.root.to_s
      )

      assert process.success?, errors
      result = JSON.parse(output.lines.last)
      assert_equal 503, result.fetch("status")
      assert_equal({ "status" => "error", "database" => "unavailable" }, result.fetch("body"))
    end
  end
end
