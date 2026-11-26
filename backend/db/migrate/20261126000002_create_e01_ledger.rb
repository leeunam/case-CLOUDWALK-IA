class CreateE01Ledger < ActiveRecord::Migration[8.1]
  def change
    create_table :e01_pilots do |t|
      t.decimal :spent_usd, precision: 13, scale: 12, null: false, default: 0
      t.integer :dispatch_count, null: false, default: 0
      t.check_constraint "id = 1 AND spent_usd BETWEEN 0 AND 1 AND dispatch_count BETWEEN 0 AND 24",
                         name: "e01_pilot_limits"
    end

    create_table :e01_executions do |t|
      t.uuid :request_event_id, null: false
      t.string :request_sha256, null: false
      t.references :pilot, null: false, default: 1, foreign_key: { to_table: :e01_pilots }, index: false
      t.string :state, null: false
      t.uuid :owner_id, null: false
      t.uuid :lease_token, null: false
      t.datetime :lease_expires_at, null: false
      t.datetime :started_at
      t.decimal :reserved_usd, precision: 13, scale: 12, null: false
      t.decimal :cost_usd, precision: 13, scale: 12
      t.jsonb :snapshot, null: false
      t.jsonb :usage
      t.jsonb :result_metadata
      t.binary :result_bytes
      t.string :result_sha256
      t.string :complete_sha256
      t.string :reason
      t.datetime :published_at
      t.timestamps
      t.check_constraint "state IN ('reserved', 'expired', 'started', 'unknown', 'result_saved', 'published', 'failed', 'discarded')",
                         name: "e01_execution_state"
      t.check_constraint "reserved_usd > 0 AND reserved_usd <= 1 AND (cost_usd BETWEEN 0 AND reserved_usd OR cost_usd IS NULL)",
                         name: "e01_execution_cost"
      t.index :request_event_id, unique: true
      t.index :pilot_id, unique: true, where: "state IN ('reserved', 'started', 'unknown')",
              name: "one_e01_dispatch_slot"
      t.index :lease_expires_at, where: "state IN ('reserved', 'started')", name: "due_e01_execution_leases"
    end
    add_foreign_key :e01_executions, :agent_outboxes, column: :request_event_id, primary_key: :event_id

    create_table :e01_nonces, id: false, primary_key: :id do |t|
      t.primary_key :id, :uuid
      t.datetime :expires_at, null: false
      t.index :expires_at
    end
  end
end
