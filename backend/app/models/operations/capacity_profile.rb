module Operations
  class CapacityProfile < ApplicationRecord
    belongs_to :user

    validates :version, numericality: { only_integer: true, greater_than: 0 },
                        uniqueness: { scope: :user_id }
    validates :portfolio_limit, numericality: { only_integer: true, greater_than: 0 }
    validates :alternatives, presence: true
  end
end
