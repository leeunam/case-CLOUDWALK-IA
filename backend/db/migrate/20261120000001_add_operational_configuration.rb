class AddOperationalConfiguration < ActiveRecord::Migration[8.1]
  def change
    %i[brands teams support_queues].each do |table|
      add_column table, :version, :integer, null: false, default: 1
    end
    add_column :brands, :catalog_version, :integer, null: false, default: 1
    add_reference :teams, :orphaned_from_brand, type: :uuid, foreign_key: { to_table: :brands }

    create_table :routing_rules, id: :uuid do |t|
      t.references :brand, null: false, type: :uuid, foreign_key: true
      t.uuid :queue_id, null: false
      t.integer :position, null: false
      t.string :category
      t.string :priority
      t.boolean :active, null: false
      t.integer :version, null: false, default: 1
      t.timestamps
    end
    add_foreign_key :routing_rules, :support_queues, column: [:queue_id, :brand_id], primary_key: [:id, :brand_id]
    add_index :routing_rules, [:brand_id, :position], unique: true, where: "active"
    add_index :routing_rules, [:queue_id, :brand_id], where: "active"
    add_check_constraint :routing_rules, "position > 0 AND (category IS NOT NULL OR priority IS NOT NULL)",
                         name: "routing_rule_with_filter"

    create_table :configuration_audits, id: :uuid do |t|
      t.references :brand, null: false, type: :uuid, foreign_key: true, index: false
      t.references :actor, null: false, type: :uuid, foreign_key: { to_table: :users }
      t.uuid :correlation_id, null: false
      t.string :resource_type, null: false
      t.uuid :resource_id, null: false
      t.integer :version, null: false
      t.jsonb :before
      t.jsonb :after, null: false
      t.timestamps
    end
    add_index :configuration_audits, [:brand_id, :created_at, :id]
    add_index :configuration_audits, [:brand_id, :resource_type, :resource_id, :created_at, :id],
              name: "configuration_audits_by_resource"
  end
end
