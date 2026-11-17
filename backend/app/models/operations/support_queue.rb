module Operations
  class SupportQueue < ApplicationRecord
    belongs_to :brand
    has_many :queue_teams
    has_many :brand_teams, through: :queue_teams

    validates :code, :name, presence: true
    validates :code, uniqueness: { scope: :brand_id }
  end
end
