module Api
  module V1
    class HealthController < ApplicationController
      def show
        ActiveRecord::Base.connection.select_value("SELECT 1")
        render json: { status: "ok", database: "ok" }
      rescue ActiveRecord::ActiveRecordError, PG::Error
        render json: { status: "error", database: "unavailable" },
               status: :service_unavailable
      end
    end
  end
end
