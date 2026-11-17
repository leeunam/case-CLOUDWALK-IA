module Operations
  class Channel < ApplicationRecord
    belongs_to :brand

    validates :kind, inclusion: { in: %w[chat whatsapp email] },
                     uniqueness: { scope: :brand_id }
    validates :name, presence: true
  end
end
