module Operations
  class Team < ApplicationRecord
    has_many :brand_teams
    has_many :brands, through: :brand_teams
    has_many :team_memberships
    has_many :users, through: :team_memberships

    validates :code, :name, presence: true
    validates :code, uniqueness: true
  end
end
