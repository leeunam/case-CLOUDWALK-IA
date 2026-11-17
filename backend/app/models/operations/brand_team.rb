module Operations
  class BrandTeam < ApplicationRecord
    belongs_to :brand
    belongs_to :team

    validates :team_id, uniqueness: { scope: :brand_id }
  end
end
