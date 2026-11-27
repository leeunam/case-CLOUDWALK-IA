SELECT
  extract(epoch FROM clock_timestamp()) * 1000 AS db_clock_ms,
  (SELECT count(*) FROM agent_outboxes WHERE published_at IS NULL AND failed_at IS NULL) AS outbox_pending,
  (SELECT count(*) FROM agent_outboxes WHERE failed_at IS NOT NULL) AS outbox_failed,
  (SELECT count(*) FROM support_cases WHERE integration_status IN ('pending_delivery', 'awaiting_result'))
    AS cases_waiting_processing,
  (SELECT count(*) FROM support_cases WHERE integration_status = 'failed') AS cases_failed,
  (SELECT count(*) FROM support_cases WHERE status = 'waiting_human') AS cases_waiting_human,
  (SELECT count(*) FROM support_cases WHERE status = 'human_active') AS cases_human_active,
  (SELECT count(*) FROM support_cases WHERE status = 'waiting_customer') AS cases_waiting_customer,
  (SELECT count(*) FROM support_cases WHERE status = 'resolved') AS cases_resolved,
  (SELECT count(*) FROM classification_requests) AS classification_requests,
  (SELECT count(*) FROM classification_attempts) AS classification_attempts,
  (SELECT jsonb_object_agg(datname, states) FROM (
    SELECT datname, jsonb_object_agg(state, total) AS states FROM (
      SELECT datname, coalesce(state, 'unknown') AS state, count(*) AS total
      FROM pg_stat_activity WHERE backend_type = 'client backend' AND datname IS NOT NULL
      GROUP BY 1, 2
    ) s GROUP BY datname
  ) clients) AS db_client_connections
