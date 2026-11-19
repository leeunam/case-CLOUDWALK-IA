module Attendances
  class ChannelConversation < ApplicationRecord
    belongs_to :channel, class_name: "Operations::Channel"
    has_many :support_cases
  end
end
