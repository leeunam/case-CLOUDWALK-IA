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

ActiveRecord::Schema[8.1].define(version: 2026_11_19_000003) do
  # These are extensions that must be enabled in order to support this database
  enable_extension "pg_catalog.plpgsql"

  create_table "agent_outboxes", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "agent_turn_id", null: false
    t.uuid "event_id", null: false
    t.text "body", null: false
    t.integer "attempts", null: false, default: 0
    t.datetime "next_attempt_at", null: false
    t.uuid "claim_token"
    t.datetime "published_at"
    t.datetime "failed_at"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["next_attempt_at"], name: "due_agent_outboxes", where: "published_at IS NULL AND failed_at IS NULL"
    t.index ["agent_turn_id"], name: "index_agent_outboxes_on_agent_turn_id", unique: true
    t.index ["event_id"], name: "index_agent_outboxes_on_event_id", unique: true
  end

  create_table "agent_receipts", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "event_id", null: false
    t.string "body_sha256", null: false
    t.string "disposition", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["event_id"], name: "index_agent_receipts_on_event_id", unique: true
  end

  create_table "agent_turns", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "support_case_id", null: false
    t.uuid "request_event_id", null: false
    t.uuid "result_event_id"
    t.integer "assignment_generation", null: false
    t.integer "through_sequence", null: false
    t.datetime "result_due_at"
    t.datetime "completed_at"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["request_event_id"], name: "index_agent_turns_on_request_event_id", unique: true
    t.index ["result_due_at"], name: "index_agent_turns_on_result_due_at", where: "completed_at IS NULL"
    t.index ["support_case_id"], name: "index_agent_turns_on_support_case_id"
    t.index ["support_case_id"], name: "one_in_flight_turn_per_case", unique: true, where: "completed_at IS NULL"
  end

  create_table "analyst_operation_audits", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.jsonb "changeset", null: false
    t.datetime "created_at", null: false
    t.string "event_type", null: false
    t.datetime "updated_at", null: false
    t.uuid "user_id", null: false
    t.index ["user_id"], name: "index_analyst_operation_audits_on_user_id"
  end

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

  create_table "case_audits", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "support_case_id"
    t.uuid "correlation_id", null: false
    t.string "event_type", null: false
    t.string "actor_type", null: false
    t.uuid "actor_id"
    t.string "from_status"
    t.string "to_status"
    t.string "reason"
    t.jsonb "details", null: false, default: {}
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["correlation_id", "created_at"], name: "index_case_audits_on_correlation_id_and_created_at"
    t.index ["support_case_id"], name: "index_case_audits_on_support_case_id"
  end

  create_table "case_command_receipts", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.string "body_sha256", null: false
    t.datetime "created_at", null: false
    t.string "key", limit: 128, null: false
    t.string "operation", null: false
    t.jsonb "response_body", null: false
    t.uuid "support_case_id", null: false
    t.datetime "updated_at", null: false
    t.uuid "user_id", null: false
    t.index ["support_case_id", "user_id", "operation", "key"], name: "unique_case_command", unique: true
    t.index ["support_case_id"], name: "index_case_command_receipts_on_support_case_id"
    t.index ["user_id"], name: "index_case_command_receipts_on_user_id"
  end

  create_table "case_messages", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "support_case_id", null: false
    t.integer "sequence", null: false
    t.string "author_type", null: false
    t.uuid "author_id", null: false
    t.string "source_event_id", null: false
    t.text "text", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["support_case_id"], name: "index_case_messages_on_support_case_id"
    t.index ["support_case_id", "sequence"], name: "index_case_messages_on_support_case_id_and_sequence", unique: true
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

  create_table "channel_conversations", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "channel_id", null: false
    t.string "external_conversation_id", null: false
    t.string "external_customer_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["channel_id"], name: "index_channel_conversations_on_channel_id"
    t.index ["channel_id", "external_conversation_id"], name: "unique_channel_conversation", unique: true
  end

  create_table "channel_entries", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "channel_id", null: false
    t.uuid "support_case_id", null: false
    t.string "source_event_id", null: false
    t.string "body_sha256", null: false
    t.text "body", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["channel_id"], name: "index_channel_entries_on_channel_id"
    t.index ["channel_id", "source_event_id"], name: "index_channel_entries_on_channel_id_and_source_event_id", unique: true
    t.index ["support_case_id"], name: "index_channel_entries_on_support_case_id"
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

  create_table "classification_attempts", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "classification_request_id", null: false
    t.integer "number", null: false
    t.datetime "finished_at"
    t.string "disposition"
    t.jsonb "issues", default: {}, null: false
    t.jsonb "evidence", default: {}, null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["classification_request_id", "number"], name: "unique_classification_attempt", unique: true
  end

  create_table "classification_requests", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "support_case_id", null: false
    t.integer "classification_version", null: false
    t.datetime "available_at", null: false
    t.datetime "completed_at"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["available_at"], name: "due_classification_requests", where: "(completed_at IS NULL)"
    t.index ["support_case_id", "classification_version"], name: "unique_classification_request", unique: true
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

  create_table "support_cases", id: :uuid, default: -> { "gen_random_uuid()" }, force: :cascade do |t|
    t.uuid "brand_id", null: false
    t.uuid "channel_id", null: false
    t.uuid "queue_id", null: false
    t.uuid "channel_conversation_id", null: false
    t.uuid "previous_case_id"
    t.uuid "assignee_id"
    t.uuid "correlation_id", null: false
    t.string "status", null: false
    t.string "integration_status", null: false, default: "idle"
    t.string "category"
    t.string "category_source"
    t.string "priority"
    t.string "priority_source"
    t.integer "classification_version", null: false, default: 1
    t.integer "version", null: false, default: 1
    t.integer "assignment_generation", null: false, default: 1
    t.datetime "human_queue_since"
    t.datetime "resolved_at"
    t.string "blocking_reason"
    t.jsonb "handoff"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["assignee_id"], name: "index_support_cases_on_assignee_id"
    t.index ["assignee_id", "status"], name: "index_support_cases_on_assignee_id_and_status"
    t.index ["brand_id"], name: "index_support_cases_on_brand_id"
    t.index ["channel_conversation_id"], name: "index_support_cases_on_channel_conversation_id"
    t.index ["correlation_id"], name: "index_support_cases_on_correlation_id", unique: true
    t.index ["previous_case_id"], name: "index_support_cases_on_previous_case_id"
    t.index ["channel_conversation_id"], name: "one_open_case_per_conversation", unique: true, where: "((status)::text <> 'resolved'::text)"
    t.index ["queue_id", "status", "human_queue_since"], name: "support_cases_queue_order"
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
    t.datetime "last_human_assignment_at"
    t.string "name", null: false
    t.string "role", null: false
    t.uuid "switch_target_brand_id"
    t.uuid "active_brand_id"
    t.boolean "available", default: false, null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["active_brand_id"], name: "index_users_on_active_brand_id"
    t.index ["email"], name: "index_users_on_email", unique: true
    t.index ["switch_target_brand_id"], name: "index_users_on_switch_target_brand_id"
    t.check_constraint "role::text = ANY (ARRAY['analyst'::character varying, 'supervisor'::character varying]::text[])", name: "user_role_allowed"
  end

  add_foreign_key "agent_outboxes", "agent_turns"
  add_foreign_key "agent_turns", "support_cases"
  add_foreign_key "analyst_operation_audits", "users"
  add_foreign_key "attendants", "users"
  add_foreign_key "brand_teams", "brands"
  add_foreign_key "brand_teams", "teams"
  add_foreign_key "capacity_profiles", "users"
  add_foreign_key "case_audits", "support_cases"
  add_foreign_key "case_command_receipts", "support_cases"
  add_foreign_key "case_command_receipts", "users"
  add_foreign_key "case_messages", "support_cases"
  add_foreign_key "categories", "brands"
  add_foreign_key "channel_conversations", "channels"
  add_foreign_key "channel_entries", "channels"
  add_foreign_key "channel_entries", "support_cases"
  add_foreign_key "channels", "brands"
  add_foreign_key "classification_attempts", "classification_requests"
  add_foreign_key "classification_requests", "support_cases"
  add_foreign_key "queue_teams", "brand_teams", column: ["brand_team_id", "brand_id"], primary_key: ["id", "brand_id"]
  add_foreign_key "queue_teams", "brands"
  add_foreign_key "queue_teams", "support_queues", column: ["support_queue_id", "brand_id"], primary_key: ["id", "brand_id"]
  add_foreign_key "supervisor_brands", "brands"
  add_foreign_key "supervisor_brands", "users"
  add_foreign_key "support_cases", "attendants", column: "assignee_id"
  add_foreign_key "support_cases", "brands"
  add_foreign_key "support_cases", "channel_conversations"
  add_foreign_key "support_cases", "channels", column: ["channel_id", "brand_id"], primary_key: ["id", "brand_id"]
  add_foreign_key "support_cases", "support_cases", column: "previous_case_id"
  add_foreign_key "support_cases", "support_queues", column: ["queue_id", "brand_id"], primary_key: ["id", "brand_id"]
  add_foreign_key "support_queues", "brands"
  add_foreign_key "team_memberships", "teams"
  add_foreign_key "team_memberships", "users"
  add_foreign_key "users", "brands", column: "active_brand_id"
  add_foreign_key "users", "brands", column: "switch_target_brand_id"
end
