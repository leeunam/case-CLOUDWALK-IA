class SeparateSimulatorBodyDigest < ActiveRecord::Migration[8.1]
  def up
    add_column :channel_entries, :simulator_body_sha256, :string
    execute <<~SQL
      UPDATE channel_entries AS entry
      SET simulator_body_sha256 = entry.body_sha256,
          body_sha256 = encode(sha256(convert_to(entry.body, 'UTF8')), 'hex')
      FROM support_cases AS attendance
      JOIN channel_conversations AS conversation ON conversation.id = attendance.channel_conversation_id
      WHERE attendance.id = entry.support_case_id
        AND conversation.simulator_session_id IS NOT NULL
        AND entry.body_sha256 <> encode(sha256(convert_to(entry.body, 'UTF8')), 'hex')
    SQL
  end

  def down
    execute <<~SQL
      UPDATE channel_entries
      SET body_sha256 = simulator_body_sha256
      WHERE simulator_body_sha256 IS NOT NULL
    SQL
    remove_column :channel_entries, :simulator_body_sha256
  end
end
