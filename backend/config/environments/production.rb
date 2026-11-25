Rails.application.configure do
  config.enable_reloading = false
  config.eager_load = true
  config.consider_all_requests_local = false
  config.force_ssl = true

  if ENV["CLOUDWALK_PUBLISH_BEHIND_PROXY"] == "1"
    # Only Caddy and services on the private Compose network can reach Rails.
    config.assume_ssl = true
    local_port = Integer(ENV.fetch("CLOUDWALK_PUBLISH_HTTPS_PORT", "18443"), 10)
    raise ArgumentError, "Porta HTTPS local inválida." unless (1..65_535).cover?(local_port)

    public_origin = ENV["CLOUDWALK_PUBLIC_ORIGIN"].presence
    public_host = public_origin&.match(%r{\Ahttps://([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.trycloudflare\.com)\z})&.[](1)
    if public_origin && !public_host
      raise ArgumentError, "Origem pública do Quick Tunnel inválida."
    end

    config.hosts = ["localhost", "127.0.0.1", "api", public_host].compact
    config.action_cable.allow_same_origin_as_host = false
    config.action_cable.allowed_request_origins = ["https://127.0.0.1:#{local_port}", public_origin].compact
  end

  config.log_level = ENV.fetch("RAILS_LOG_LEVEL", "info")
  config.logger = ActiveSupport::TaggedLogging.new(Logger.new($stdout))
end
