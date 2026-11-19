module BrowserAccess
  class Session < ApplicationRecord
    self.table_name = "browser_sessions"
    TTL = 24.hours
    COOKIE_KEYS = { "staff" => :staff_session_id, "simulator" => :simulator_session_id }.freeze

    belongs_to :user, class_name: "Operations::User", optional: true

    scope :current, -> { where(revoked_at: nil).where("expires_at > ?", Time.current) }

    def self.resolve(cookie, audience)
      id = cookie[COOKIE_KEYS.fetch(audience)]
      current.find_by(id: id, audience: audience) if id
    end

    def self.start!(cookie, audience, user: nil)
      transaction do
        resolve(cookie, audience)&.revoke!
        create!(audience: audience, user: user, expires_at: TTL.from_now)
      end
    end

    def revoke!
      update!(revoked_at: Time.current)
    end

    def simulator_channels
      codes = ENV.fetch("CLOUDWALK_SIMULATOR_BRANDS", "aurora,horizonte").split(",").map(&:strip).reject(&:empty?)
      Operations::Channel.where(active: true, brand: Operations::Brand.where(code: codes))
    end

    def visible_cases
      if audience == "simulator"
        conversations = Attendances::ChannelConversation.where(simulator_session_id: id, channel: simulator_channels)
        Attendances::SupportCase.where(channel_conversation: conversations)
      else
        Attendances::Visibility.new(user).cases
      end
    end
  end
end
