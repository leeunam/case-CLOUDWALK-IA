require "openssl"

module WebhookV1
  module Signature
    WINDOW = 300

    def self.headers(secret, body, timestamp: Time.now.to_i.to_s)
      {
        "X-Webhook-Timestamp" => timestamp,
        "X-Webhook-Signature" => OpenSSL::HMAC.hexdigest("SHA256", secret, "#{timestamp}.#{body}")
      }
    end

    def self.valid?(secret, body, timestamp, signature, now: Time.now.to_i)
      return false if secret.blank? || !timestamp.to_s.match?(/\A[0-9]+\z/) ||
                      !signature.to_s.match?(/\A[0-9a-f]{64}\z/)

      seconds = timestamp.sub(/\A0+/, "")
      return false if seconds.size > 20 || (now - seconds.to_i).abs > WINDOW

      expected = headers(secret, body, timestamp: timestamp).fetch("X-Webhook-Signature")
      ActiveSupport::SecurityUtils.secure_compare(signature, expected)
    end

    def self.channel_secret(channel)
      root = ENV["CLOUDWALK_CHANNEL_SECRET"]
      return if root.blank?

      OpenSSL::HMAC.hexdigest("SHA256", root, "channel:#{channel.id}")
    end
  end
end
