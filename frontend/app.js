(() => {
  const state = { chats: [], activeChatId: null, queue: [], processing: false, research: null, backendOk: false, attachments: [] };
  const $ = (id) => document.getElementById(id);
  const root = document.documentElement;
  const sidebar = $('sidebar'), overlay = document.querySelector('.mobile-overlay');
  const workspace = $('workspace'), workspaceBody = $('workspace-body');
  const conversation = $('conversation-scroll'), prompt = $('prompt'), search = $('chat-search');
  const emptyState = $('empty-state'), composerStatus = $('composer-status');
  const queuePanel = $('message-queue'), queueList = $('queue-list'), queueCount = $('queue-count'), queueStatus = $('queue-status');
  const toast = $('toast'), connectionPill = $('connection-pill'), mobileTitle = $('mobile-title');
  const API_BASE = (document.body.dataset.apiBase || '').replace(/\/$/, '');
  const STORAGE_KEY = 'rie.frontend.chats.v1';

  const showToast = (message) => { toast.textContent = message; toast.classList.add('show'); clearTimeout(showToast.timer); showToast.timer = setTimeout(() => toast.classList.remove('show'), 1800); };
  const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const currentMode = () => document.querySelector('.mode.active')?.dataset.mode || 'chat';
  const apiUrl = (path) => `${API_BASE}${path}`;
  const saveChats = () => localStorage.setItem(STORAGE_KEY, JSON.stringify(state.chats));
  const loadChats = () => { try { state.chats = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch { state.chats = []; } };

  function newChat() {
    const chat = { id: crypto.randomUUID?.() || `${Date.now()}`, title: 'New chat', messages: [], createdAt: Date.now() };
    state.chats.unshift(chat); state.activeChatId = chat.id; state.research = null; saveChats(); render(); prompt.focus();
  }
  function activeChat() { return state.chats.find(c => c.id === state.activeChatId); }
  function ensureChat() { if (!state.activeChatId || !activeChat()) newChat(); return activeChat(); }
  function addMessage(role, text, meta = {}) { const chat = ensureChat(); chat.messages.push({ id: crypto.randomUUID?.() || `${Date.now()}-${Math.random()}`, role, text, meta, at: Date.now() }); if (role === 'user' && chat.title === 'New chat') chat.title = text.slice(0, 48); saveChats(); }

  function renderChats() {
    const list = $('chat-list');
    const q = search.value.trim().toLowerCase();
    list.innerHTML = state.chats.filter(c => !q || c.title.toLowerCase().includes(q)).slice(0, 50).map(c => `<button class="chat-row ${c.id === state.activeChatId ? 'active' : ''}" data-chat="${c.id}"><span class="chat-icon">✦</span><span><strong>${escapeHtml(c.title)}</strong><small>${new Date(c.createdAt).toLocaleDateString()}</small></span></button>`).join('');
  }
  function renderConversation() {
    const chat = activeChat();
    mobileTitle.textContent = chat?.title || 'New chat';
    if (!chat || chat.messages.length === 0) { conversation.innerHTML = ''; conversation.append(emptyState); emptyState.hidden = false; return; }
    emptyState.hidden = true;
    conversation.innerHTML = chat.messages.map(m => `<article class="message ${m.role === 'user' ? 'user-message' : 'assistant-message'}"><div class="message-bubble">${escapeHtml(m.text)}</div>${m.meta?.sources?.length ? `<div class="source-list">${m.meta.sources.map((s,i)=>`<div><span>${i+1}</span><a href="${escapeHtml(s.url || '#')}" target="_blank" rel="noreferrer">${escapeHtml(s.url || 'source')}</a><small>${escapeHtml(s.access_state || '')}</small></div>`).join('')}</div>` : ''}</article>`).join('');
    conversation.scrollTop = conversation.scrollHeight;
  }
  function render() { renderChats(); renderConversation(); renderQueue(); renderResearch(); }

  function renderQueue() { queueCount.textContent = state.queue.length; queueCount.hidden = !state.queue.length; queueStatus.textContent = state.queue.length ? `${state.queue.length} waiting` : 'Nothing waiting'; queueList.innerHTML = state.queue.map((q,i)=>`<div class="queue-item"><b>${i+1}</b><div><strong>${q.mode}</strong><p>${escapeHtml(q.text)}</p></div><button data-remove-queue="${q.id}">×</button></div>`).join(''); }
  function openQueue() { queuePanel.classList.add('open'); queuePanel.setAttribute('aria-hidden','false'); document.querySelector('.queue-overlay').classList.add('show'); renderQueue(); }
  function closeQueue() { queuePanel.classList.remove('open'); queuePanel.setAttribute('aria-hidden','true'); document.querySelector('.queue-overlay').classList.remove('show'); }
  function openSidebar() { sidebar.classList.add('open'); overlay.classList.add('show'); }
  function closeSidebar() { sidebar.classList.remove('open'); overlay.classList.remove('show'); }
  function openWorkspace() { workspace.classList.add('open'); }
  function closeWorkspace() { workspace.classList.remove('open'); }

  async function backendCheck() {
    if (!API_BASE) { setBackend(false, 'API base not configured'); return false; }
    try { const r = await fetch(apiUrl('/readiness'), { headers: { Accept: 'application/json' } }); setBackend(r.ok, r.ok ? 'Backend ready' : `Backend ${r.status}`); return r.ok; }
    catch { setBackend(false, 'Backend unavailable'); return false; }
  }
  function setBackend(ok, text) { state.backendOk = ok; connectionPill.textContent = text; connectionPill.classList.toggle('ok', ok); }

  async function submitResearch(question) {
    if (!API_BASE) throw new Error('Research API base is not configured');
    const chat = ensureChat();
    addMessage('user', question);
    renderConversation();
    const payload = { question, depth: 'standard', require_citations: true, max_sources: 8, max_evidence_items: 24, strict_zero_cost_only: true, source_urls: [] };
    const response = await fetch(apiUrl('/api/v1/research'), { method:'POST', headers:{'Content-Type':'application/json','Accept':'application/json'}, body:JSON.stringify(payload) });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || !body.ok) throw new Error(body.error || `Research request failed (${response.status})`);
    state.research = { runId: body.run_id, status: 'submitted', metadata: body.metadata || {}, sources: body.sources || [] };
    renderResearch();
    addMessage('assistant', `Research run ${body.run_id} submitted. Tracking backend observations.`, { runId: body.run_id, sources: body.sources || [] });
    renderConversation();
    void pollResearch(body.run_id);
    return body;
  }

  async function pollResearch(runId) {
    if (!API_BASE) return;
    for (let i = 0; i < 30; i++) {
      await new Promise(r => setTimeout(r, 1500));
      try {
        const r = await fetch(apiUrl(`/api/v1/research/${encodeURIComponent(runId)}`), { headers:{Accept:'application/json'} });
        if (!r.ok) throw new Error(`status ${r.status}`);
        const body = await r.json();
        state.research = { ...state.research, status:'observed', run:body.run, observations:body.observations || [] };
        renderResearch();
        const chat = activeChat();
        if (chat && !chat.messages.some(m => m.meta?.runId === runId && m.meta?.final)) {
          const observations = (body.observations || []).map(o => ({ url:o.url, access_state:o.access_state }));
          addMessage('assistant', `Research run ${runId} returned ${observations.length} observed source record(s).`, { runId, sources:observations, final:true });
          renderConversation();
        }
        return body;
      } catch (err) { state.research = { ...state.research, status:'polling', error:String(err.message || err) }; renderResearch(); }
    }
    state.research = { ...state.research, status:'timeout' }; renderResearch();
  }

  function renderResearch() {
    if (!state.research) { workspaceBody.innerHTML = '<div class="workspace-card"><strong>No active research run</strong><p>Switch to Research mode to submit a real run.</p></div>'; return; }
    const r = state.research;
    const obs = (r.observations || []).map(o => `<div class="evidence-row"><span>●</span><div><strong>${escapeHtml(o.url || 'source')}</strong><small>${escapeHtml(o.access_state || o.retrieval_method || 'observed')}</small></div></div>`).join('');
    workspaceBody.innerHTML = `<section class="workspace-card accent-card"><div class="card-head"><span>Current task</span><b>${escapeHtml(r.status)}</b></div><h3>${escapeHtml(r.runId || 'pending')}</h3><p>Backend research lifecycle with bounded polling. Strict $0 mode remains enabled.</p></section><section class="workspace-card"><div class="card-head"><span>Evidence</span><span>${(r.observations||[]).length}</span></div>${obs || '<p>No observation records returned yet.</p>'}</section>`;
  }

  async function send() {
    const text = prompt.value.trim(); if (!text) return; prompt.value=''; prompt.style.height='auto';
    if (currentMode() === 'research') { try { composerStatus.textContent='Submitting research run…'; await submitResearch(text); composerStatus.textContent='Research run is being tracked in the workspace.'; } catch (e) { addMessage('assistant', `Research could not be submitted: ${e.message}`); renderConversation(); composerStatus.textContent='Research submission failed; inspect the backend status.'; } return; }
    addMessage('user', text); addMessage('assistant', 'This local chat message is stored in this browser. Full conversational backend streaming is not yet exposed by Foundation.'); render();
  }

  function enqueue(text) { state.queue.push({id:crypto.randomUUID?.()||`${Date.now()}-${Math.random()}`, text, mode:currentMode()}); renderQueue(); if (!state.processing) processQueue(); }
  async function processQueue() { if (state.processing) return; state.processing=true; while(state.queue.length){ const item=state.queue.shift(); renderQueue(); if(item.mode==='research'){ try{ await submitResearch(item.text); } catch(e){ addMessage('assistant',`Queued research failed: ${e.message}`); renderConversation(); } } else { addMessage('user',item.text); addMessage('assistant','Queued local chat message processed. Full conversational backend streaming is not yet exposed.'); renderConversation(); } } state.processing=false; renderQueue(); }

  function handleAction(action) {
    if (action==='new-chat') return newChat();
    if (action==='open-sidebar') return openSidebar();
    if (action==='close-sidebar') return closeSidebar();
    if (action==='open-queue') return openQueue();
    if (action==='close-queue') return closeQueue();
    if (action==='close-workspace') return closeWorkspace();
    if (action==='backend-check') return backendCheck();
    if (action==='attachments') { const input=document.createElement('input'); input.type='file'; input.multiple=true; input.onchange=()=>{state.attachments=[...input.files]; showToast(`${state.attachments.length} file(s) selected locally`);}; input.click(); return; }
    if (action==='voice') { if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) { const Rec=window.SpeechRecognition||window.webkitSpeechRecognition; const rec=new Rec(); rec.lang='en-IN'; rec.onresult=e=>{prompt.value=e.results[0][0].transcript; prompt.dispatchEvent(new Event('input'));}; rec.start(); showToast('Listening…'); } else showToast('Voice input is not available in this browser'); return; }
    if (action==='send') return send();
    if (action==='clear-queue') { state.queue=[]; renderQueue(); return; }
    if (action==='search') return openSidebar();
  }

  document.addEventListener('click', (event) => {
    const action = event.target.closest('[data-action]'); if(action) { event.preventDefault(); handleAction(action.dataset.action); }
    const chat = event.target.closest('[data-chat]'); if(chat){ state.activeChatId=chat.dataset.chat; closeSidebar(); render(); }
    const starter = event.target.closest('[data-starter]'); if(starter){ document.querySelector('[data-mode="research"]').click(); prompt.value=starter.dataset.starter; prompt.focus(); }
    const mode = event.target.closest('[data-mode]'); if(mode){ document.querySelectorAll('[data-mode]').forEach(x=>x.classList.toggle('active',x===mode)); composerStatus.textContent=mode.dataset.mode==='research'?'Research submits to the real Worker API and tracks the run.':'Chat stays local until a conversational backend exists.'; }
    const remove = event.target.closest('[data-remove-queue]'); if(remove){ state.queue=state.queue.filter(q=>q.id!==remove.dataset.removeQueue); renderQueue(); }
  });
  prompt.addEventListener('keydown', e=>{ if(e.key==='Enter'&&!e.shiftKey){e.preventDefault(); send();} });
  prompt.addEventListener('input', ()=>{prompt.style.height='auto';prompt.style.height=`${Math.min(prompt.scrollHeight,130)}px`;});
  search.addEventListener('input', renderChats);
  window.addEventListener('keydown', e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();prompt.focus();} if(e.key==='Escape'){closeSidebar();closeQueue();closeWorkspace();}});

  loadChats(); if(state.chats.length) state.activeChatId=state.chats[0].id; else newChat(); render(); backendCheck();
})();
