module AgentIntegration
  module Pilot
    class Nonce < ApplicationRecord
      self.table_name = "e01_nonces"
    end
  end
end
