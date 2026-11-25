module Attendances
  class ChannelEntry < ApplicationRecord
    belongs_to :support_case
  end
end
