class AddBrowserSessions < ActiveRecord::Migration[8.1]
  def change
    create_table :browser_sessions, id: :uuid do |t|
      t.references :user, type: :uuid, foreign_key: { on_delete: :cascade }
      t.string :audience, null: false
      t.datetime :expires_at, null: false
      t.datetime :revoked_at
      t.timestamps
    end
    add_check_constraint :browser_sessions,
                         "(audience = 'staff' AND user_id IS NOT NULL) OR (audience = 'simulator' AND user_id IS NULL)",
                         name: "browser_session_audience_owner"
    add_reference :channel_conversations, :simulator_session, type: :uuid,
                  foreign_key: { to_table: :browser_sessions }
  end
end
