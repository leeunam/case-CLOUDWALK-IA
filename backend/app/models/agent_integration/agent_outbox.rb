module AgentIntegration
  class AgentOutbox < ApplicationRecord
    belongs_to :agent_turn
  end
end
