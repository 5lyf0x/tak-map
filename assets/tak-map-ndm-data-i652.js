/* TAK Map i652: NDM Data modal in the existing Tools card.
 * UI only: operates on the authenticated i651 NDM catalog/import endpoints.
 * Import and registration NEVER activate Valhalla or overwrite NDM source files.
 */
(function (w, d) {
  'use strict';
  if (w.TakMapNDMDataI652) return;
  const BASE = '/api/tak-map/ndm/';
  const ID = 'takMapNDMModalI652';
  let root = null;
  let busy = false;
  let activeTab = 'existing';
  let lastFocus = null;
  let files = [];
  let catalog = [];
  let adminDenied = false;
  let maxUploadBytes = 4096*1024*1024;
  let showHistory = false;
  const byId = (id) => d.getElementById(id);
  const h = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (x) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
  const fmt = (n) => { const v=Number(n)||0; return v>=1073741824 ? (v/1073741824).toFixed(2)+' GiB' : (v/1048576).toFixed(1)+' MiB'; };
  const kind = (name) => /terrain/i.test(name) ? 'Elevation' : /routing|valhalla/i.test(name) ? 'Navigation' : 'NDM package';
  const label = (item) => [item.region, item.type === 'terrain' ? 'Elevation' : item.type === 'routing' ? 'Navigation' : 'NDM package'].filter(Boolean).join(' • ');

  function status(msg, tone) {
    const el=byId('takMapNDMStatusI652'); if(!el) return;
    el.textContent=msg || ''; el.dataset.tone=tone || 'normal';
  }
  function setBusy(value) {
    busy=!!value;
    if(!root)return;
    root.querySelectorAll('[data-ndm-operation]').forEach((el)=>{el.disabled=busy || (adminDenied && el.dataset.ndmOperation !== 'refresh');});
    const file=byId('takMapNDMFileI652'); if(file)file.disabled=busy || adminDenied;
    const close=byId('takMapNDMCloseI652'); if(close)close.disabled=busy;
  }
  function setTab(tab) {
    activeTab = tab === 'upload' ? 'upload' : 'existing';
    ['existing','upload'].forEach((t)=>{
      const panel=byId('takMapNDMTab'+(t==='existing'?'Existing':'Upload')+'I652');
      const button=byId('takMapNDMSelect'+(t==='existing'?'Existing':'Upload')+'I652');
      if(panel)panel.hidden=t!==activeTab;
      if(button){button.setAttribute('aria-selected',String(t===activeTab));button.tabIndex=t===activeTab?0:-1;}
    });
  }
  function renderExisting() {
    const el=byId('takMapNDMExistingRowsI652'); if(!el)return;
    if(adminDenied){el.innerHTML='<p class="ndm-muted">Administrator access is required to discover and register existing NDM packages.</p>';return;}
    if(!files.length){el.innerHTML='<p class="ndm-muted">No existing NDM ZIPs were discovered. Check that the TAK Map service can read the NDM package directories, or use Upload ZIP.</p>';return;}
    el.innerHTML=files.map((f,i)=>'<div class="ndm-row"><div class="ndm-row-info"><strong>'+h(f.name)+'</strong><small>'+h(kind(f.name))+' • '+fmt(f.size_bytes)+'</small></div><button class="layer-button" type="button" data-ndm-operation="register" data-index="'+i+'" '+(busy?'disabled':'')+'>Register</button></div>').join('');
    // Backend content hashes determine deduplication: filenames may be reused.
  }
  function renderCatalog() {
    const el=byId('takMapNDMRegisteredRowsI652'); if(!el)return;
    const rows=catalog.filter((e)=>showHistory||!e.superseded);
    if(!rows.length){el.innerHTML='<p class="ndm-muted">No current datasets registered. Turn on registration history to view older entries.</p>';return;}
    el.innerHTML=rows.map((e)=>{
      const current=e.status || (e.active?'Active':e.superseded?'Superseded':e.available===false?'Missing':'Available');
      const isActive=!!e.active;
      return '<div class="ndm-row"><div class="ndm-row-info"><strong>'+h(label(e))+'</strong><small>'+h(e.owner==='ndm-external'?'Existing NDM file · read-only':'Uploaded to TAK Map')+' • '+fmt(e.zip_size_bytes||e.source_size||e.size_bytes)+'</small></div>'+
        '<div class="ndm-actions"><span class="ndm-state '+((e.available===false||e.superseded)?'ndm-notavailable':'')+'">'+h(current)+'</span>'+
        '<button class="layer-button" type="button" data-ndm-operation="unregister" data-id="'+h(e.dataset_id)+'" '+(busy||isActive?'disabled title="Active graph must be switched before unregistering"':'')+'>Unregister</button></div></div>';
    }).join('');
  }
  async function unregisterDataset(id){
    if(busy || !/^[a-f0-9]{64}$/.test(id))return;
    const dataset=catalog.find((x)=>x.dataset_id===id);
    if(!dataset || dataset.active)return;
    if(!w.confirm('Unregister '+label(dataset)+' from TAK Map? This does not delete its NDM ZIP or any downloaded data.'))return;
    setBusy(true);
    let result='',tone='ok';
    try{
      const r=await w.fetch(BASE+'datasets/'+id,{method:'DELETE',credentials:'same-origin'});
      const body=await r.json();
      if(!r.ok||!body.ok)throw new Error(body.error||'Unregister failed');
      result='Registration removed. Original NDM files were not touched.';
    }catch(e){result='Unregister failed: '+e.message;tone='error'}
    finally{setBusy(false);await refresh();status(result,tone)}
  }
  async function jsonFetch(path,options) {
    const resp=await w.fetch(BASE+path,Object.assign({credentials:'same-origin',headers:{'Accept':'application/json'}},options||{}));
    let data;
    try{data=await resp.json();}catch(_){throw new Error('Server response was not JSON (HTTP '+resp.status+').');}
    if(!resp.ok || !data.ok){const error=new Error(data.error || ('HTTP '+resp.status));error.httpStatus=resp.status;throw error;}
    return data;
  }
  async function refresh() {
    if(busy)return;
    setBusy(true);status('Loading registered and available NDM datasets…');
    let problems=[];
    try{
      const r=await jsonFetch('catalog'); catalog=Array.isArray(r.datasets)?r.datasets:[];
      if(Number.isSafeInteger(r.max_upload_bytes) && r.max_upload_bytes>0)maxUploadBytes=r.max_upload_bytes;
      renderCatalog();
    }catch(e){problems.push('Catalog: '+e.message);}
    try{
      const r=await jsonFetch('discover'); files=Array.isArray(r.available)?r.available:[];adminDenied=false;renderExisting();
    }catch(e){if(e.httpStatus===403){adminDenied=true;files=[];renderExisting();problems.push('Only an administrator can register or upload datasets.');}
      else problems.push('Discovery: '+e.message);}
    setBusy(false);renderExisting();
    status(problems.length?problems.join(' '):catalog.length+' registered dataset(s); '+files.length+' existing ZIP(s) available.',problems.length?'warning':'ok');
  }
  async function register(index) {
    if(busy || adminDenied)return;
    const entry=files[index];if(!entry || !entry.discovery_id)return;
    setBusy(true);status('Validating '+entry.name+' and registering without copying the ZIP…');
    let result='',tone='ok';
    try{
      const r=await jsonFetch('register-existing',{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify({discovery_id:entry.discovery_id})});
      result=(r.duplicate?'Already registered: ':'Registered: ')+entry.name+'. NDM source file remains unchanged.';
    }catch(e){result='Registration failed: '+e.message;tone='error';}
    finally{setBusy(false);await refresh();status(result,tone);}
  }
  function uploadFile() {
    if(busy || adminDenied)return;
    const picker=byId('takMapNDMFileI652');const file=picker&&picker.files&&picker.files[0];
    if(!file){status('Choose an NDM navigation or elevation ZIP first.','warning');return;}
    if(!/\.zip$/i.test(file.name)){status('Select a ZIP file.','error');return;}
    if(!file.size){status('The ZIP file is empty.','error');return;}
    if(file.size>maxUploadBytes){status('This ZIP exceeds the '+fmt(maxUploadBytes)+' browser upload limit. Existing on Server has no ZIP file-size quota.','warning');return;}
    setBusy(true);status('Uploading '+file.name+' (0%)…');
    const xhr=new XMLHttpRequest();
    xhr.open('POST',BASE+'import');xhr.responseType='json';xhr.timeout=0; // large 4 GiB uploads must not hit a 30-minute total timeout
    xhr.setRequestHeader('Content-Type','application/zip');xhr.setRequestHeader('Accept','application/json');
    xhr.upload.onprogress=(event)=>{if(event.lengthComputable){const percent=Math.min(100,Math.round(100*event.loaded/event.total));status('Uploading '+file.name+' ('+percent+'%)… Validation may continue after upload.');}};
    xhr.onload=async()=>{
      const result=xhr.response&&typeof xhr.response==='object'?xhr.response:{};
      const successful=xhr.status>=200 && xhr.status<300 && result.ok;
      setBusy(false);
      if(successful){picker.value='';await refresh();status((result.duplicate?'Already registered: ':'Imported: ')+file.name+'. Routing service was not started.','ok');}
      else status('Import failed: '+(result.error || ('HTTP '+xhr.status))+'.','error');
    };
    xhr.onerror=()=>{setBusy(false);status('Upload failed. Check your connection and HTTPS certificate.','error');};
    xhr.ontimeout=()=>{setBusy(false);status('Upload timed out. Refresh the catalog before retrying to avoid duplicates.','error');};
    xhr.onabort=()=>{setBusy(false);status('Upload interrupted. Refresh the catalog before retrying.','warning');};
    xhr.send(file);
  }
  function close() {
    if(busy || !root)return;
    root.hidden=true;d.removeEventListener('keydown',onKeyDown,true);
    if(lastFocus && lastFocus.isConnected && lastFocus.focus)lastFocus.focus();
  }
  function onKeyDown(event) {
    if(!root || root.hidden)return;
    if(event.key==='Escape'){event.preventDefault();close();return;}
    if(event.key==='Tab'){
      const focus=Array.from(root.querySelectorAll('button:not(:disabled),input:not(:disabled),[tabindex="0"]')).filter((el)=>!el.closest('[hidden]'));
      if(!focus.length)return;
      const first=focus[0],last=focus[focus.length-1];
      if(event.shiftKey && d.activeElement===first){event.preventDefault();last.focus();}
      else if(!event.shiftKey && d.activeElement===last){event.preventDefault();first.focus();}
    }
  }
  function create() {
    if(root)return root;
    const style=d.createElement('style');style.id='takMapNDMStyleI652';style.textContent=`
      #${ID}[hidden],#${ID} [hidden]{display:none!important}
      #${ID}{position:fixed;inset:0;background:rgba(0,0,0,.73);z-index:16000;display:flex;align-items:center;justify-content:center;padding:18px}
      #${ID} .ndm-dialog{width:min(760px,100%);max-height:min(91vh,900px);overflow:auto;border:1px solid #465463;border-radius:15px;background:#111a23;color:#e8edf2;box-shadow:0 15px 75px #000c;padding:18px}
      #${ID} .ndm-head{display:flex;justify-content:space-between;align-items:flex-start;gap:15px;margin-bottom:13px}
      #${ID} h2{font-size:1.05rem;margin:0 0 6px;letter-spacing:0;color:#eef3fa;text-transform:none}
      #${ID} h3{font-size:.86rem;margin:12px 0 6px;color:#edf2f9}
      #${ID} .ndm-muted{color:#9eafbd;font-size:.79rem;line-height:1.45;margin:0 0 10px}
      #${ID} .ndm-tabs{display:flex;gap:8px;border-bottom:1px solid #31404e;padding-bottom:10px;margin-bottom:12px;flex-wrap:wrap}
      #${ID} button{cursor:pointer} #${ID} button:disabled{opacity:.48;cursor:default}
      #${ID} .ndm-tabs button{background:#1e2b38;color:#e8edf2;border:1px solid #354657;border-radius:9px;padding:8px 11px;font-weight:700}
      #${ID} .ndm-tabs button[aria-selected="true"]{border-color:#ff783c;background:#302720}
      #${ID} .ndm-close{background:transparent;border:1px solid #405363;border-radius:8px;padding:5px 10px;color:#e8edf2;font-size:1.2rem}
      #${ID} .ndm-row{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:10px 2px;border-bottom:1px solid #293642}
      #${ID} .ndm-row-info{min-width:0;overflow-wrap:anywhere} #${ID} .ndm-row strong{display:block;font-size:.84rem;font-weight:650}
      #${ID} .ndm-row small{display:block;color:#9eafbd;margin-top:4px;font-size:.73rem}
      #${ID} .ndm-section{max-height:260px;overflow:auto;border:1px solid #2b3b48;border-radius:9px;padding:3px 10px}
      #${ID} .ndm-actions .layer-button{padding:5px 8px;font-size:.72rem} #takMapNDMHistoryI655{accent-color:#3a99b1;vertical-align:middle;margin-right:6px} .ndm-state{font-size:.7rem;color:#75dfaf;white-space:nowrap} #${ID} .ndm-notavailable{color:#f2ac7d}
      #${ID} input[type="file"]{display:block;color:#e8edf2;max-width:100%;margin:12px 0}
      #${ID} .ndm-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
      #${ID} .ndm-note{margin-top:15px;border-top:1px solid #2b3b48;padding-top:12px}
      #${ID} #takMapNDMStatusI652{font-size:.79rem;min-height:1.6rem;color:#b4c5d0;margin-top:10px;overflow-wrap:anywhere}
      #${ID} #takMapNDMStatusI652[data-tone="error"]{color:#ff8c86}
      #${ID} #takMapNDMStatusI652[data-tone="warning"]{color:#f4c276}
      #${ID} #takMapNDMStatusI652[data-tone="ok"]{color:#7cddaf}
    `;d.head.appendChild(style);
    root=d.createElement('div');root.id=ID;root.hidden=true;
    root.innerHTML='<div class="ndm-dialog" role="dialog" aria-modal="true" aria-labelledby="takMapNDMTitleI652">'+
      '<div class="ndm-head"><div><h2 id="takMapNDMTitleI652">NDM Navigation & Elevation Data</h2><p class="ndm-muted">Add NDM routing graphs and terrain datasets to TAK Map. TAK Map automatically discovers rebuilt NDM packages. Unregistering never deletes source data.</p></div><button class="ndm-close" id="takMapNDMCloseI652" type="button" aria-label="Close NDM data">×</button></div>'+
      '<div class="ndm-tabs" role="tablist"><button id="takMapNDMSelectExistingI652" type="button" role="tab" aria-controls="takMapNDMTabExistingI652">Existing on Server</button><button id="takMapNDMSelectUploadI652" type="button" role="tab" aria-controls="takMapNDMTabUploadI652">Upload ZIP</button></div>'+
      '<section id="takMapNDMTabExistingI652" role="tabpanel"><p class="ndm-muted">Packages already installed by NDM. Register them without copying or modifying the originals.</p><div class="ndm-section" id="takMapNDMExistingRowsI652"><p class="ndm-muted">Loading available packages…</p></div></section>'+
      '<section id="takMapNDMTabUploadI652" role="tabpanel" hidden><p class="ndm-muted">Select an NDM navigation or terrain ZIP from your computer (up to 4 GiB by default). Existing on Server has no ZIP file-size quota. The server validates its manifest, graph or terrain database, and integrity before registering it.</p><input type="file" id="takMapNDMFileI652" accept=".zip,application/zip"><div class="ndm-actions"><button class="layer-button" id="takMapNDMUploadI652" data-ndm-operation="upload" type="button">Import ZIP</button></div></section>'+
      '<h3>Registered datasets</h3><label class="ndm-muted"><input type="checkbox" id="takMapNDMHistoryI655"> Show superseded registrations</label><div class="ndm-section" id="takMapNDMRegisteredRowsI652"><p class="ndm-muted">Loading catalog…</p></div>'+
      '<div class="ndm-note"><p class="ndm-muted">TAK Map starts a prepared, compatible local routing graph automatically with the server. Crossing state boundaries needs a connected multi-state routing graph.</p><div class="ndm-actions"><button class="layer-button" id="takMapNDMRefreshI652" data-ndm-operation="refresh" type="button">Refresh datasets</button></div><div id="takMapNDMStatusI652" role="status" aria-live="polite"></div></div>'+
      '</div>';
    d.body.appendChild(root);
    byId('takMapNDMCloseI652').addEventListener('click',close);
    root.addEventListener('click',(event)=>{if(event.target===root)close();});
    byId('takMapNDMSelectExistingI652').addEventListener('click',()=>setTab('existing'));
    byId('takMapNDMSelectUploadI652').addEventListener('click',()=>setTab('upload'));
    byId('takMapNDMRefreshI652').addEventListener('click',refresh);
    byId('takMapNDMHistoryI655').addEventListener('change',ev=>{showHistory=ev.target.checked;renderCatalog()});
    byId('takMapNDMRegisteredRowsI652').addEventListener('click',event=>{const button=event.target.closest('[data-ndm-operation="unregister"]');if(button)unregisterDataset(button.dataset.id)});
    byId('takMapNDMUploadI652').addEventListener('click',uploadFile);
    byId('takMapNDMExistingRowsI652').addEventListener('click',(event)=>{
      const button=event.target&&event.target.closest('[data-ndm-operation="register"]');
      if(button)register(Number(button.dataset.index));
    });
    setTab('existing');return root;
  }
  function open() {
    const dialog=create();lastFocus=d.activeElement;
    setTab('existing');dialog.hidden=false;
    d.addEventListener('keydown',onKeyDown,true);
    byId('takMapNDMCloseI652').focus();refresh();
  }
  w.openTakMapNDMData=open;
  w.TakMapNDMDataI652=Object.freeze({open,close,refresh,version:'i652'});
})(window, document);
