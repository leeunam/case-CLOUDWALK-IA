import http from 'k6/http';
import { signature } from './wire.js';
import exec from 'k6/execution';

const config = JSON.parse(open(__ENV.F08_CONFIG || '/results/config.json'));
const entries = JSON.parse(open(__ENV.F08_PLAN || '/results/plan.json'));
const base = __ENV.F08_API || 'http://api:3000';
const channels = config.channels;
const secret = __ENV.CLOUDWALK_CHANNEL_SECRET;
const scenarios = {};
const offsets = {};
let elapsed = 0;
let offset = 0;
for (const [index, [rate, seconds]] of config.stages.entries()) {
  const name = `stage_${index}`;
  offsets[name] = offset;
  scenarios[name] = {
    executor: 'constant-arrival-rate', exec: 'initial', rate, timeUnit: '1s',
    startTime: `${elapsed}s`, duration: `${seconds}s`, gracefulStop: '5s',
    preAllocatedVUs: config.vus, maxVUs: config.vus,
  };
  elapsed += seconds;
  offset += rate * seconds;
}
export const options = { scenarios, systemTags: ['status', 'method', 'name', 'scenario', 'error_code'] };

function log(data) {
  console.log(JSON.stringify(data));
}

export function setup() {
  if (!secret) throw new Error('Segredo sintético ausente');
  log({ type: 'setup', at_ms: Date.now() });
}

function accepted(response) {
  if (response.status !== 202) return {};
  try {
    const body = response.json();
    return { case_id: body.case_id, correlation_id: body.correlation_id };
  } catch (_) {
    return {};
  }
}

export function initial() {
  const item = entries[offsets[exec.scenario.name] + exec.scenario.iterationInTest];
  const channel = channels[item.brand][item.kind];
  const raw = JSON.stringify(item.initial);
  const sent = Date.now();
  const timestamp = String(Math.floor(sent / 1000));
  const signed = signature(secret, channel, timestamp, raw);
  const response = http.post(`${base}/webhooks/v1/channels/${channel}/messages`, raw, {
    headers: { 'Content-Type': 'application/json', 'X-Webhook-Timestamp': timestamp, 'X-Webhook-Signature': signed },
    tags: { name: 'channel_webhook' }, redirects: 0, timeout: '4s',
  });
  const finished = Date.now();
  log({
    type: 'initial', source_event_id: item.initial.source_event_id, index: item.index, channel_id: channel,
    scenario_start_ms: exec.scenario.startTime, sent_ms: sent, finished_ms: finished, elapsed_ms: finished - sent,
    status: response.status, error_code: response.error_code ?? null, ...accepted(response),
  });
}

export { handleSummary } from './summary.js';
