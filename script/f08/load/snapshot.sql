SELECT c.id AS case_id, c.channel_id, c.brand_id, b.code AS brand, ch.kind,
       c.correlation_id, c.status, c.integration_status, c.blocking_reason, c.assignee_id, c.version,
       conv.external_conversation_id,
       extract(epoch FROM c.resolved_at AT TIME ZONE 'UTC') * 1000 AS resolved_ms,
       (SELECT jsonb_agg(jsonb_build_object('id', e.id, 'source_event_id', e.source_event_id,
         'sha256', e.body_sha256) ORDER BY e.created_at, e.id)
         FROM channel_entries e WHERE e.support_case_id = c.id) AS entries,
       (SELECT jsonb_agg(jsonb_build_object('id', m.id, 'sequence', m.sequence, 'author', m.author_type,
         'source_event_id', m.source_event_id, 'created_ms',
         extract(epoch FROM m.created_at AT TIME ZONE 'UTC') * 1000) ORDER BY m.sequence)
         FROM case_messages m WHERE m.support_case_id = c.id) AS messages,
       (SELECT jsonb_agg(jsonb_build_object('id', t.id, 'through_sequence', t.through_sequence,
         'generation', t.assignment_generation, 'request_event_id', t.request_event_id,
         'result_event_id', t.result_event_id, 'disposition', r.disposition,
         'completed_ms', extract(epoch FROM t.completed_at AT TIME ZONE 'UTC') * 1000,
         'outbox_event_id', o.event_id, 'attempts', o.attempts,
         'published_ms', extract(epoch FROM o.published_at AT TIME ZONE 'UTC') * 1000,
         'failed_ms', extract(epoch FROM o.failed_at AT TIME ZONE 'UTC') * 1000) ORDER BY t.created_at, t.id)
         FROM agent_turns t LEFT JOIN agent_outboxes o ON o.agent_turn_id = t.id
         LEFT JOIN agent_receipts r ON r.event_id = t.result_event_id WHERE t.support_case_id = c.id) AS turns,
       (SELECT jsonb_agg(jsonb_build_object('id', a.id, 'type', a.event_type, 'reason', a.reason,
         'event_id', a.details->>'event_id', 'turn_id', a.details->>'turn_id',
         'source_event_id', a.details->>'source_event_id', 'message_id', a.details->>'message_id',
         'at_ms', extract(epoch FROM a.created_at AT TIME ZONE 'UTC') * 1000) ORDER BY a.created_at, a.id)
         FROM case_audits a WHERE a.support_case_id = c.id) AS audits
FROM support_cases c JOIN channel_conversations conv ON conv.id = c.channel_conversation_id
JOIN channels ch ON ch.id = c.channel_id JOIN brands b ON b.id = c.brand_id
WHERE c.id <> %s
ORDER BY c.created_at, c.id
