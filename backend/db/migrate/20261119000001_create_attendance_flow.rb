class CreateAttendanceFlow < ActiveRecord::Migration[8.1]
  def change
    create_table :channel_conversations, id: :uuid do |t|
      t.references :channel, type: :uuid, null: false, foreign_key: true
      t.string :external_conversation_id, null: false
      t.string :external_customer_id, null: false
      t.timestamps
    end
    add_index :channel_conversations, [:channel_id, :external_conversation_id], unique: true,
              name: "unique_channel_conversation"

    create_table :support_cases, id: :uuid do |t|
      t.references :brand, type: :uuid, null: false, foreign_key: true
      t.uuid :channel_id, null: false
      t.uuid :queue_id, null: false
      t.references :channel_conversation, type: :uuid, null: false, foreign_key: true
      t.references :previous_case, type: :uuid, foreign_key: { to_table: :support_cases }
      t.references :assignee, type: :uuid, foreign_key: { to_table: :attendants }
      t.uuid :correlation_id, null: false
      t.string :status, null: false
      t.string :integration_status, null: false, default: "idle"
      t.string :category
      t.string :category_source
      t.string :priority
      t.string :priority_source
      t.integer :classification_version, null: false, default: 1
      t.integer :version, null: false, default: 1
      t.integer :assignment_generation, null: false, default: 1
      t.datetime :human_queue_since
      t.datetime :resolved_at
      t.string :blocking_reason
      t.jsonb :handoff
      t.timestamps
    end
    add_foreign_key :support_cases, :channels, column: [:channel_id, :brand_id], primary_key: [:id, :brand_id]
    add_foreign_key :support_cases, :support_queues, column: [:queue_id, :brand_id], primary_key: [:id, :brand_id]
    add_index :support_cases, :correlation_id, unique: true
    add_index :support_cases, :channel_conversation_id, unique: true, where: "status <> 'resolved'",
              name: "one_open_case_per_conversation"
    add_index :support_cases, [:queue_id, :status, :human_queue_since], name: "support_cases_queue_order"
    add_index :support_cases, [:assignee_id, :status]

    create_table :channel_entries, id: :uuid do |t|
      t.references :channel, type: :uuid, null: false, foreign_key: true
      t.references :support_case, type: :uuid, null: false, foreign_key: true
      t.string :source_event_id, null: false
      t.string :body_sha256, null: false
      t.text :body, null: false
      t.timestamps
    end
    add_index :channel_entries, [:channel_id, :source_event_id], unique: true

    create_table :case_messages, id: :uuid do |t|
      t.references :support_case, type: :uuid, null: false, foreign_key: true
      t.integer :sequence, null: false
      t.string :author_type, null: false
      t.uuid :author_id, null: false
      t.string :source_event_id, null: false
      t.text :text, null: false
      t.timestamps
    end
    add_index :case_messages, [:support_case_id, :sequence], unique: true

    create_table :agent_turns, id: :uuid do |t|
      t.references :support_case, type: :uuid, null: false, foreign_key: true
      t.uuid :request_event_id, null: false
      t.uuid :result_event_id
      t.integer :assignment_generation, null: false
      t.integer :through_sequence, null: false
      t.datetime :result_due_at
      t.datetime :completed_at
      t.timestamps
    end
    add_index :agent_turns, :request_event_id, unique: true
    add_index :agent_turns, :support_case_id, unique: true, where: "completed_at IS NULL",
              name: "one_in_flight_turn_per_case"
    add_index :agent_turns, :result_due_at, where: "completed_at IS NULL"

    create_table :agent_outboxes, id: :uuid do |t|
      t.references :agent_turn, type: :uuid, null: false, foreign_key: true, index: { unique: true }
      t.uuid :event_id, null: false
      t.text :body, null: false
      t.integer :attempts, null: false, default: 0
      t.datetime :next_attempt_at, null: false
      t.uuid :claim_token
      t.datetime :published_at
      t.datetime :failed_at
      t.timestamps
    end
    add_index :agent_outboxes, :event_id, unique: true
    add_index :agent_outboxes, :next_attempt_at, where: "published_at IS NULL AND failed_at IS NULL",
              name: "due_agent_outboxes"

    create_table :agent_receipts, id: :uuid do |t|
      t.uuid :event_id, null: false
      t.string :body_sha256, null: false
      t.string :disposition, null: false
      t.timestamps
    end
    add_index :agent_receipts, :event_id, unique: true

    create_table :case_audits, id: :uuid do |t|
      t.references :support_case, type: :uuid, foreign_key: true
      t.uuid :correlation_id, null: false
      t.string :event_type, null: false
      t.string :actor_type, null: false
      t.uuid :actor_id
      t.string :from_status
      t.string :to_status
      t.string :reason
      t.jsonb :details, null: false, default: {}
      t.timestamps
    end
    add_index :case_audits, [:correlation_id, :created_at]
  end
end
