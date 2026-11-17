module Operations
  class User < ApplicationRecord
    belongs_to :active_brand, class_name: "Operations::Brand", optional: true
    has_many :team_memberships
    has_many :teams, through: :team_memberships
    has_many :capacity_profiles

    validates :name, :email, presence: true
    validates :email, uniqueness: true
    validates :role, inclusion: { in: %w[analyst supervisor] }
  end
end
