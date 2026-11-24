require "test_helper"

class PublishSessionsTest < ActiveSupport::TestCase
  setup do
    @environment = ENV.to_h.slice("CLOUDWALK_PUBLISH_DEMO_LOGIN", "CLOUDWALK_DEMO_PASSWORDS")
    @rails_env = Rails.env.to_s
    @controller = Api::V1::SessionsController.new
    @email = "bia@example.test"
    @password = SecureRandom.hex(32)
    ENV["CLOUDWALK_DEMO_PASSWORDS"] = JSON.generate(@email => @password)
    ENV.delete("CLOUDWALK_PUBLISH_DEMO_LOGIN")
  end

  teardown do
    Rails.env = @rails_env
    %w[CLOUDWALK_PUBLISH_DEMO_LOGIN CLOUDWALK_DEMO_PASSWORDS].each { |key| ENV[key] = @environment[key] }
  end

  test "produção exige habilitação explícita para credenciais de demonstração" do
    Rails.env = "production"
    refute password_valid?
    ENV["CLOUDWALK_PUBLISH_DEMO_LOGIN"] = "true"
    refute password_valid?
    ENV["CLOUDWALK_PUBLISH_DEMO_LOGIN"] = "1"
    assert password_valid?
    refute password_valid?("demonstracao@example.test")
    refute password_valid?(@email, SecureRandom.hex(32))
  end

  test "produção rejeita configuração ausente inválida e vazia" do
    Rails.env = "production"
    ENV["CLOUDWALK_PUBLISH_DEMO_LOGIN"] = "1"
    [nil, "{", "[]", JSON.generate(@email => ""), JSON.generate(@email => 123)].each do |raw|
      ENV["CLOUDWALK_DEMO_PASSWORDS"] = raw
      refute password_valid?
    end
  end

  test "desenvolvimento e teste preservam a autenticação existente" do
    %w[development test].each do |environment|
      Rails.env = environment
      assert password_valid?
    end
  end

  private

  def password_valid?(email = @email, password = @password)
    @controller.send(:demo_password_valid?, email, password)
  end
end
