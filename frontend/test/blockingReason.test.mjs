import assert from 'node:assert/strict'
import { test } from 'node:test'
import { blockingMessage } from '../src/staff/blockingReason.ts'

test('bloqueio em revisão informa a causa conhecida e a ação da supervisão', () => {
  assert.match(blockingMessage('invalid_input', 'classification_review', 'idle'), /catálogo.*supervisão/s)
  assert.match(blockingMessage('classifier_disabled', 'classification_review', 'idle'), /desativada.*revisar/s)
})

test('falha de entrega e causa futura têm orientação operacional sem expor o código', () => {
  assert.match(blockingMessage('agent_result_timeout', 'ai_active', 'failed'), /prazo.*tentar novamente/s)
  assert.match(blockingMessage('bridge_http_503', 'ai_active', 'failed'), /entrega.*encaminhar/s)
  const unknown = blockingMessage('future_code', 'waiting_human', 'idle')
  assert.match(unknown, /registro do caso/)
  assert.doesNotMatch(unknown, /future_code/)
})
