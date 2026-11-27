import { signature } from './wire.js';

export default function () {
  const digest = signature('test-only', 'demo', '1700000000', JSON.stringify({ text: 'Confirmação do Pix?' }));
  console.log(JSON.stringify({ signature: digest }));
}

export { handleSummary } from './summary.js';
