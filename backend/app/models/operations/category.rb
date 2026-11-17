module Operations
  class Category < ApplicationRecord
    belongs_to :brand

    validates :code, :name, presence: true
    validates :code, uniqueness: { scope: :brand_id }
  end
end
