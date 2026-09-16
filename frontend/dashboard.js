(() => {
  'use strict';
  const api = window.RIEFrontend;
  const root = document.getElementById('system-dashboard');
  const body = document.getElementById('system-dashboard-body');
  if (!api || !root || !body) return;

  const escapeHtml = (value) => String(value ?? '').replace(/[&<>\"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
  const statusHtml = (status) => `<span class="dashboard-status ${escapeHtml(status || 'unknown')}">${escapeHtml(status || 'unknown')}</span>`;
  const metricText = (metric) => metric?.available ? `${metric.value ?? '—'} ${metric.unit || ''}`.trim() : 'Unavailable';
  const metricReason = (metric) => metric?.available ? `Source: ${metric.source || 'unknown'} · ${metric.timestamp || 'unknown'}` : `Unavailable · ${metric.reason || 'provider did not expose this metric'}`;

  function metricRows(resources = {}) {
    return Object.entries(resources).map(([name, metric]) => `<div class="dashboard-metric"><span>${escapeHtml(name.replaceAll('_', ' '))}<small class="dashboard-provenance">${escapeHtml(metricReason(metric))}</small></span><span class="dashboard-value">${escapeHtml(metricText(metric))}</span></div>`).join('');
  }

  function providerCard(provider) {
    const jobs = provider.running_jobs || [];
    const incidents = provider.incidents || [];
    const capabilities = Object.entries(provider.capabilities || {}).filter(([, enabled]) => enabled);
    return `<section class="dashboard-card dashboard-provider">
      <div class="dashboard-provider-head"><h3>${escapeHtml(provider.name)}</h3>${statusHtml(provider.status)}</div>
      <p class="dashboard-muted">${escapeHtml(provider.message || '')}</p>
      <div class="dashboard-metric"><span>Running jobs</span><span class="dashboard-value">${jobs.length}</span></div>
      <div class="dashboard-metric"><span>Open incidents</span><span class="dashboard-value">${incidents.length}</span></div>
      <div class="dashboard-metric"><span>Available capabilities</span><span class="dashboard-value">${capabilities.length}</span></div>
    </section>`;
  }

  function recentFailures(providers) {
    const failures = providers.flatMap((provider) => (provider.recent_failures || []).map((run) => ({...run, provider: provider.name})));
    if (!failures.length) return '<p class="dashboard-empty">No recent failed/cancelled workflow runs were reported.</p>';
    return `<ul class="dashboard-list">${failures.slice(0, 30).map(run => `<li><strong>${escapeHtml(run.provider)}</strong> — ${escapeHtml(run.repository || '')} — ${escapeHtml(run.workflow || 'workflow')} — ${escapeHtml(run.conclusion || run.status || 'unknown')} ${run.url ? `<a href="${escapeHtml(run.url)}" target="_blank" rel="noreferrer">Open</a>` : ''}</li>`).join('')}</ul>`;
  }

  function render(snapshot) {
    const providers = snapshot.providers || [];
    const incidents = snapshot.incidents || [];
    const jobs = providers.flatMap((provider) => (provider.running_jobs || []).map((job) => ({...job, provider: provider.name})));
    const totalBuckets = providers.find((provider) => provider.name === 'backblaze_b2')?.buckets?.length ?? 0;
    const github = providers.find((provider) => provider.name === 'github');
    const githubRate = github?.rate_limit;
    body.innerHTML = `<div class="dashboard-grid">
      <section class="dashboard-card dashboard-card-full"><h3>System status</h3>
        <div class="dashboard-metric"><span>Overall</span><span>${statusHtml(snapshot.status)}</span></div>
        <div class="dashboard-metric"><span>Providers</span><span class="dashboard-value">${snapshot.summary?.provider_count ?? providers.length}</span></div>
        <div class="dashboard-metric"><span>Running jobs</span><span class="dashboard-value">${snapshot.summary?.running_job_count ?? jobs.length}</span></div>
        <div class="dashboard-metric"><span>Incidents</span><span class="dashboard-value">${snapshot.summary?.incident_count ?? incidents.length}</span></div>
        <div class="dashboard-muted">Observed ${escapeHtml(snapshot.observed_at || 'unknown')} · freshness window ${escapeHtml(snapshot.freshness?.max_age_seconds ?? 'unknown')}s</div>
      </section>
      <section class="dashboard-card dashboard-card-full"><h3>Providers</h3><div class="dashboard-provider-grid">${providers.map(providerCard).join('')}</div></section>
      <section class="dashboard-card dashboard-card-wide"><h3>Jobs running</h3>${jobs.length ? `<ul class="dashboard-list">${jobs.map(job => `<li>${escapeHtml(job.provider)} — ${escapeHtml(job.job || job.name || job.job_id || 'job')} — ${escapeHtml(job.status || 'unknown')} ${job.url ? `<a href="${escapeHtml(job.url)}" target="_blank" rel="noreferrer">Open</a>` : ''}</li>`).join('')}</ul>` : '<p class="dashboard-empty">No running jobs reported.</p>'}</section>
      <section class="dashboard-card"><h3>GitHub API budget</h3>${githubRate ? `<div class="dashboard-metric"><span>Remaining</span><span class="dashboard-value">${githubRate.remaining ?? '—'} / ${githubRate.limit ?? '—'}</span></div><div class="dashboard-metric"><span>Used</span><span class="dashboard-value">${githubRate.used ?? '—'}</span></div><p class="dashboard-provenance">Source: github.rest.rate_limit</p>` : '<p class="dashboard-empty">GitHub credentials not configured.</p>'}</section>
      <section class="dashboard-card"><h3>Backblaze B2</h3><div class="dashboard-metric"><span>Buckets</span><span class="dashboard-value">${totalBuckets}</span></div><div class="dashboard-muted">Bucket enumeration is not storage usage. Exact usage stays unavailable until the Usage Reports adapter is present.</div></section>
      <section class="dashboard-card dashboard-card-wide"><h3>Provider resources</h3>${providers.map(provider => `<div class="dashboard-provider-resource"><h4>${escapeHtml(provider.name)} ${statusHtml(provider.status)}</h4>${metricRows(provider.resources || {}) || '<p class="dashboard-empty">No provider resource metrics available.</p>'}</div>`).join('')}</section>
      <section class="dashboard-card dashboard-card-wide"><h3>Recent failures / cancellations</h3>${recentFailures(providers)}</section>
      <section class="dashboard-card dashboard-card-full"><h3>Incidents / bugs / failures</h3>${incidents.length ? incidents.map(item => `<div class="dashboard-incident"><strong>${escapeHtml(item.repository || item.repo || item.provider || '')} ${item.number ? `#${escapeHtml(item.number)}` : ''}</strong> — ${escapeHtml(item.title || item.message || item.code || 'incident')}<div>${item.url ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">Open</a>` : ''}${item.message ? `<span class="dashboard-provenance">${escapeHtml(item.message)}</span>` : ''}</div></div>`).join('') : '<p class="dashboard-empty">No incidents were reported by the configured collectors.</p>'}</section>
    </div>`;
  }

  async function refresh() {
    body.classList.add('dashboard-refreshing');
    try {
      const response = await fetch(api.apiUrl('/api/v1/dashboard'), { headers: api.authHeaders() });
      const snapshot = await response.json().catch(() => ({}));
      if (!response.ok || !snapshot.ok) {
        if (response.status === 401) throw new Error('dashboard_auth_required');
        throw new Error(snapshot.error || `Dashboard request failed (${response.status})`);
      }
      render(snapshot);
    } catch (error) {
      const code = String(error.message || error);
      const message = code === 'dashboard_auth_required' ? 'Dashboard authentication is required. Set a short-lived session token in Settings, then refresh.' : (code === 'dashboard_backend_unavailable' ? 'Dashboard telemetry is currently unavailable. Chat and research remain independent.' : code);
      body.innerHTML = `<div class="dashboard-error"><strong>Dashboard unavailable</strong><p>${escapeHtml(message)}</p><div class="dashboard-actions-inline"><button class="secondary" data-action="open-settings-from-dashboard">Open settings</button><button class="secondary" data-action="refresh-system-dashboard">Retry</button></div></div>`;
    } finally {
      body.classList.remove('dashboard-refreshing');
    }
  }

  document.addEventListener('click', (event) => {
    if (event.target.closest('[data-action="open-system-dashboard"]')) { event.preventDefault(); root.classList.add('open'); void refresh(); }
    if (event.target.closest('[data-action="close-system-dashboard"]')) { event.preventDefault(); root.classList.remove('open'); }
    if (event.target.closest('[data-action="refresh-system-dashboard"]')) { event.preventDefault(); void refresh(); }
    if (event.target.closest('[data-action="open-settings-from-dashboard"]')) { event.preventDefault(); root.classList.remove('open'); api.state.view = 'settings'; api.chatView?.render(); }
  });

  api.openSystemDashboard = () => { root.classList.add('open'); void refresh(); };
  api.closeSystemDashboard = () => root.classList.remove('open');
})();
