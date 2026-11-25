module Attendances
  class CaseCommandReceipt < ApplicationRecord
    belongs_to :support_case
    belongs_to :user, class_name: "Operations::User"
  end
end
