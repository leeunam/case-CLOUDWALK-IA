# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[8.1].define(version: 2026_11_17_000001) do
  # These are extensions that must be enabled in order to support this database
  enable_extension "pg_catalog.plpgsql"

  create_table "attendants", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.string "code", null: false
    t.string "kind", null: false
    t.uuid "user_id"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["code"], name: "index_attendants_on_code", unique: true
    t.index ["user_id"], name: "index_attendants_on_user_id", unique: true
    t.check_constraint "kind::text = 'human'::text AND user_id IS NOT NULL OR kind::text = 'ai'::text AND user_id IS NULL", name: "attendant_matches_identity"
  end

  create_table "brand_teams", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "brand_id", null: false
    t.uuid "team_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["brand_id", "team_id"], name: "index_brand_teams_on_brand_id_and_team_id", unique: true
    t.index ["brand_id"], name: "index_brand_teams_on_brand_id"
    t.index ["id", "brand_id"], name: "index_brand_teams_on_id_and_brand_id", unique: true
    t.index ["team_id"], name: "index_brand_teams_on_team_id"
  end

  create_table "brands", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.string "code", null: false
    t.string "name", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["code"], name: "index_brands_on_code", unique: true
  end

  create_table "capacity_profiles", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "user_id", null: false
    t.integer "version", null: false
    t.integer "portfolio_limit", null: false
    t.jsonb "alternatives", default: [], null: false
    t.boolean "active", default: true, null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["user_id", "version"], name: "index_capacity_profiles_on_user_id_and_version", unique: true
    t.index ["user_id"], name: "index_capacity_profiles_on_user_id"
    t.index ["user_id"], name: "one_active_capacity_profile_per_user", unique: true, where: "active"
    t.check_constraint "version > 0 AND portfolio_limit > 0", name: "capacity_profile_positive_limits"
  end

  create_table "categories", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "brand_id", null: false
    t.string "code", null: false
    t.string "name", null: false
    t.boolean "active", default: true, null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["brand_id", "code"], name: "index_categories_on_brand_id_and_code", unique: true
    t.index ["brand_id"], name: "index_categories_on_brand_id"
  end

  create_table "channels", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "brand_id", null: false
    t.string "kind", null: false
    t.string "name", null: false
    t.boolean "active", default: true, null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["brand_id", "kind"], name: "index_channels_on_brand_id_and_kind", unique: true
    t.index ["brand_id"], name: "index_channels_on_brand_id"
    t.index ["id", "brand_id"], name: "index_channels_on_id_and_brand_id", unique: true
    t.check_constraint "kind::text = ANY (ARRAY['chat'::character varying, 'whatsapp'::character varying, 'email'::character varying]::text[])", name: "channel_kind_allowed"
  end

  create_table "queue_teams", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "brand_id", null: false
    t.uuid "support_queue_id", null: false
    t.uuid "brand_team_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["brand_id"], name: "index_queue_teams_on_brand_id"
    t.index ["support_queue_id", "brand_team_id"], name: "index_queue_teams_on_support_queue_id_and_brand_team_id", unique: true
  end

  create_table "supervisor_brands", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "user_id", null: false
    t.uuid "brand_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["brand_id"], name: "index_supervisor_brands_on_brand_id"
    t.index ["user_id", "brand_id"], name: "index_supervisor_brands_on_user_id_and_brand_id", unique: true
    t.index ["user_id"], name: "index_supervisor_brands_on_user_id"
  end

  create_table "support_queues", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "brand_id", null: false
    t.string "code", null: false
    t.string "name", null: false
    t.boolean "active", default: true, null: false
    t.boolean "is_default", default: false, null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["brand_id", "code"], name: "index_support_queues_on_brand_id_and_code", unique: true
    t.index ["brand_id"], name: "index_support_queues_on_brand_id"
    t.index ["brand_id"], name: "one_default_queue_per_brand", unique: true, where: "is_default"
    t.index ["id", "brand_id"], name: "index_support_queues_on_id_and_brand_id", unique: true
    t.check_constraint "NOT is_default OR active", name: "default_queue_must_be_active"
  end

  create_table "team_memberships", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "user_id", null: false
    t.uuid "team_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["team_id"], name: "index_team_memberships_on_team_id"
    t.index ["user_id", "team_id"], name: "index_team_memberships_on_user_id_and_team_id", unique: true
    t.index ["user_id"], name: "index_team_memberships_on_user_id"
  end

  create_table "teams", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.string "code", null: false
    t.string "name", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["code"], name: "index_teams_on_code", unique: true
  end

  create_table "users", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.string "email", null: false
    t.string "name", null: false
    t.string "role", null: false
    t.uuid "active_brand_id"
    t.boolean "available", default: false, null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["active_brand_id"], name: "index_users_on_active_brand_id"
    t.index ["email"], name: "index_users_on_email", unique: true
    t.check_constraint "role::text = ANY (ARRAY['analyst'::character varying, 'supervisor'::character varying]::text[])", name: "user_role_allowed"
  end

  add_foreign_key "attendants", "users"
  add_foreign_key "brand_teams", "brands"
  add_foreign_key "brand_teams", "teams"
  add_foreign_key "capacity_profiles", "users"
  add_foreign_key "categories", "brands"
  add_foreign_key "channels", "brands"
  add_foreign_key "queue_teams", "brand_teams", column: ["brand_team_id", "brand_id"], primary_key: ["id", "brand_id"]
  add_foreign_key "queue_teams", "brands"
  add_foreign_key "queue_teams", "support_queues", column: ["support_queue_id", "brand_id"], primary_key: ["id", "brand_id"]
  add_foreign_key "supervisor_brands", "brands"
  add_foreign_key "supervisor_brands", "users"
  add_foreign_key "support_queues", "brands"
  add_foreign_key "team_memberships", "teams"
  add_foreign_key "team_memberships", "users"
  add_foreign_key "users", "brands", column: "active_brand_id"
end
