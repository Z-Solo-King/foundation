(() => {
  'use strict';

  const api = window.RIEFrontend;
  if (!api) throw new Error('frontend_state.js must load before workspace_view.js');

  const body = document.getElementById('workspace-body');

  const esc = api.escapeHtml;
  const asArray = (value) => Array.isArray(value) ? value : [];

  function statusClass(status) {
    const value = String(status || '').toLowerCase();
    if (['completed', 'complete', 'success', 'succeeded'].includes(value)) return 'status-success';
    if (['failed', 'error', 'blocked', 'cancelled', 'canceled'].includes(value)) return 'status-danger';
    if (['partial', 'unknown', 'timeout', 'paused'].includes(value)) return 'status-warn';
    return 'status-live';
  }

  function sourceRows(sources) {
    return asArray(sources).map((source, index) => {
      const url = source.url || '';
      const title = source.title || url || `Source ${index + 1}`;
      const state = source.access_state || source.integrity_state || source.state || 'observed';
      const method = source.retrieval_method || source.method || '';
      return `<div class="evidence-row"><span class="state-dot ${statusClass(state)}">●</span><div><a href="${esc(url || '#')}" target="_blank" rel="noopener noreferrer">${esc(title)}</a><small>${esc(state)}${method ? ` · ${esc(method)}` : ''}</small></div></div>`;
    }).join('');
  }

  function resultText(data) {
    return data?.result?.answer || data?.result?.text || data?.result?.summary || data?.answer || '';
  }

  function render(data = {}, error = '') {
    if (!body) return;
    const run = data.run || data.research_run || {};
    const status = String(data.status || run.status || 'unknown').toLowerCase();
    const observations = asArray(data.observations || run.observations);
    const sources = asArray(data.sources || data.result?.sources);
    const capabilities = data.capabilities || {};
    const stats = data.stats || run.stats || {};
    const metadata = data.metadata || {};
    const answer = resultText(data);
    const runId = run.run_id || data.run_id || 'unknown';
    const evidence = sources.length ? sources : observations;
    const errorHtml = error ? `<div class="error-banner" role="alert">${esc(error)}</div>` : '';
    const answerHtml = answer ? `<section class="workspace-card result-card"><div class="card-head"><strong>Result</strong><span>${esc(status)}</span></div><div class="result-text">${esc(answer)}</div></section>` : '';
    const statsHtml = Object.keys(stats).length ? `<section class="workspace-card"><div class="card-head"><strong>Run metrics</strong><span>${Object.keys(stats).length}</span></div><pre class="json-block">${esc(JSON.stringify(stats, null, 2))}</pre></section>` : '';
    const metadataHtml = Object.keys(metadata).length ? `<section class="workspace-card"><div class="card-head"><strong>Run metadata</strong></div><pre class="json-block">${esc(JSON.stringify(metadata, null, 2))}</pre></section>` : '';
    const capabilitiesHtml = Object.keys(capabilities).length ? `<section class="workspace-card"><details><summary>Backend capabilities</summary><pre class="json-block">${esc(JSON.stringify(capabilities, null, 2))}</pre></details></section>` : '';

    body.innerHTML = `${errorHtml}
      <section class="workspace-card accent-card" aria-live="polite">
        <div class="card-head"><span>Current research run</span><b class="run-status ${statusClass(status)}">${esc(status)}</b></div>
        <h3>${esc(runId)}</h3>
        <p>Browser UI observes backend state; it never invents completion, evidence, or policy state.</p>
        <div class="card-actions"><button class="secondary" data-lifecycle-refresh="true">Refresh</button><button class="secondary" data-lifecycle-reconnect="true">Reconnect</button><button class="secondary" data-lifecycle-stop="true">Stop polling</button></div>
      </section>
      ${answerHtml}
      <section class="workspace-card"><div class="card-head"><strong>Evidence</strong><span>${evidence.length}</span></div>${sourceRows(evidence) || '<p class="muted">No evidence records returned yet.</p>'}</section>
      ${statsHtml}${metadataHtml}${capabilitiesHtml}`;
  }

  api.workspaceView = Object.freeze({ render });
})();
