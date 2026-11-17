module Operations
  class QueueTeam < ApplicationRecord
    belongs_to :brand
    belongs_to :support_queue
    belongs_to :brand_team

    validates :brand_team_id, uniqueness: { scope: :support_queue_id }
    validate :same_brand

    private

    def same_brand
      return if support_queue&.brand_id == brand_id && brand_team&.brand_id == brand_id

      errors.add(:brand, "deve ser a mesma da fila e da equipe autorizada")
    end
  end
end
