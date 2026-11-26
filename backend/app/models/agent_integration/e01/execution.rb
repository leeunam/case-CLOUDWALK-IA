module AgentIntegration
  module E01
    class Execution < ApplicationRecord
      self.table_name = "e01_executions"
      self.filter_attributes += %i[lease_token result_bytes]

      scope :holding_slot, -> { where(state: %w[reserved started unknown]) }
      scope :expirable, -> { where(state: %w[reserved started]) }

      attr_readonly :request_event_id, :request_sha256, :snapshot, :reserved_usd
    end
  end
end
