class CloseAttemptsOfCompletedClassificationRequests < ActiveRecord::Migration[8.1]
  def up
    execute <<~SQL
      UPDATE classification_attempts AS attempt
      SET finished_at = request.completed_at,
          updated_at = CURRENT_TIMESTAMP,
          disposition = 'discarded',
          issues = attempt.issues || '{"provider":"request_already_completed"}'::jsonb
      FROM classification_requests AS request
      WHERE attempt.classification_request_id = request.id
        AND request.completed_at IS NOT NULL
        AND attempt.finished_at IS NULL
    SQL
  end

  def down
    # Preserva o desfecho já registrado para pedidos concluídos.
  end
end
