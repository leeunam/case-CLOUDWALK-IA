module Operations
  class Brand < ApplicationRecord
    has_many :brand_teams
    has_many :teams, through: :brand_teams
    has_many :support_queues
    has_many :channels
    has_many :categories

    validates :code, :name, presence: true
    validates :code, uniqueness: true
  end
end
