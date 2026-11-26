require "openssl"

module AgentIntegration
  module E01
    module Authentication
      WINDOW = 30
      TIMESTAMP = /\A(?:0|[1-9][0-9]{0,18})\z/
      NONCE = /\A[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\z/

      def self.verify!(request, body, now: Time.current)
        secret = ENV["CLOUDWALK_E01_LEDGER_SECRET"]
        timestamp = request.get_header("HTTP_X_E01_TIMESTAMP").to_s
        nonce = request.get_header("HTTP_X_E01_NONCE").to_s
        signature = request.get_header("HTTP_X_E01_SIGNATURE").to_s
        unless secret.present? && TIMESTAMP.match?(timestamp) && NONCE.match?(nonce) &&
               Contract::SHA256.match?(signature) && (now.to_i - timestamp.to_i).abs <= WINDOW
          raise Error, "unauthenticated"
        end

        message = "#{timestamp}\n#{nonce}\nPOST\n#{request.path}\n".b + body.b
        expected = OpenSSL::HMAC.hexdigest("SHA256", secret, message)
        raise Error, "unauthenticated" unless ActiveSupport::SecurityUtils.secure_compare(signature, expected)

        inserted = Nonce.insert_all([{ id: nonce, expires_at: Time.at(timestamp.to_i + WINDOW + 1) }],
                                    unique_by: :id, returning: [:id])
        raise Error, "nonce_reused" if inserted.rows.empty?
      end
    end
  end
end
