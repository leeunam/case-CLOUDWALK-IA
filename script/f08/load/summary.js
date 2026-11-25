// Apenas agregados internos do k6, sem tags por ID, cabeçalhos ou payloads.
export function handleSummary(data) {
  const names = ['dropped_iterations', 'iterations', 'http_reqs', 'http_req_failed',
    'http_req_duration', 'vus', 'vus_max', 'ws_sessions', 'ws_connecting', 'ws_session_duration'];
  const metrics = Object.fromEntries(names.filter(name => name in data.metrics).map(name => {
    const metric = data.metrics[name];
    return [name, metric.values ?? metric.summary ?? null];
  }));
  return { [__ENV.F08_K6_SUMMARY || '/results/k6-summary.json']: JSON.stringify(metrics) };
}
