module Operations
  class SupervisorBrand < ApplicationRecord
    belongs_to :user
    belongs_to :brand

    validates :brand_id, uniqueness: { scope: :user_id }
  end
end
