module Operations
  class Attendant < ApplicationRecord
    belongs_to :user, optional: true

    validates :code, presence: true, uniqueness: true
    validates :kind, inclusion: { in: %w[ai human] }
    validates :user, presence: true, if: -> { kind == "human" }
    validates :user, absence: true, if: -> { kind == "ai" }
  end
end
