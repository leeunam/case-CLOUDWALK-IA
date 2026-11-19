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

      def staff_identity
        @staff_identity ||= BrowserAccess::Session.resolve(session, "staff")
      end

      def simulator_identity
        @simulator_identity ||= BrowserAccess::Session.resolve(session, "simulator")
      end

      def current_user
        @current_user ||= staff_identity&.user
      end

      def start_browser_identity!(audience, user: nil)
        identities = BrowserAccess::Session::COOKIE_KEYS.values.to_h { |key| [key, session[key]] }.compact
        identity = BrowserAccess::Session.start!(session, audience, user: user)
        identities[BrowserAccess::Session::COOKIE_KEYS.fetch(audience)] = identity.id
        reset_session
        identities.each { |key, value| session[key] = value }
        identity
      end

      def simulator_session_data(identity)
        {
          user: { id: identity.id, name: "Cliente simulado", role: "simulator",
                  brand_ids: identity.simulator_channels.distinct.order(:brand_id).pluck(:brand_id), attendant_id: nil },
          operation: nil, csrf_token: form_authenticity_token
        }
      end

      def bounded_integer(key, default:, range:)
        raw = request.query_parameters.fetch(key, default.to_s)
        value = Integer(raw, 10, exception: false) if raw.is_a?(String) && raw.match?(/\A[0-9]+\z/)
        invalid_query!(key) unless value && range.cover?(value)
        value
      end

      def invalid_query!(key)
        raise WebhookV1::Error.new(422, "invalid_query", "Parâmetro inválido: #{key}.")
      end

      def paginated(relation, order:, scope:)
        limit = bounded_integer("limit", default: 25, range: 1..100)
        signer = Rails.application.message_verifier("browser-collection")
        purpose = scope.join(":")
        if request.query_parameters.key?("cursor")
          token = request.query_parameters["cursor"]
          cursor = signer.verified(token, purpose: purpose) if token.is_a?(String) && token.present?
          invalid_query!("cursor") unless cursor.is_a?(Array) && cursor.size == order.size
          columns = order.join(", ")
          values = (["?"] * order.size).join(", ")
          relation = relation.where("(#{columns}) < (#{values})", *cursor)
        end
        rows = relation.order(order.index_with(:desc)).limit(limit + 1).to_a
        items = rows.first(limit)
        if rows.size > limit
          position = order.map do |column|
            value = items.last.public_send(column)
            value.respond_to?(:iso8601) ? value.iso8601(6) : value
          end
          next_cursor = signer.generate(position, purpose: purpose)
        end
        { items: items, next_cursor: next_cursor }
      end

      def messages_page(relation)
        after = bounded_integer("after_sequence", default: 0, range: 0..)
        limit = bounded_integer("limit", default: 25, range: 1..100)
        rows = relation.where("sequence > ?", [after, 2**31 - 1].min).order(:sequence).limit(limit + 1).to_a
        items = rows.first(limit)
        { items: items.map(&:contract_data), next_after_sequence: rows.size > limit ? items.last.sequence : nil }
      end

      def require_user!
        return if current_user

        raise WebhookV1::Error.new(401, "unauthenticated", "Sessão autenticada necessária.")
      end

      def require_simulator!
        return if simulator_identity

        raise WebhookV1::Error.new(401, "unauthenticated", "Sessão do simulador necessária.")
      end
    end
  end
end
