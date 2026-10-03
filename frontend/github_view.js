(() => {
  'use strict';
  const api = window.RIEFrontend;
  if (!api) return;
  let githubToken = '';
  let repository = 'Z-Solo-King/foundation';
  let lastAction = 'repo';
  let resultText = '';

  const ACTIONS = [
    ['repo','Repository overview','read'],['issues_list','List issues','read'],['issue_get','Get issue','read'],
    ['issue_create','Create issue','write'],['issue_update','Update issue','write'],['issue_comment','Comment on issue','write'],
    ['issue_lock','Lock issue','write'],['issue_unlock','Unlock issue','write'],['pr_list','List pull requests','read'],
    ['pr_get','Get pull request','read'],['pr_comments','PR comments','read'],['pr_create','Create pull request','write'],
    ['pr_update','Update pull request','write'],['pr_comment','Comment on pull request','write'],['pr_review','Create PR review','write'],
    ['pr_merge','Merge pull request','write'],['workflows_list','List workflows','read'],['runs_list','List workflow runs','read'],
    ['run_get','Get workflow run','read'],['workflow_dispatch','Dispatch workflow','write'],['workflow_cancel','Cancel workflow run','write'],
    ['workflow_rerun_failed','Re-run failed jobs','write'],['branches_list','List branches','read'],['branch_create','Create branch','write'],
    ['branch_delete','Delete branch','write'],['commits_list','List commits','read'],['commit_get','Get commit','read'],
    ['file_get','Read file','read'],['file_write','Create/update file','write'],['releases_list','List releases','read'],
    ['release_create','Create release','write'],['release_delete','Delete release','write'],['tags_list','List tags','read'],['rate_limit','GitHub API rate limit','read']
  ];
  const quick=[['repo','Overview'],['issues_list','Issues'],['pr_list','PRs'],['workflows_list','Workflows'],['runs_list','Runs'],['branches_list','Branches'],['commits_list','Commits'],['releases_list','Releases'],['tags_list','Tags'],['rate_limit','Rate limit']];
  const esc=v=>api.escapeHtml(String(v??''));
  const isWrite=a=>ACTIONS.find(([id])=>id===a)?.[2]==='write';

  function defaults(action){
    const b={action,repository};
    if(['issue_get','issue_update','issue_comment','issue_lock','issue_unlock','pr_get','pr_comments','pr_update','pr_comment','pr_review','pr_merge'].includes(action))b.number='';
    if(['run_get','workflow_cancel','workflow_rerun_failed'].includes(action))b.run_id='';
    if(action==='workflow_dispatch')Object.assign(b,{workflow:'',ref:'main',inputs:{}});
    if(action==='branch_create')Object.assign(b,{branch:'',source:''});
    if(action==='branch_delete')b.branch='';
    if(action==='commit_get')b.sha='';
    if(action==='file_get')Object.assign(b,{path:'',ref:'main'});
    if(action==='file_write')Object.assign(b,{path:'',content:'',message:'',branch:''});
    if(action==='release_create')Object.assign(b,{tag_name:'',name:'',body:'',target_commitish:'main',draft:false,prerelease:false});
    if(action==='release_delete')b.release_id='';
    if(action==='pr_create')Object.assign(b,{title:'',body:'',head:'',base:'main',draft:false});
    if(action==='pr_review')Object.assign(b,{body:'',event:'COMMENT'});
    
    if(action==='issue_create')Object.assign(b,{title:'',body:'',labels:[],assignees:[],milestone:null});
    if(action==='issue_update'||action==='pr_update')b.body={};
    if(action==='issue_comment'||action==='pr_comment')b.body='';
    return b;
  }

  function render(){
    const connected=Boolean(githubToken);
    const options=ACTIONS.map(([id,label,kind])=>'<option value="'+esc(id)+'" '+(id===lastAction?'selected':'')+'>'+esc(label)+(kind==='write'?' - mutation':'')+'</option>').join('');
    const quickHtml=quick.map(([id,label])=>'<button class="secondary github-quick" data-github-action="'+esc(id)+'">'+esc(label)+'</button>').join('');
    return '<div class="message view-panel github-view">'+
      '<div class="view-heading"><div><span class="eyebrow">GitHub</span><h2>Repository workspace</h2><p>Read and operate on the project repositories through an explicit GitHub credential. The token stays in memory for this tab and is never written to chatbot storage.</p></div>'+
      '<span class="status-dot '+(connected?'ok':'')+'">'+(connected?'Connected for this tab':'Not connected')+'</span></div>'+
      '<section class="workspace-card"><div class="github-grid">'+
      '<div><label class="field-label" for="github-token">GitHub access token</label><input id="github-token" type="password" autocomplete="off" placeholder="Fine-grained PAT / short-lived App token" value=""></div>'+
      '<div><label class="field-label" for="github-repo">Repository</label><select id="github-repo"><option value="Z-Solo-King/foundation" '+(repository==='Z-Solo-King/foundation'?'selected':'')+'>Z-Solo-King/foundation</option><option value="Z-Solo-King/operations" '+(repository==='Z-Solo-King/operations'?'selected':'')+'>Z-Solo-King/operations</option></select></div>'+
      '</div><div class="card-actions"><button class="primary" data-action="github-connect">'+(connected?'Reconnect':'Connect GitHub')+'</button><button class="secondary" data-action="github-clear">Clear</button><span class="github-note">Use the narrowest repository permissions needed.</span></div></section>'+
      '<section class="workspace-card"><div class="card-head"><strong>Quick access</strong><span>Core project surfaces</span></div><div class="github-quick-grid">'+quickHtml+'</div></section>'+
      '<section class="workspace-card"><div class="card-head"><strong>GitHub operation</strong><span>'+(connected?'Credential available':'Connect first')+'</span></div>'+
      '<div class="github-operation-grid"><div><label class="field-label" for="github-action">Action</label><select id="github-action">'+options+'</select></div>'+
      '<div><label class="field-label" for="github-payload">Parameters JSON</label><textarea id="github-payload" rows="12" spellcheck="false">'+esc(JSON.stringify(defaults(lastAction),null,2))+'</textarea></div></div>'+
      '<div class="github-warning '+(isWrite(lastAction)?'visible':'')+'">'+(isWrite(lastAction)?'Mutation: execution requires explicit browser confirmation and a GitHub token with matching scope.':'Read-only operation.')+'</div>'+
      '<div class="card-actions"><button class="primary" data-action="github-execute" '+(connected?'':'disabled')+'>Execute</button></div></section>'+
      '<section class="workspace-card"><div class="card-head"><strong>Result</strong><span>'+(resultText?'Latest response':'No request yet')+'</span></div><pre class="github-result" aria-live="polite">'+esc(resultText||'Connect GitHub and run an operation.')+'</pre></section></div>';
  }

  async function execute(action,payload=null){
    if(!githubToken){resultText='GitHub connection required. The token is kept only in memory for this tab.';api.chatView?.renderView();return;}
    lastAction=action;
    const body=payload||(()=>{const raw=document.getElementById('github-payload')?.value||'';try{return JSON.parse(raw)}catch(error){throw new Error('Invalid parameters JSON: '+error.message)}})();
    body.action=action;body.repository=repository;
    if(isWrite(action)){if(!window.confirm('GitHub mutation: '+action+' on '+repository+'. Execute it?')){resultText='Mutation cancelled before any GitHub request was sent.';api.chatView?.renderView();return;}body.confirm=true;}
    try{const response=await fetch(api.apiUrl('/api/v1/github'),{method:'POST',headers:{Accept:'application/json','Content-Type':'application/json','X-GitHub-Access-Token':githubToken},body:JSON.stringify(body)});const data=await response.json().catch(()=>({ok:false,error:'HTTP '+response.status}));resultText=JSON.stringify(data,null,2);}
    catch(error){resultText='Request failed: '+(error.message||error);}
    api.chatView?.renderView();
  }

  document.addEventListener('change',event=>{
    if(event.target.id==='github-repo'){repository=event.target.value;api.chatView?.renderView();}
    if(event.target.id==='github-action'){lastAction=event.target.value;resultText='';api.chatView?.renderView();}
  });
  document.addEventListener('click',event=>{
    const quickButton=event.target.closest('[data-github-action]');
    if(quickButton){event.preventDefault();void execute(quickButton.dataset.githubAction,{action:quickButton.dataset.githubAction,repository});return;}
    if(event.target.closest('[data-action="github-connect"]')){event.preventDefault();const input=document.getElementById('github-token');const value=input?.value.trim()||'';if(!value){resultText='Enter a GitHub access token first.';api.chatView?.renderView();return;}githubToken=value;resultText='GitHub token loaded into memory for this tab.';api.chatView?.renderView();return;}
    if(event.target.closest('[data-action="github-clear"]')){event.preventDefault();githubToken='';resultText='GitHub token cleared from memory.';api.chatView?.renderView();return;}
    if(event.target.closest('[data-action="github-execute"]')){event.preventDefault();const action=document.getElementById('github-action')?.value||lastAction;try{void execute(action)}catch(error){resultText=error.message||String(error);api.chatView?.renderView();}}
  });
  api.githubView=Object.freeze({render,connected:()=>Boolean(githubToken)});
})();