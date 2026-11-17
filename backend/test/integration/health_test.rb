require "test_helper"

class HealthTest < ActionDispatch::IntegrationTest
  test "a API consulta o banco antes de informar saúde" do
    get "/api/v1/health"

    assert_response :success
    assert_equal({ "status" => "ok", "database" => "ok" }, response.parsed_body)
  end
end
