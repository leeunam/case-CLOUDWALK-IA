module Classification
  class Attempt < ApplicationRecord
    self.table_name = "classification_attempts"

    belongs_to :request, class_name: "Classification::Request", foreign_key: :classification_request_id
  end
end
