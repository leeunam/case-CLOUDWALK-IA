module Api
  module V1
    class BrowserController < ActionController::Base
      protect_from_forgery with: :exception
      before_action :prevent_caching

      rescue_from WebhookV1::Error do |error|
        payload = { code: error.code, message: error.message }
        payload[:details] = error.details if error.details.present?
        render json: { error: payload }, status: error.status
      end

      rescue_from ActionController::InvalidAuthenticityToken do
        render json: { error: { code: "csrf_rejected", message: "Token CSRF recusado." } }, status: 403
      end

      rescue_from ActiveRecord::RecordNotFound do
        render json: { error: { code: "not_found", message: "Atendimento não encontrado." } }, status: 404
      end

      private

      def request_authenticity_tokens
        [request.x_csrf_token]
      end

      def prevent_caching
        response.headers["Cache-Control"] = "no-store"
      end

      def current_user
        @current_user ||= Operations::User.find_by(id: session[:user_id]) if session[:user_id]
      end

      def require_user!
        return if current_user

        raise WebhookV1::Error.new(401, "unauthenticated", "Sessão autenticada necessária.")
      end
    end
  end
end
