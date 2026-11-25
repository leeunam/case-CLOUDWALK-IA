module Operations
  class Channel < ApplicationRecord
    belongs_to :brand
    has_many :conversations, class_name: "Attendances::ChannelConversation"

    validates :kind, inclusion: { in: %w[chat whatsapp email] },
                     uniqueness: { scope: :brand_id }
    validates :name, presence: true
  end
end
