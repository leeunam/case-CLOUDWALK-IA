class CreateOperations < ActiveRecord::Migration[8.1]
  def change
    create_table :brands, id: :uuid do |t|
      t.string :code, null: false
      t.string :name, null: false
      t.timestamps
    end
    add_index :brands, :code, unique: true

    create_table :teams, id: :uuid do |t|
      t.string :code, null: false
      t.string :name, null: false
      t.timestamps
    end
    add_index :teams, :code, unique: true

    create_table :brand_teams, id: :uuid do |t|
      t.references :brand, null: false, type: :uuid, foreign_key: true
      t.references :team, null: false, type: :uuid, foreign_key: true
      t.timestamps
    end
    add_index :brand_teams, [:brand_id, :team_id], unique: true
    add_index :brand_teams, [:id, :brand_id], unique: true

    create_table :support_queues, id: :uuid do |t|
      t.references :brand, null: false, type: :uuid, foreign_key: true
      t.string :code, null: false
      t.string :name, null: false
      t.boolean :active, null: false, default: true
      t.boolean :is_default, null: false, default: false
      t.timestamps
    end
    add_index :support_queues, [:brand_id, :code], unique: true
    add_index :support_queues, [:id, :brand_id], unique: true
    add_index :support_queues, :brand_id, unique: true, where: "is_default",
              name: "one_default_queue_per_brand"
    add_check_constraint :support_queues, "NOT is_default OR active",
                         name: "default_queue_must_be_active"

    create_table :queue_teams, id: :uuid do |t|
      t.references :brand, null: false, type: :uuid, foreign_key: true
      t.uuid :support_queue_id, null: false
      t.uuid :brand_team_id, null: false
      t.timestamps
    end
    add_index :queue_teams, [:support_queue_id, :brand_team_id], unique: true
    add_foreign_key :queue_teams, :support_queues,
                    column: [:support_queue_id, :brand_id], primary_key: [:id, :brand_id]
    add_foreign_key :queue_teams, :brand_teams,
                    column: [:brand_team_id, :brand_id], primary_key: [:id, :brand_id]

    create_table :channels, id: :uuid do |t|
      t.references :brand, null: false, type: :uuid, foreign_key: true
      t.string :kind, null: false
      t.string :name, null: false
      t.boolean :active, null: false, default: true
      t.timestamps
    end
    add_index :channels, [:brand_id, :kind], unique: true
    add_index :channels, [:id, :brand_id], unique: true
    add_check_constraint :channels, "kind IN ('chat', 'whatsapp', 'email')",
                         name: "channel_kind_allowed"

    create_table :categories, id: :uuid do |t|
      t.references :brand, null: false, type: :uuid, foreign_key: true
      t.string :code, null: false
      t.string :name, null: false
      t.boolean :active, null: false, default: true
      t.timestamps
    end
    add_index :categories, [:brand_id, :code], unique: true

    create_table :users, id: :uuid do |t|
      t.string :email, null: false
      t.string :name, null: false
      t.string :role, null: false
      t.references :active_brand, type: :uuid, foreign_key: { to_table: :brands }
      t.boolean :available, null: false, default: false
      t.timestamps
    end
    add_index :users, :email, unique: true
    add_check_constraint :users, "role IN ('analyst', 'supervisor')",
                         name: "user_role_allowed"

    create_table :team_memberships, id: :uuid do |t|
      t.references :user, null: false, type: :uuid, foreign_key: true
      t.references :team, null: false, type: :uuid, foreign_key: true
      t.timestamps
    end
    add_index :team_memberships, [:user_id, :team_id], unique: true

    create_table :supervisor_brands, id: :uuid do |t|
      t.references :user, null: false, type: :uuid, foreign_key: true
      t.references :brand, null: false, type: :uuid, foreign_key: true
      t.timestamps
    end
    add_index :supervisor_brands, [:user_id, :brand_id], unique: true

    create_table :attendants, id: :uuid do |t|
      t.string :code, null: false
      t.string :kind, null: false
      t.references :user, type: :uuid, foreign_key: true, index: { unique: true }
      t.timestamps
    end
    add_index :attendants, :code, unique: true
    add_check_constraint :attendants,
                         "(kind = 'human' AND user_id IS NOT NULL) OR (kind = 'ai' AND user_id IS NULL)",
                         name: "attendant_matches_identity"

    create_table :capacity_profiles, id: :uuid do |t|
      t.references :user, null: false, type: :uuid, foreign_key: true
      t.integer :version, null: false
      t.integer :portfolio_limit, null: false
      t.jsonb :alternatives, null: false, default: []
      t.boolean :active, null: false, default: true
      t.timestamps
    end
    add_index :capacity_profiles, [:user_id, :version], unique: true
    add_index :capacity_profiles, :user_id, unique: true, where: "active",
              name: "one_active_capacity_profile_per_user"
    add_check_constraint :capacity_profiles, "version > 0 AND portfolio_limit > 0",
                         name: "capacity_profile_positive_limits"
  end
end
