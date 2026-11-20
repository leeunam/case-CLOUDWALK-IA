import http from 'k6/http';
import crypto from 'k6/crypto';
import ws from 'k6/ws';
import exec from 'k6/execution';
import { sleep } from 'k6';

const config = JSON.parse(open(__ENV.F08_CONFIG || '/results/config.json'));
const base = __ENV.F08_API || 'http://api:3000';
const { target, ramp_seconds, hold_seconds, period_seconds } = config.chat;
export const options = {
  scenarios: { chat: { executor: 'per-vu-iterations', vus: target, iterations: 1,
    maxDuration: `${ramp_seconds + hold_seconds + 25}s`, gracefulStop: '5s' } },
  systemTags: ['status', 'method', 'name', 'scenario', 'error_code'],
};

export function setup() {
  const at = Date.now();
  console.log(JSON.stringify({ type: 'setup', at_ms: at }));
  return { steady: at + ramp_seconds * 1000, end: at + (ramp_seconds + hold_seconds) * 1000 };
}

export default function ({ steady, end }) {
  const client = exec.vu.idInTest;
  const log = (type, data = {}) => console.log(JSON.stringify({ type, client, at_ms: Date.now(), ...data }));
  const period = period_seconds * 1000;
  const phase = ((client - 1 + config.seed % target) % target) / target * period;
  sleep((client - 1) / target * ramp_seconds * 0.8);
  const tag = name => ({ tags: { name }, timeout: '4s', redirects: 0 });
  const root = '/api/v1';
  const brand = client % 2 ? 'aurora' : 'horizonte';
  const channel = config.channels[brand].chat;
  const first = http.get(base + root + '/session', tag('session_csrf'));
  if (first.status !== 200) {
    log('setup_error', { operation: 'csrf', status: first.status, error_code: first.error_code });
    return;
  }
  const session = http.post(base + root + '/simulator/session', null, {
    ...tag('simulator_session'), headers: { 'X-CSRF-Token': first.json('csrf_token') },
  });
  if (session.status !== 201) {
    log('setup_error', { operation: 'simulator_session', status: session.status, error_code: session.error_code });
    return;
  }
  const headers = { 'X-CSRF-Token': session.json('csrf_token'), 'X-Simulator-Session-Id': session.json('user.id'),
    'Content-Type': 'application/json' };
  let sequence = 0;
  let conversation = null;
  let caseId = null;
  let cursor = 0;
  let next = steady + phase;
  let everConfirmed = false;
  let reconnectProbe = false;

  function send(preparation = false, reconnectProbeWrite = false) {
    const key = `${config.run_id}-chat-${client}-${sequence++}`;
    const raw = JSON.stringify({ text: 'Qual é o prazo de confirmação do Pix?', category: 'pix', priority: 'basic',
      ...(conversation ? { external_conversation_id: conversation } : {}) });
    const sent = Date.now();
    const response = http.post(base + root + `/simulator/channels/${channel}/messages`, raw, {
      ...tag('chat_message'), headers: { ...headers, 'Idempotency-Key': key },
    });
    const previous = caseId;
    if (response.status === 202) {
      caseId = response.json('case_id');
      conversation = response.json('external_conversation_id');
      if (previous !== caseId) cursor = 0;
    }
    const source = 'simulator-' + crypto.sha256(JSON.stringify([headers['X-Simulator-Session-Id'], channel, key]), 'hex');
    log('chat_write', { key, source_event_id: source, case_id: response.status === 202 ? caseId : null,
      correlation_id: response.status === 202 ? response.json('correlation_id') : null,
      channel_id: channel, sent_ms: sent, status: response.status, error_code: response.error_code,
      preparation, reconnect_probe_write: reconnectProbeWrite, opened_case: response.status === 202 ? previous !== caseId : null });
    return response.status === 202;
  }

  function recover(reason, identifier) {
    let status;
    let recovered = 0;
    const before = cursor;
    const ids = [];
    do {
      const response = http.get(base + root + `/simulator/cases/${caseId}/messages?after_sequence=${cursor}`,
        tag('chat_read'));
      status = response.status;
      if (status !== 200) break;
      const data = response.json();
      const last = data.items[data.items.length - 1];
      if (!last || last.sequence <= cursor) break;
      recovered += data.items.length;
      if (reason === 'reconnect' && client === 1) ids.push(...data.items.map(item => item.id));
      cursor = last.sequence;
      if (!data.next_after_sequence) break;
    } while (Date.now() < end);
    if (reason === 'reconnect' || status !== 200) {
      log('chat_read', { reason, status, identifier, case_id: caseId, after_sequence: before, through_sequence: cursor, recovered, recovered_ids: ids });
    }
  }

  if (!send(true)) return;
  while (Date.now() < end) {
    let identifier;
    let confirmed = false;
    let closing = false;
    let controlled = false;
    const close = (socket, reason) => {
      if (closing) return;
      closing = true;
      if (confirmed) log('subscription_closed', { case_id: caseId, identifier, cursor, reason });
      confirmed = false;
      socket.close();
    };
    try {
      const response = ws.connect(base.replace(/^http/, 'ws') + '/cable', {
        jar: http.cookieJar(), headers: { Origin: base, 'Sec-WebSocket-Protocol': 'actioncable-v1-json' },
        tags: { name: 'action_cable' },
      }, socket => {
        function subscribe() {
          identifier = JSON.stringify({ channel: 'CaseUpdatesChannel', case_id: caseId, audience: 'simulator' });
          socket.send(JSON.stringify({ command: 'subscribe', identifier }));
        }

        socket.on('message', raw => {
          if (closing) return;
          const frame = JSON.parse(raw);
          if (frame.type === 'welcome') subscribe();
          if (frame.type === 'disconnect' || frame.type === 'reject_subscription') {
            log('socket_error', { operation: frame.type });
            close(socket, 'rejeicao');
          }
          if (frame.type === 'confirm_subscription' && identifier === frame.identifier && !confirmed) {
            confirmed = true;
            log('subscription_confirmed', { case_id: caseId, identifier, reconnect: everConfirmed });
            recover(everConfirmed ? 'reconnect' : 'initial', identifier);
            everConfirmed = true;
          }
          if (confirmed && frame.identifier === identifier && frame.message?.type === 'case.updated') recover('update', identifier);
        });
        socket.on('close', () => {
          if (confirmed) log('subscription_closed', { case_id: caseId, identifier, cursor, reason: 'remoto' });
          confirmed = false;
        });
        socket.on('error', () => {
          log('socket_error', { operation: 'transport' });
          close(socket, 'transporte');
        });
        socket.setTimeout(() => {
          if (!confirmed) close(socket, 'timeout_confirmacao');
        }, 8000);
        socket.setInterval(() => {
          const at = Date.now();
          if (at >= end) {
            close(socket, 'fim');
            return;
          }
          if (!confirmed) return;
          if (client === 1 && !reconnectProbe) {
            // Provar a recuperação no caso inicial, antes que outra escrita o resolva.
            if (cursor <= 0) return;
            reconnectProbe = controlled = true;
            close(socket, 'prova_reconexao');
            return;
          }
          if (at < next) return;
          if (at >= next + period) {
            const skipped = Math.floor((at - next) / period);
            log('chat_slots_skipped', { count: skipped });
            next += skipped * period;
          }
          next += period;
          const previous = caseId;
          send();
          if (caseId !== previous) {
            log('subscription_closed', { case_id: previous, identifier, reason: 'novo_caso' });
            confirmed = false;
            socket.send(JSON.stringify({ command: 'unsubscribe', identifier }));
            subscribe();
          }
        }, 500);
      });
      if (response?.status !== 101) log('socket_error', { operation: 'handshake', status: response?.status });
    } catch (_) {
      log('socket_error', { operation: 'exception' });
    } finally {
      if (confirmed) log('subscription_closed', { case_id: caseId, identifier, cursor, reason: 'fim_da_iteracao' });
    }
    if (controlled) send(true, true); // Escrita identificada fora do socket para testar recuperação pelo cursor.
    if (Date.now() < end) sleep(1);
  }
}

export { handleSummary } from './summary.js';
