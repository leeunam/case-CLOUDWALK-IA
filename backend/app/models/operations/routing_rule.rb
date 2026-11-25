module Operations
  class RoutingRule < ApplicationRecord
    belongs_to :brand
    belongs_to :queue, class_name: "Operations::SupportQueue"

    def contract_data
      as_json(only: %i[id brand_id queue_id position category priority active version]).symbolize_keys
    end
  end
end
