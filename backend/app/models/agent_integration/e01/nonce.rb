module AgentIntegration
  module E01
    class Nonce < ApplicationRecord
      self.table_name = "e01_nonces"
    end
  end
end
