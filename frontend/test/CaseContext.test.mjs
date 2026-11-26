import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { createServer } from 'vite'

test('contexto mostra origem de cada campo, histórico Jev e motivo da revisão', async () => {
  const server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom' })
  try {
    const { CaseContext } = await server.ssrLoadModule('/src/staff/CaseContext.tsx')
    function render(categorySource, prioritySource, reason = null) {
      const detail = {
        classification: { category: 'pix', category_source: categorySource,
          priority: prioritySource ? 'urgent' : null, priority_source: prioritySource },
        status: reason ? 'classification_review' : 'ai_active', integration_status: 'idle',
        blocking_reason: reason, created_at: '2026-11-26T10:00:00Z', updated_at: '2026-11-26T10:00:00Z',
      }
      return renderToStaticMarkup(createElement(CaseContext, { detail, owned: false, messages: [] }))
    }
    assert.match(render('channel', 'setfit'), /Pix<small>Origem · Canal.*Urgente<small>Origem · Classificador SetFit/s)
    assert.match(render('jev', 'supervisor'), /Pix<small>Origem · Classificador Jev.*Urgente<small>Origem · Supervisão/s)
    assert.doesNotMatch(render('channel', 'channel'), /SetFit|Jev/)
    const review = render('channel', null, 'text_out_of_scope')
    assert.match(review, /128 tokens.*supervisão precisa revisar/s)
    assert.match(review, /Sem prioridade<\/dd>/)
  } finally {
    await server.close()
  }
})
