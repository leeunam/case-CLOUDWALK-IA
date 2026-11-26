module AgentIntegration
  module E01
    class Pilot < ApplicationRecord
      self.table_name = "e01_pilots"
      ID = 1
      LIMIT_USD = BigDecimal("1")
      MAX_DISPATCHES = 24

      def self.lock_current!
        (find_by(id: ID) || create_or_find_by!(id: ID)).lock!
      end

      def allows?(reservation)
        dispatch_count < MAX_DISPATCHES && spent_usd + reservation <= LIMIT_USD
      end
    end
  end
end
