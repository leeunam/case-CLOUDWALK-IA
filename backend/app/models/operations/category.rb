module Operations
  class Category < ApplicationRecord
    belongs_to :brand

    validates :code, :name, presence: true
    validates :code, uniqueness: { scope: :brand_id }
    validate { errors.add(:code, "fora do catálogo ou reservado") unless Classification::Catalog.category_code?(code) }
  end
end
