module Operations
  class CapacityProfile < ApplicationRecord
    belongs_to :user

    validates :version, numericality: { only_integer: true, greater_than: 0 },
                        uniqueness: { scope: :user_id }
    validates :portfolio_limit, numericality: { only_integer: true, greater_than: 0 }
    validates :alternatives, presence: true

    def fits?(counts)
      alternatives.any? do |alternative|
        limits = alternative.to_h do |pair|
          [[pair.fetch("priority"), pair.fetch("category")], pair.fetch("limit")]
        end
        counts.all? { |pair, count| count <= limits.fetch(pair, 0) }
      end
    end
  end
end
