module AgentIntegration
  module E01
    class Error < StandardError
      STATUSES = {
        "unauthenticated" => 401, "not_found" => 404, "too_large" => 413,
        "invalid_body" => 422, "preflight_missing" => 503
      }.freeze

      def status
        STATUSES.fetch(message, 409)
      end
    end
  end
end
