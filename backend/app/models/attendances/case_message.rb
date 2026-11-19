module Attendances
  class CaseMessage < ApplicationRecord
    belongs_to :support_case

    def contract_data
      { id: id, sequence: sequence, author: { type: author_type, id: author_id },
        text: text, created_at: created_at.iso8601(6) }
    end
  end
end
