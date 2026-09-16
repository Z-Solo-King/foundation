(() => {
  'use strict';
  const api = window.RIEFrontend;
  const root = document.getElementById('system-dashboard');
  const body = document.getElementById('system-dashboard-body');
  if (!api || !root || !body) return;

  const escapeHtml = (value) => String(value ?? '').replace(/[&<>\"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
  const statusHtml = (status) => `<span class="dashboard-status ${escapeHtml(status)}">${escapeHtml(status)}</span>`;

  function providerCard(provider) {
    const jobs = provider.running_jobs || [];
    const incidents = provider.incidents || [];
    const capabilities = Object.entries(provider.capabilities || {}).filter(([, enabled]) => enabled);
    return `<section class="dashboard-card dashboard-provider">
      <div style="display:flex;justify-content:space-between;gap:8px;align-items:center"><h3>${escapeHtml(provider.name)}</h3>${statusHtml(provider.status)}</div>
      <p class="dashboard-muted">${escapeHtml(provider.message || '')}</p>
      <div class="dashboard-metric"><span>Running jobs</span><span class="dashboard-value">${jobs.length}</span></div>
      <div class="dashboard-metric"><span>Open incidents</span><span class="dashboard-value">${incidents.length}</span></div>
      <div class="dashboard-metric"><span>Available capabilities</span><span class="dashboard-value">${capabilities.length}</span></div>
    </section>`;
  }

  function render(snapshot) {
    const providers = snapshot.providers || [];
    const incidents = snapshot.incidents || [];
    const jobs = providers.flatMap((provider) => (provider.running_jobs || []).map((job) => ({...job, provider: provider.name})));
    const totalBuckets = providers.find((provider) => provider.name === 'backblaze_b2')?.buckets?.length ?? 0;
    const githubRate = providers.find((provider) => provider.name === 'github')?.rate_limit;
    body.innerHTML = `<div class="dashboard-grid">
      <section class="dashboard-card dashboard-card-full"><h3>System status</h3>
        <div class="dashboard-metric"><span>Overall</span><span>${statusHtml(snapshot.status)}</span></div>
        <div class="dashboard-metric"><span>Providers</span><span class="dashboard-value">${snapshot.summary?.provider_count ?? providers.length}</span></div>
        <div class="dashboard-metric"><span>Running jobs</span><span class="dashboard-value">${snapshot.summary?.running_job_count ?? jobs.length}</span></div>
        <div class="dashboard-metric"><span>Incidents</span><span class="dashboard-value">${snapshot.summary?.incident_count ?? incidents.length}</span></div>
        <div class="dashboard-muted">Observed ${escapeHtml(snapshot.observed_at || 'unknown')}</div>
      </section>
      <section class="dashboard-card dashboard-card-full"><h3>Providers</h3><div class="dashboard-provider-grid">${providers.map(providerCard).join('')}</div></section>
      <section class="dashboard-card dashboard-card-wide"><h3>Jobs running</h3>${jobs.length ? `<ul class="dashboard-list">${jobs.map(job => `<li>${escapeHtml(job.provider)} — ${escapeHtml(job.name || job.id || 'job')} — ${escapeHtml(job.status || 'unknown')}</li>`).join('')}</ul>` : '<p class="dashboard-empty">No running jobs reported.</p>'}</section>
      <section class="dashboard-card"><h3>GitHub API budget</h3>${githubRate ? `<div class="dashboard-metric"><span>Remaining</span><span class="dashboard-value">${githubRate.remaining ?? '—'} / ${githubRate.limit ?? '—'}</span></div><div class="dashboard-metric"><span>Used</span><span class="dashboard-value">${githubRate.used ?? '—'}</span></div>` : '<p class="dashboard-empty">GitHub credentials not configured.</p>'}</section>
      <section class="dashboard-card"><h3>Backblaze B2</h3><div class="dashboard-metric"><span>Buckets</span><span class="dashboard-value">${totalBuckets}</span></div><p class="dashboard-muted">Exact storage is reported from the Usage Report integration, not by repeatedly scanning all files.</p></section>
      <section class="dashboard-card"><h3>Resource telemetry</h3><div class="dashboard-metric"><span>CPU</span><span class="dashboard-value">provider-specific</span></div><div class="dashboard-metric"><span>Memory</span><span class="dashboard-value">provider-specific</span></div><div class="dashboard-metric"><span>Storage</span><span class="dashboard-value">provider-specific</span></div><p class="dashboard-muted">The dashboard never invents host-level CPU/RAM/storage values where a provider does not expose them.</p></section>
      <section class="dashboard-card dashboard-card-full"><h3>Incidents / bugs / failures</h3>${incidents.length ? incidents.map(item => `<div class="dashboard-incident"><strong>${escapeHtml(item.repo || '')} #${escapeHtml(item.number || '')}</strong> — ${escapeHtml(item.title || 'incident')}<div><a href="${escapeHtml(item.url || '#')}" target="_blank" rel="noreferrer">Open in GitHub</a></div></div>`).join('') : '<p class="dashboard-empty">No GitHub issues currently classified as bug/error/failure by the collector.</p>'}</section>
    </div>`;
  }

  async function refresh() {
    body.classList.add('dashboard-refreshing');
    try {
      const response = await fetch(api.apiUrl('/api/v1/dashboard'), { headers: api.authHeaders() });
      const snapshot = await response.json().catch(() => ({}));
      if (!response.ok || !snapshot.ok) throw new Error(snapshot.error || `Dashboard request failed (${response.status})`);
      render(snapshot);
    } catch (error) {
      body.innerHTML = `<div class="dashboard-error"><strong>Dashboard unavailable</strong><p>${escapeHtml(error.message || error)}</p><p class="dashboard-muted">The chatbot remains usable; telemetry failure does not affect chat or research authority.</p></div>`;
    } finally {
      body.classList.remove('dashboard-refreshing');
    }
  }

  document.addEventListener('click', (event) => {
    if (event.target.closest('[data-action="open-system-dashboard"]')) {
      event.preventDefault();
      root.classList.add('open');
      void refresh();
    }
    if (event.target.closest('[data-action="close-system-dashboard"]')) {
      event.preventDefault();
      root.classList.remove('open');
    }
    if (event.target.closest('[data-action="refresh-system-dashboard"]')) {
      event.preventDefault();
      void refresh();
    }
  });

  api.openSystemDashboard = () => { root.classList.add('open'); void refresh(); };
  api.closeSystemDashboard = () => root.classList.remove('open');
})();
