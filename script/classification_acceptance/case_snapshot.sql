-- Um atendimento do ensaio. Somente identificadores, decisões e tempos.
SELECT json_build_object(
  'case_id', c.id, 'correlation_id', c.correlation_id, 'brand', b.code, 'channel', ch.kind,
  'status', c.status, 'queue_id', c.queue_id, 'queue', q.code,
  'category', c.category, 'priority', c.priority, 'category_source', c.category_source,
  'priority_source', c.priority_source, 'classification_version', c.classification_version,
  'entry', (SELECT json_build_object('source_event_id',e.source_event_id,'sha256',e.body_sha256)
    FROM channel_entries e WHERE e.support_case_id=c.id ORDER BY e.created_at LIMIT 1),
  'requests', (SELECT count(*) FROM classification_requests WHERE support_case_id=c.id),
  'attempts', coalesce((SELECT json_agg(json_build_object('id',a.id,'number',a.number,
    'disposition',a.disposition,'provider',r.provider,'provider_mode',r.provider_mode,
    'queue_ms',round(extract(epoch FROM a.created_at-r.created_at)*1000,3),
    'http_ms',a.evidence->'client_elapsed_ms','sidecar_ms',a.evidence->'elapsed_ms',
    'raw_frame_sha256',a.evidence->'raw_frame_sha256','package_sha256',a.evidence->'package_sha256',
    'calls',a.evidence->'calls','received',a.snapshot->'received','applied',a.evidence->'applied',
    'outcome',a.evidence->'outcome','issues',a.issues,'catalog_version',a.snapshot->'catalog_version',
    'catalog_sha256',a.snapshot->'catalog_sha256') ORDER BY a.number)
    FROM classification_requests r JOIN classification_attempts a ON a.classification_request_id=r.id
    WHERE r.support_case_id=c.id),'[]'::json),
  'turns',coalesce((SELECT json_agg(json_build_object('id',t.id,'request_id',t.request_event_id,
    'result_id',t.result_event_id,'outbox_id',o.id,'deliveries',o.attempts,'request_version',o.body::json->'schema_version',
    'turn_to_result_ms',round(extract(epoch FROM t.completed_at-t.created_at)*1000,3),
    'case_to_result_ms',round(extract(epoch FROM t.completed_at-c.created_at)*1000,3),
    'outbox_published',o.published_at IS NOT NULL))
    FROM agent_turns t JOIN agent_outboxes o ON o.agent_turn_id=t.id WHERE t.support_case_id=c.id),'[]'::json),
  'messages',(SELECT json_agg(json_build_object('id',id,'author',author_type,'sequence',sequence)
    ORDER BY sequence) FROM case_messages WHERE support_case_id=c.id),
  'audit',(SELECT json_agg(json_build_object('type',event_type,'id',id,'attempt_id',details->'attempt_id',
    'rule_id',details->'rule_id','rule_version',details->'rule_version','queue_id',details->'queue_id')
    ORDER BY created_at) FROM case_audits WHERE support_case_id=c.id)
) FROM support_cases c JOIN brands b ON b.id=c.brand_id JOIN channels ch ON ch.id=c.channel_id
  JOIN support_queues q ON q.id=c.queue_id WHERE c.id=:'case_id'::uuid;
