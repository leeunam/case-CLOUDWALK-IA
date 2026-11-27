import crypto from 'k6/crypto';

export function signature(secret, channel, timestamp, raw) {
  const key = crypto.hmac('sha256', secret, `channel:${channel}`, 'hex');
  return crypto.hmac('sha256', key, `${timestamp}.${raw}`, 'hex');
}
