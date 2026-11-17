module Infrastructure
  class HealthCheckJob < ApplicationJob
    def perform
      Rails.logger.info("Worker conectado ao Solid Queue e ao PostgreSQL.")
    end
  end
end
