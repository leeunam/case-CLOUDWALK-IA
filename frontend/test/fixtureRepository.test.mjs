import assert from 'node:assert/strict'
import test from 'node:test'
import { createFixtureRepository } from '../src/simulator/fixtureRepository.ts'

const storageKey = 'cloudwalk.simulator.v1.empty'
const accessDelay = 320
const classification = { category: 'pix', priority: 'basic' }

function simulateBrowser(context) {
  const storage = new Map()
  const connection = { onLine: true }
  const previousNavigator = Object.getOwnPropertyDescriptor(globalThis, 'navigator')
  let now = Date.parse('2026-11-19T12:00:00Z')

  Object.defineProperty(globalThis, 'navigator', { configurable: true, value: connection })
  globalThis.window = {
    localStorage: {
      getItem: key => storage.get(key) ?? null,
      setItem: (key, value) => storage.set(key, value),
    },
    setTimeout: (callback, delay) => {
      now += delay
      callback()
    },
  }
  context.mock.method(Date, 'now', () => now)
  context.after(() => {
    delete globalThis.window
    Object.defineProperty(globalThis, 'navigator', previousNavigator)
  })

  return {
    storage,
    connection,
    beforeReadAt: time => { now = time - accessDelay },
  }
}

async function openConversation(repository, type) {
  const { items } = await repository.listChannels()
  const channel = items.find(item => item.type === type)
  const receipt = await repository.sendMessage(channel.id, { text: 'Relato inicial', ...classification }, 'inicio')
  return { receipt, openedAt: Date.now() }
}

function sendFollowUp(repository, receipt, text, key = text) {
  return repository.sendMessage(receipt.channel_id, {
    text,
    external_conversation_id: receipt.external_conversation_id,
  }, key)
}

const authors = snapshot => snapshot.messages.map(message => message.author.type)
const endingMessage = 'Recebi o complemento. Vou encerrar este atendimento simulado.'

for (const [type, responseDelay] of [['chat', 1000], ['whatsapp', 3500], ['email', 3500]]) {
  test(`agrupa os complementos na próxima rodada e lê o encerramento em conjunto (${type})`, async context => {
    const browser = simulateBrowser(context)
    const repository = createFixtureRepository('empty')
    const { receipt, openedAt } = await openConversation(repository, type)
    assert.deepEqual(await sendFollowUp(repository, receipt, 'Primeiro complemento'), receipt)
    assert.deepEqual(await sendFollowUp(repository, receipt, 'Segundo complemento'), receipt)

    browser.beforeReadAt(openedAt + responseDelay - 1)
    const beforeReply = await repository.getConversation(receipt.case_id)
    assert.deepEqual(authors(beforeReply), ['customer', 'customer', 'customer'])

    browser.beforeReadAt(openedAt + responseDelay)
    const firstReply = await repository.getConversation(receipt.case_id)
    assert.equal(firstReply.detail.status, 'ai_active')
    assert.deepEqual(authors(firstReply), ['customer', 'customer', 'customer', 'ai'])

    browser.beforeReadAt(openedAt + 2 * responseDelay - 1)
    const beforeResolution = await repository.getConversation(receipt.case_id)
    assert.equal(beforeResolution.detail.status, 'ai_active')
    assert.deepEqual(beforeResolution.messages, firstReply.messages)

    browser.beforeReadAt(openedAt + 2 * responseDelay)
    const reopened = createFixtureRepository('empty')
    const resolved = await reopened.getConversation(receipt.case_id)
    assert.equal(resolved.detail.status, 'resolved')
    assert.equal(resolved.detail.updated_at, resolved.messages.at(-1).created_at)
    assert.equal(resolved.messages.at(-1).text, endingMessage)
    assert.deepEqual(authors(resolved), ['customer', 'customer', 'customer', 'ai', 'ai'])
    assert.deepEqual(resolved.messages.map(message => message.sequence), [1, 2, 3, 4, 5])
  })
}

