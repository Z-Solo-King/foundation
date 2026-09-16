(() => {
  'use strict';
  const api = window.RIEFrontend;
  const root = document.getElementById('system-dashboard');
  const body = document.getElementById('system-dashboard-body');
  if (!api || !root || !body) return;

  const safeExternalUrl = (value) => {
    try {
      const url = new URL(String(value || ''), window.location.origin);
      return url.protocol === 'http:' || url.protocol === 'https:' ? url.href : '';
    } catch {
      return '';
    }
  };
  const safeLink = (value, label = 'Open') => {
    const url = safeExternalUrl(value);
    return url ? `<a href="${api.escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${api.escapeHtml(label)}</a>` : '';
  };
  const statusHtml = (status) => `<span class="dashboard-status ${api.escapeHtml(status || 'unknown')}">${api.escapeHtml(status || 'unknown')}</span>`;
  const metricText = (metric) => metric?.available ? `${metric.value ?? '—'} ${metric.unit || ''}`.trim() : 'Unavailable';
  const metricReason = (metric) => metric?.available ? `Source: ${metric.source || 'unknown'} · ${metric.timestamp || 'unknown'}` : `Unavailable · ${metric.reason || 'provider did not expose this metric'}`;

  function metricRows(resources = {}) {
    return Object.entries(resources).map(([name, metric]) => `<div class="dashboard-metric"><span>${api.escapeHtml(name.replaceAll('_', ' '))}<small class="dashboard-provenance">${api.escapeHtml(metricReason(metric))}</small></span><span class="dashboard-value">${api.escapeHtml(metricText(metric))}</span></div>`).join('');
  }

  function providerCard(provider) {
    const jobs = provider.running_jobs || [];
    const incidents = provider.incidents || [];
    const capabilities = Object.entries(provider.capabilities || {}).filter(([, enabled]) => enabled);
    return `<section class="dashboard-card dashboard-provider"><div class="dashboard-provider-head"><h3>${api.escapeHtml(provider.name)}</h3>${statusHtml(provider.status)}</div><p class="dashboard-muted">${api.escapeHtml(provider.message || '')}</p><div class="dashboard-metric"><span>Running jobs</span><span class="dashboard-value">${jobs.length}</span></div><div class="dashboard-metric"><span>Open incidents</span><span class="dashboard-value">${incidents.length}</span></div><div class="dashboard-metric"><span>Available capabilities</span><span class="dashboard-value">${capabilities.length}</span></div></section>`;
  }

  function recentFailures(providers) {
    const failures = providers.flatMap((provider) => (provider.recent_failures || []).map((run) => ({...run, provider: provider.name})));
    if (!failures.length) return '<p class="dashboard-empty">No recent failed/cancelled workflow runs were reported.</p>';
    return `<ul class="dashboard-list">${failures.slice(0, 30).map(run => `<li><strong>${api.escapeHtml(run.provider)}</strong> — ${api.escapeHtml(run.repository || '')} — ${api.escapeHtml(run.workflow || 'workflow')} — ${api.escapeHtml(run.conclusion || run.status || 'unknown')} ${safeLink(run.url)}</li>`).join('')}</ul>`;
  }

  function render(snapshot) {
    const providers = snapshot.providers || [];
    const incidents = snapshot.incidents || [];
    const jobs = providers.flatMap((provider) => (provider.running_jobs || []).map((job) => ({...job, provider: provider.name})));
    const totalBuckets = providers.find((provider) => provider.name === 'backblaze_b2')?.buckets?.length ?? 0;
    const github = providers.find((provider) => provider.name === 'github');
    const githubRate = github?.rate_limit;
    body.innerHTML = `<div class="dashboard-grid">
      <section class="dashboard-card dashboard-card-full"><h3>System status</h3><div class="dashboard-metric"><span>Overall</span><span>${statusHtml(snapshot.status)}</span></div><div class="dashboard-metric"><span>Providers</span><span class="dashboard-value">${snapshot.summary?.provider_count ?? providers.length}</span></div><div class="dashboard-metric"><span>Running jobs</span><span class="dashboard-value">${snapshot.summary?.running_job_count ?? jobs.length}</span></div><div class="dashboard-metric"><span>Incidents</span><span class="dashboard-value">${snapshot.summary?.incident_count ?? incidents.length}</span></div><div class="dashboard-muted">Observed ${api.escapeHtml(snapshot.observed_at || 'unknown')} · freshness window ${api.escapeHtml(snapshot.freshness?.max_age_seconds ?? 'unknown')}s</div></section>
      <section class="dashboard-card dashboard-card-full"><h3>Providers</h3><div class="dashboard-provider-grid">${providers.map(providerCard).join('')}</div></section>
      <section class="dashboard-card dashboard-card-wide"><h3>Jobs running</h3>${jobs.length ? `<ul class="dashboard-list">${jobs.map(job => `<li>${api.escapeHtml(job.provider)} — ${api.escapeHtml(job.job || job.name || job.job_id || 'job')} — ${api.escapeHtml(job.status || 'unknown')} ${safeLink(job.url)}</li>`).join('')}</ul>` : '<p class="dashboard-empty">No running jobs reported.</p>'}</section>
      <section class="dashboard-card"><h3>GitHub API budget</h3>${githubRate ? `<div class="dashboard-metric"><span>Remaining</span><span class="dashboard-value">${githubRate.remaining ?? '—'} / ${githubRate.limit ?? '—'}</span></div><div class="dashboard-metric"><span>Used</span><span class="dashboard-value">${githubRate.used ?? '—'}</span></div><p class="dashboard-provenance">Source: github.rest.rate_limit</p>` : '<p class="dashboard-empty">GitHub credentials not configured.</p>'}</section>
      <section class="dashboard-card"><h3>Backblaze B2</h3><div class="dashboard-metric"><span>Buckets</span><span class="dashboard-value">${totalBuckets}</span></div><div class="dashboard-muted">Bucket enumeration is not storage usage. Exact usage stays unavailable until the Usage Reports adapter is present.</div></section>
      <section class="dashboard-card dashboard-card-wide"><h3>Provider resources</h3>${providers.map(provider => `<div class="dashboard-provider-resource"><h4>${api.escapeHtml(provider.name)} ${statusHtml(provider.status)}</h4>${metricRows(provider.resources || {}) || '<p class="dashboard-empty">No provider resource metrics available.</p>'}</div>`).join('')}</section>
      <section class="dashboard-card dashboard-card-wide"><h3>Recent failures / cancellations</h3>${recentFailures(providers)}</section>
      <section class="dashboard-card dashboard-card-full"><h3>Incidents / bugs / failures</h3>${incidents.length ? incidents.map(item => `<div class="dashboard-incident"><strong>${api.escapeHtml(item.repository || item.repo || item.provider || '')} ${item.number ? `#${api.escapeHtml(item.number)}` : ''}</strong> — ${api.escapeHtml(item.title || item.message || item.code || 'incident')}<div>${safeLink(item.url)}${item.message ? `<span class="dashboard-provenance">${api.escapeHtml(item.message)}</span>` : ''}</div></div>`).join('') : '<p class="dashboard-empty">No incidents were reported by the configured collectors.</p>'}</section>
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
      body.innerHTML = `<div class="dashboard-error"><strong>Dashboard unavailable</strong><p>${api.escapeHtml(message)}</p><div class="dashboard-actions-inline"><button class="secondary" data-action="open-settings-from-dashboard">Open settings</button><button class="secondary" data-action="refresh-system-dashboard">Retry</button></div></div>`;
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