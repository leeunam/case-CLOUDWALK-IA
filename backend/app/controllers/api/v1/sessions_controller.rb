require "digest"

module Api
  module V1
    class SessionsController < BrowserController
      def show
        render json: session_data
      end

      def create
        login = WebhookV1::Contract.parse!(request.raw_post, "SessionLogin")
        email = login.fetch("email").downcase
        user = Operations::User.find_by(email: email) if demo_password_valid?(email, login.fetch("password"))
        unless user
          raise WebhookV1::Error.new(401, "unauthenticated", "Credenciais inválidas.")
        end

        start_browser_identity!("staff", user: user)
        @current_user = user
        render json: session_data
      end

      def destroy
        identities = [staff_identity, simulator_identity].compact
        require_user! if identities.empty?

        BrowserAccess::Session.transaction { identities.each(&:revoke!) }
        reset_session
        head 204
      end

      def update_operation
        require_user!
        data = WebhookV1::Contract.parse!(request.raw_post, "OperationUpdate")
        Attendances::AnalystOperation.update!(current_user, data)
        render json: session_data
      end

      private

      def demo_password_valid?(email, password)
        enabled = Rails.env.development? || Rails.env.test? ||
                  (Rails.env.production? && ENV["CLOUDWALK_PUBLISH_DEMO_LOGIN"] == "1")
        return false unless enabled

        raw = ENV.fetch("CLOUDWALK_DEMO_PASSWORDS", "{}")
        passwords = JSON.parse(raw)
        expected = passwords[email] if passwords.is_a?(Hash)
        return false unless expected.is_a?(String) && expected.present?

        ActiveSupport::SecurityUtils.secure_compare(Digest::SHA256.digest(expected), Digest::SHA256.digest(password))
      rescue JSON::ParserError
        false
      end

      def session_data
        user = current_user
        unless user
          return simulator_session_data(simulator_identity) if simulator_identity

          return { user: nil, operation: nil, csrf_token: form_authenticity_token }
        end

        attendant = Operations::Attendant.find_by(user: user) if user.role == "analyst"
        {
          user: { id: user.id, name: user.name, role: user.role, attendant_id: attendant&.id,
                  brand_ids: Attendances::Visibility.new(user).brands.order(:id).pluck(:id) },
          operation: attendant && operation_data(user, attendant),
          csrf_token: form_authenticity_token
        }
      end

      def operation_data(user, attendant)
        profile = user.capacity_profiles.find_by(active: true)
        return unless profile
        portfolio = Attendances::HumanEligibility.portfolio(attendant)
        {
          active_brand_id: user.active_brand_id, switch_target_brand_id: user.switch_target_brand_id, available: user.available,
          active_count: portfolio.where(status: "human_active", brand_id: user.active_brand_id).count,
          portfolio_count: portfolio.count, portfolio_limit: profile.portfolio_limit, profile_version: profile.version
        }
      end
    end
  end
end