test('adia uma proposta de resolução ao receber mensagem durante a rodada', async context => {
  const browser = simulateBrowser(context)
  const repository = createFixtureRepository('empty')
  const { receipt, openedAt } = await openConversation(repository, 'whatsapp')

  browser.beforeReadAt(openedAt + 3500)
  await repository.getConversation(receipt.case_id)
  await sendFollowUp(repository, receipt, 'Detalhe adicional')
  const secondRoundStartedAt = Date.now()
  await sendFollowUp(repository, receipt, 'Mais um detalhe')

  browser.beforeReadAt(secondRoundStartedAt + 3500)
  const stillActive = await repository.getConversation(receipt.case_id)
  assert.equal(stillActive.detail.status, 'ai_active')
  assert.deepEqual(authors(stillActive), ['customer', 'ai', 'customer', 'customer', 'ai'])
  assert.notEqual(stillActive.messages.at(-1).text, endingMessage)

  browser.beforeReadAt(secondRoundStartedAt + 7000)
  const resolved = await repository.getConversation(receipt.case_id)
  assert.equal(resolved.detail.status, 'resolved')
  assert.deepEqual(authors(resolved), ['customer', 'ai', 'customer', 'customer', 'ai', 'ai'])
  assert.equal(resolved.messages.at(-1).text, endingMessage)
})

test('recupera envios e rodada pendente salvos pelo simulador anterior', async context => {
  const browser = simulateBrowser(context)
  const repository = createFixtureRepository('empty')
  const { receipt, openedAt } = await openConversation(repository, 'email')
  await sendFollowUp(repository, receipt, 'Primeiro complemento')
  const secondDue = Date.now() + 3500
  await sendFollowUp(repository, receipt, 'Segundo complemento')

  // O formato anterior tinha uma resposta agendada para cada um dos dois primeiros relatos.
  const saved = JSON.parse(browser.storage.get(storageKey))
  const record = saved.cases[0]
  delete record.pendingReply
  record.replies = [{ due: openedAt + 3500, resolves: false }, { due: secondDue, resolves: true }]
  browser.storage.set(storageKey, JSON.stringify(saved))

  const reopened = createFixtureRepository('empty')
  browser.beforeReadAt(secondDue)
  const pending = await reopened.getConversation(receipt.case_id)
  assert.equal(pending.detail.status, 'ai_active')
  assert.deepEqual(authors(pending), ['customer', 'customer', 'customer', 'ai'])
  assert.deepEqual(await sendFollowUp(reopened, receipt, 'Segundo complemento'), receipt)

  browser.beforeReadAt(openedAt + 7000)
  const resolved = await reopened.getConversation(receipt.case_id)
  assert.equal(resolved.detail.status, 'resolved')
  assert.deepEqual(resolved.messages.slice(0, 3), record.messages)
  assert.deepEqual(authors(resolved), ['customer', 'customer', 'customer', 'ai', 'ai'])
})

test('repete o envio após falha de conexão e vincula novo caso após o encerramento', async context => {
  const browser = simulateBrowser(context)
  const repository = createFixtureRepository('empty')
  const { receipt, openedAt } = await openConversation(repository, 'email')
  browser.connection.onLine = false
  await assert.rejects(sendFollowUp(repository, receipt, 'Detalhe adicional'), /Conexão indisponível/)

  browser.connection.onLine = true
  assert.deepEqual(await sendFollowUp(repository, receipt, 'Detalhe adicional'), receipt)
  assert.deepEqual(await sendFollowUp(repository, receipt, 'Detalhe adicional'), receipt)
  await assert.rejects(sendFollowUp(repository, receipt, 'Outro texto', 'Detalhe adicional'), /outra mensagem/)

  browser.beforeReadAt(openedAt + 7000)
  const resolved = await repository.getConversation(receipt.case_id)
  assert.equal(resolved.detail.status, 'resolved')
  assert.deepEqual(authors(resolved), ['customer', 'customer', 'ai', 'ai'])

  const nextReceipt = await repository.sendMessage(receipt.channel_id, {
    text: 'Novo relato',
    external_conversation_id: receipt.external_conversation_id,
    ...classification,
  }, 'novo-caso')
  const next = await repository.getConversation(nextReceipt.case_id)
  assert.notEqual(nextReceipt.case_id, receipt.case_id)
  assert.equal(nextReceipt.external_conversation_id, receipt.external_conversation_id)
  assert.equal(next.detail.previous_case_id, receipt.case_id)
  assert.equal(next.detail.status, 'ai_active')
  assert.deepEqual(authors(next), ['customer'])
})
