class PrepareHumanService < ActiveRecord::Migration[8.1]
  def change
    add_reference :users, :switch_target_brand, type: :uuid, foreign_key: { to_table: :brands }
    add_column :users, :last_human_assignment_at, :datetime

    create_table :case_command_receipts, id: :uuid do |t|
      t.references :support_case, type: :uuid, null: false, foreign_key: true
      t.references :user, type: :uuid, null: false, foreign_key: true
      t.string :operation, null: false
      t.string :key, limit: 128, null: false
      t.string :body_sha256, null: false
      t.jsonb :response_body, null: false
      t.timestamps
    end
    add_index :case_command_receipts, %i[support_case_id user_id operation key], unique: true,
              name: "unique_case_command"

    create_table :analyst_operation_audits, id: :uuid do |t|
      t.references :user, type: :uuid, null: false, foreign_key: true
      t.string :event_type, null: false
      t.jsonb :changeset, null: false
      t.timestamps
    end
  end
end
