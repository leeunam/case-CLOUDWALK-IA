module Attendances
  class CaseAudit < ApplicationRecord
    belongs_to :support_case, optional: true
  end
end
