Rails.application.configure do
  config.enable_reloading = true
  config.eager_load = false
  config.consider_all_requests_local = true
  # O serviço db_setup prepara as migrações antes de iniciar a API.
  config.active_record.migration_error = false
  config.active_record.verbose_query_logs = true
  config.hosts << "api"
  config.logger = ActiveSupport::TaggedLogging.new(Logger.new($stdout))
  config.log_level = ENV.fetch("RAILS_LOG_LEVEL", "info")
end
