class PersistClassificationAttempts < ActiveRecord::Migration[8.1]
  def change
    create_table :classification_requests, id: :uuid do |t|
      t.references :support_case, type: :uuid, null: false, foreign_key: true, index: false
      t.integer :classification_version, null: false
      t.datetime :available_at, null: false
      t.datetime :completed_at
      t.timestamps
      t.index [:support_case_id, :classification_version], unique: true, name: "unique_classification_request"
      t.index :available_at, where: "completed_at IS NULL", name: "due_classification_requests"
    end

    create_table :classification_attempts, id: :uuid do |t|
      t.references :classification_request, type: :uuid, null: false, foreign_key: true, index: false
      t.integer :number, null: false
      t.datetime :finished_at
      t.string :disposition
      t.jsonb :issues, default: {}, null: false
      t.jsonb :evidence, default: {}, null: false
      t.timestamps
      t.index [:classification_request_id, :number], unique: true, name: "unique_classification_attempt"
    end

    reversible do |direction|
      direction.up do
        execute <<~SQL
          INSERT INTO classification_requests (support_case_id, classification_version, available_at, created_at, updated_at)
          SELECT id, classification_version, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
          FROM support_cases WHERE status = 'classification_pending'
          ON CONFLICT (support_case_id, classification_version) DO NOTHING
        SQL
      end
    end
  end
end
