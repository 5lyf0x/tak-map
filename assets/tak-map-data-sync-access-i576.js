/* TAK Map i576 authoritative Mission-row access controls and sidebar visual polish. */
(() => {
  'use strict';
  if (window.TakMapMissionAccessI576) return;

  const VERSION = 'i602';
  const API = '/api/tak-map/data-sync-mission-access-i573';
  const state = {status:new Map(), pending:new Map(), activeMission:'', unknownRefreshIssued:false};
  const text = value => String(value == null ? '' : value).trim();
  const key = mission => text(mission).toLowerCase();

  let renderScheduled = false;
  let primeTimer = 0;

  function currentPayload() {
    try { return typeof lastDataSync !== 'undefined' ? lastDataSync : window.lastDataSync; }
    catch (_) { return window.lastDataSync || window.__takMapLastDataSyncJsonI553 || null; }
  }

  function missionNames(payload = currentPayload()) {
    const out = [], seen = new Set();
    for (const row of (payload && Array.isArray(payload.missions) ? payload.missions : [])) {
      const mission = text(typeof row === 'string' ? row : (row && (row.name || row.mission_name || row.missionName || row.uid)));
      const k = key(mission);
      if (!mission || seen.has(k)) continue;
      seen.add(k); out.push(mission);
    }
    return out;
  }

  function renderAuthoritativeRows() {
    renderScheduled = false;
    try {
      if (typeof window.renderDataSyncRows === 'function') window.renderDataSyncRows();
      else if (typeof renderDataSyncRows === 'function') renderDataSyncRows();
    } catch (_) {}
  }

  function queueRender(delay = 0) {
    if (renderScheduled) return;
    renderScheduled = true;
    setTimeout(renderAuthoritativeRows, Math.max(0, Number(delay) || 0));
  }

  async function primeStatuses(force = false) {
    clearTimeout(primeTimer);
    // The completed Data Sync snapshot is the sole access-state authority. Do
    // not fan out per-Mission status requests or start follow-up refresh loops.
    const count = ingest(currentPayload());
    queueRender(0);
    return count;
  }

  async function refreshAfterUnlock(mission) {
    try {
      if (typeof window.refreshDataSync === 'function') await window.refreshDataSync(true, 'mission-unlocked-i602');
      else if (typeof refreshDataSync === 'function') await refreshDataSync(true, 'mission-unlocked-i602');
    } catch (_) {}
    ingest(currentPayload());
    queueRender(0);
    return true;
  }

  async function readJson(response) {
    const raw = await response.text();
    let body = {};
    try { body = raw ? JSON.parse(raw) : {}; }
    catch (_) { body = {error:raw || `HTTP ${response.status}`}; }
    if (!response.ok || body.ok === false) {
      const error = new Error(body.error || `HTTP ${response.status}`);
      error.status = response.status;
      error.payload = body;
      throw error;
    }
    return body;
  }

  function truthy(value) {
    return value === true || value === 1 || ['1','true','yes','on'].includes(text(value).toLowerCase());
  }

  function firstAccessRows(payload) {
    if (!payload || typeof payload !== 'object') return [];
    let fallback = [];
    for (const name of ['mission_access_i599','mission_access_i596','mission_access_i595','mission_access_i594','mission_access_i591','mission_access_i576','mission_access_i575','mission_access_i573','mission_access_i572']) {
      const rows = payload[name];
      if (!Array.isArray(rows)) continue;
      fallback = rows;
      if (rows.length) return rows;
    }
    return fallback;
  }

  function payloadHasAuthorizedMissionData(payload, mission) {
    const wanted = key(mission);
    if (!wanted || !payload || typeof payload !== 'object') return false;
    for (const row of (Array.isArray(payload.missions) ? payload.missions : [])) {
      const name = text(typeof row === 'string' ? row : (row && (row.name || row.mission || row.mission_name || row.missionName || row.uid)));
      if (key(name) === wanted && !truthy(row && row.metadata_only)) return true;
    }
    for (const collection of ['objects','packages','mission_content']) {
      for (const row of (Array.isArray(payload[collection]) ? payload[collection] : [])) {
        const name = text(row && (row.mission || row.mission_name || row.missionName || row.missionTitle));
        if (key(name) === wanted) return true;
      }
    }
    return false;
  }

  function normalize(mission, body) {
    body = Object.assign({}, body || {});
    const protectedMission = truthy(body.protected != null ? body.protected : body.password_protected);
    const unlocked = protectedMission ? truthy(body.unlocked) : true;
    return Object.assign(body, {
      ok:true,
      version:VERSION,
      mission:text(mission),
      protected:protectedMission,
      password_protected:protectedMission,
      unlocked,
      locked:Boolean(protectedMission && !unlocked),
    });
  }

  function mergeStatus(previous, incoming, authority='snapshot') {
    if (!incoming) return previous;
    if (!previous || authority === 'direct' || authority === 'action') return incoming;
    // A completed backend snapshot is authoritative, including relock/token
    // expiry. Never preserve an older unlocked value with boolean OR.
    return incoming;
  }

  function remember(mission, body, authority='snapshot') {
    const k = key(mission);
    const incoming = normalize(mission, body);
    const merged = mergeStatus(state.status.get(k), incoming, authority);
    state.status.set(k, merged);
    return merged;
  }

  function ingest(payload) {
    if (!payload || typeof payload !== 'object') return 0;
    const rows = firstAccessRows(payload);
    let count = 0;
    if (Array.isArray(rows)) {
      for (const row of rows) {
        const mission = text(row && row.mission);
        if (!mission) continue;
        const incoming = Object.assign({}, row);
        remember(mission, incoming, 'snapshot');
        count += 1;
      }
    }
    return count;
  }

  function embeddedAccess(mission) {
    let payload = null;
    try { payload = typeof lastDataSync !== 'undefined' ? lastDataSync : window.lastDataSync; }
    catch (_) { payload = window.lastDataSync; }
    const rows = firstAccessRows(payload);
    const found = Array.isArray(rows) ? rows.find(row => key(row && row.mission) === key(mission)) : null;
    if (!found) return null;
    const info = remember(mission, found, 'snapshot');
    queueRender(0);
    return info;
  }

  function peek(mission) {
    mission = text(mission);
    return state.status.get(key(mission)) || embeddedAccess(mission) || null;
  }

  async function status(mission, force = false) {
    mission = text(mission);
    if (!mission) return normalize('', {protected:false, unlocked:true});
    const k = key(mission);
    if (!force && state.status.has(k)) return state.status.get(k);
    if (!force) {
      const embedded = embeddedAccess(mission);
      if (embedded) return embedded;
    }
    if (state.pending.has(k)) return state.pending.get(k);
    const task = fetch(`${API}?mission=${encodeURIComponent(mission)}`, {
      cache:'no-store', credentials:'same-origin'
    }).then(readJson).then(body => {
      const info = remember(mission, body, 'direct');
      queueRender(0);
      return info;
    }).finally(() => state.pending.delete(k));
    state.pending.set(k, task);
    return task;
  }

  async function action(mission, actionName, password = '') {
    mission = text(mission);
    const body = await readJson(await fetch(API, {
      method:'POST', headers:{'Content-Type':'application/json'}, credentials:'same-origin', cache:'no-store',
      body:JSON.stringify({action:actionName, mission, password})
    }));
    if (actionName === 'unlock' && truthy(body && body.unlocked)) body.content_state_i599 = 'loading';
    if (actionName === 'clear') body.content_state_i599 = 'locked';
    return remember(mission, body, 'action');
  }

  function ensureStyles() {
    if (document.getElementById('takMapMissionAccessStyleI576')) return;
    const style = document.createElement('style');
    style.id = 'takMapMissionAccessStyleI576';
    style.textContent = `
      #dataSyncRows .tak-mission-card-i576{display:flex!important;align-items:center!important;gap:10px!important}
      #dataSyncRows .tak-mission-main-i576{min-width:0;flex:1;display:flex;flex-direction:column;gap:2px}
      #dataSyncRows .tak-mission-access-i576{margin-left:auto;flex:0 0 auto;display:flex;align-items:center;gap:6px}
      #dataSyncRows .tak-mission-control-i576{font-family:Rajdhani,"Arial Narrow",Arial,sans-serif!important;font-size:10px!important;line-height:1!important;font-weight:800!important;letter-spacing:0!important;white-space:nowrap!important;min-height:24px!important;height:24px!important}
      #dataSyncRows .tak-mission-state-i576{display:inline-flex;align-items:center;justify-content:center;min-width:60px;padding:0 8px;border:1px solid #596874;border-radius:999px;background:#17242e;color:#ccd4da}
      #dataSyncRows .tak-mission-state-i576.unlocked{border-color:rgba(117,181,143,.70);background:rgba(40,104,67,.22);color:#ccebd8}
      #dataSyncRows .tak-mission-state-i576.locked{border-color:rgba(205,164,99,.72);background:rgba(112,73,22,.24);color:#f0d59f}
      #dataSyncRows .tak-mission-edit-i576{min-width:45px!important;padding:0 8px!important;margin:0!important}

      #takMapMissionAccessDialogI576{position:fixed;inset:0;z-index:7800;display:flex;align-items:center;justify-content:center;padding:20px;background:rgba(0,0,0,.68)}
      #takMapMissionAccessDialogI576[hidden]{display:none!important}
      #takMapMissionAccessDialogI576 .mission-access-card-i576{position:relative;z-index:1;width:min(450px,calc(100vw - 32px));overflow:hidden;border:1px solid #74828d;border-radius:13px;background:linear-gradient(180deg,#192733,#0b151e);box-shadow:0 28px 90px rgba(0,0,0,.78);color:#edf1f4}
      #takMapMissionAccessDialogI576 .mission-access-head-i576{padding:15px 17px 12px;border-bottom:1px solid rgba(203,210,216,.22)}
      #takMapMissionAccessDialogI576 h2{margin:0 0 5px;font-size:17px}
      #takMapMissionAccessDialogI576 p{margin:0;color:#b8c2ca;font-size:11.5px;line-height:1.45}
      #takMapMissionAccessDialogI576 .mission-access-body-i576{padding:14px 17px 17px}
      #takMapMissionAccessDialogI576 label{display:block;margin-bottom:6px;color:#d7dde2;font-size:11px;font-weight:800}
      #takMapMissionAccessDialogI576 .mission-access-name-i591{margin-bottom:11px}
      #takMapMissionAccessDialogI576 input{box-sizing:border-box;width:100%;height:39px;padding:0 11px;border:1px solid #687682;border-radius:8px;background:#08121a;color:#f2f5f7;font:inherit;outline:none}
      #takMapMissionAccessDialogI576 input:focus{border-color:#d4dbe0;box-shadow:0 0 0 2px rgba(203,210,216,.18)}
      #takMapMissionAccessDialogI576 .mission-access-current-i576{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px;padding:9px 10px;border:1px solid rgba(203,210,216,.18);border-radius:8px;background:rgba(4,10,15,.34);font-size:11px}
      #takMapMissionAccessDialogI576 .mission-access-status-i576{min-height:19px;margin-top:8px;color:#c8d0d6;font-size:10.5px;line-height:1.4}
      #takMapMissionAccessDialogI576 .mission-access-status-i576.error{color:#efb0aa}
      #takMapMissionAccessDialogI576 .mission-access-status-i576.ok{color:#bce2ca}
      #takMapMissionAccessDialogI576 .mission-access-actions-i576{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:13px}
      #takMapMissionAccessDialogI576 .mission-access-actions-i576 button{box-sizing:border-box;width:100%;min-width:0;min-height:36px;height:36px;margin:0;padding:0 10px;border:1px solid #687682;border-radius:8px;background:#17242e;color:#e9edf0;font-size:10px;font-weight:800;white-space:nowrap;cursor:pointer}
      #takMapMissionAccessDialogI576 .mission-access-actions-i576 button.primary{border-color:#e0e5e8;background:linear-gradient(180deg,#dde3e7,#aeb8bf);color:#111920}
      #takMapMissionAccessDialogI576 .mission-access-actions-i576 button.clear{border-color:rgba(205,125,116,.58);color:#f1c5c1;background:rgba(112,36,31,.2)}
      #takMapMissionAccessDialogI576 button:disabled{opacity:.55;cursor:wait}

      #sidebar,.sidebar,#dataSyncRows,#dataSyncRows .datasync-section-list{scrollbar-color:#7f8d97 #111a21!important;scrollbar-width:thin!important}
      #sidebar::-webkit-scrollbar,.sidebar::-webkit-scrollbar,#dataSyncRows::-webkit-scrollbar,#dataSyncRows .datasync-section-list::-webkit-scrollbar{width:10px;height:10px}
      #sidebar::-webkit-scrollbar-track,.sidebar::-webkit-scrollbar-track,#dataSyncRows::-webkit-scrollbar-track,#dataSyncRows .datasync-section-list::-webkit-scrollbar-track{background:#111a21!important}
      #sidebar::-webkit-scrollbar-thumb,.sidebar::-webkit-scrollbar-thumb,#dataSyncRows::-webkit-scrollbar-thumb,#dataSyncRows .datasync-section-list::-webkit-scrollbar-thumb{background:linear-gradient(180deg,#98a4ac,#64727c)!important;border:2px solid #111a21!important;border-radius:999px!important}
      #sidebar::-webkit-scrollbar-thumb:hover,.sidebar::-webkit-scrollbar-thumb:hover,#dataSyncRows::-webkit-scrollbar-thumb:hover,#dataSyncRows .datasync-section-list::-webkit-scrollbar-thumb:hover{background:linear-gradient(180deg,#b0bac1,#798790)!important}
      .sidebar .panel>h2:hover,.sidebar .panel>h2:focus-visible,.sidebar .tak-card-header-v491:hover,.sidebar .tak-card-header-v491:focus-visible{background:transparent!important;color:#c8d2da!important;box-shadow:none!important}
      #adsbMenuHostV316 .adsb-stepper-buttons{background:rgba(123,137,147,.10)!important;border-left-color:rgba(123,137,147,.48)!important}
      #adsbMenuHostV316 .adsb-stepper-buttons button{color:#c8d0d6!important;background:linear-gradient(180deg,rgba(118,132,142,.34),rgba(64,76,85,.28))!important;border-color:rgba(133,147,157,.58)!important;text-shadow:none!important}
      #adsbMenuHostV316 .adsb-stepper-buttons button:hover,#adsbMenuHostV316 .adsb-stepper-buttons button:focus{color:#fff!important;background:linear-gradient(180deg,rgba(145,158,167,.46),rgba(78,90,99,.40))!important;border-color:rgba(175,185,192,.75)!important}
      #takMapPointEditorI556 [data-i576-access-locked="1"],#pointEditPanel [data-i576-access-locked="1"]{opacity:.58;cursor:not-allowed!important}
    `;
    document.head.appendChild(style);
  }

  function dialog() {
    ensureStyles();
    let root = document.getElementById('takMapMissionAccessDialogI576');
    if (root) return root;
    root = document.createElement('div');
    root.id = 'takMapMissionAccessDialogI576';
    root.hidden = true;
    root.innerHTML = `
      <form class="mission-access-card-i576" autocomplete="off">
        <div class="mission-access-head-i576"><h2>Mission Password</h2><p class="mission-access-copy-i576"></p></div>
        <div class="mission-access-body-i576">
          <div class="mission-access-current-i576"><span>Status</span><b class="mission-access-state-i576">Locked</b></div>
          <div class="mission-access-name-i591" hidden>
            <label for="takMapMissionNameI591">Mission name</label>
            <input id="takMapMissionNameI591" type="text" autocomplete="off" maxlength="180" spellcheck="false" autocapitalize="off" autocorrect="off">
          </div>
          <label for="takMapMissionPasswordI576">Enter or replace password</label>
          <input id="takMapMissionPasswordI576" type="password" autocomplete="new-password" maxlength="512" spellcheck="false">
          <div class="mission-access-status-i576" aria-live="polite"></div>
          <div class="mission-access-actions-i576">
            <button type="button" class="clear" data-clear>Clear Password</button>
            <button type="button" data-cancel>Cancel</button>
            <button type="submit" class="primary">Save Password</button>
          </div>
        </div>
      </form>`;
    document.body.appendChild(root);
    root.addEventListener('click', event => { if (event.target === root) closeDialog(); });
    return root;
  }

  function closeDialog() {
    const root = document.getElementById('takMapMissionAccessDialogI576');
    if (!root) return;
    for (const input of root.querySelectorAll('input')) input.value = '';
    root.hidden = true;
    state.activeMission = '';
  }

  function rerender() {
    try { ingest(currentPayload()); } catch (_) {}
    queueRender(0);
    setTimeout(enforceProtectedActions, 10);
  }


  async function openDialog(mission) {
    mission = text(mission);
    if (!mission) return false;
    const manual = false;
    const root = dialog();
    const form = root.querySelector('form');
    const missionWrap = root.querySelector('.mission-access-name-i591');
    const missionInput = root.querySelector('#takMapMissionNameI591');
    const input = root.querySelector('#takMapMissionPasswordI576');
    const copy = root.querySelector('.mission-access-copy-i576');
    const current = root.querySelector('.mission-access-state-i576');
    const message = root.querySelector('.mission-access-status-i576');
    const submit = root.querySelector('button[type="submit"]');
    const cancel = root.querySelector('[data-cancel]');
    const clear = root.querySelector('[data-clear]');
    state.activeMission = mission;
    root.hidden = false;
    missionWrap.hidden = !manual;
    missionInput.value = mission;
    input.value = '';
    message.className = 'mission-access-status-i576';
    let info = null;
    if (manual) {
      copy.textContent = 'Enter the exact OpenTAKServer Mission name and its password. TAK Map will not download or display protected Mission data until OpenTAKServer accepts the password.';
      current.textContent = 'Locked';
      clear.disabled = true;
      message.textContent = 'Mission access has not been established for this signed-in TAK Map account.';
      setTimeout(() => missionInput.focus(), 0);
    } else {
      copy.textContent = `${mission} is password protected in OpenTAKServer. The accepted password is stored encrypted for only your signed-in TAK Map account.`;
      message.textContent = 'Checking Mission access…';
      try { info = await status(mission, true); }
      catch (error) { info = normalize(mission,{protected:true,unlocked:false}); message.textContent = error.message || String(error); message.classList.add('error'); }
      current.textContent = info.unlocked ? 'Unlocked' : 'Locked';
      clear.disabled = !info.password_stored_server_side && !info.credential_configured && !info.unlocked;
      if (!message.classList.contains('error')) message.textContent = info.unlocked ? 'A password is stored and currently accepted by OpenTAKServer.' : 'Enter the Mission password to unlock protected read and write operations.';
      setTimeout(() => input.focus(), 0);
    }

    cancel.onclick = closeDialog;
    clear.onclick = async () => {
      const selectedMission = text(missionInput.value || state.activeMission);
      if (!selectedMission) { message.textContent = 'Enter the Mission name.'; message.className = 'mission-access-status-i576 error'; missionInput.focus(); return; }
      clear.disabled = cancel.disabled = submit.disabled = true;
      message.textContent = 'Clearing the stored password…'; message.className = 'mission-access-status-i576';
      try {
        info = await action(selectedMission,'clear');
        current.textContent = 'Locked'; input.value = '';
        message.textContent = 'Stored Mission password cleared. Mission data is now locked and removed.'; message.classList.add('ok');
        rerender(); void refreshAfterUnlock(selectedMission);
      } catch (error) { message.textContent = error.message || String(error); message.classList.add('error'); }
      finally { clear.disabled = true; cancel.disabled = submit.disabled = false; }
    };
    form.onsubmit = async event => {
      event.preventDefault();
      const selectedMission = text(missionInput.value || state.activeMission);
      const password = input.value;
      if (!selectedMission) { message.textContent = 'Enter the Mission name.'; message.className = 'mission-access-status-i576 error'; missionInput.focus(); return; }
      if (!password) { message.textContent = 'Enter the Mission password.'; message.className = 'mission-access-status-i576 error'; input.focus(); return; }
      clear.disabled = cancel.disabled = submit.disabled = true;
      message.textContent = 'Validating with OpenTAKServer…'; message.className = 'mission-access-status-i576';
      try {
        info = await action(selectedMission,'unlock',password);
        state.activeMission = selectedMission;
        input.value = ''; current.textContent = 'Unlocked';
        message.textContent = 'Password accepted and stored securely for this Mission.'; message.classList.add('ok');
        clear.disabled = false; rerender(); void refreshAfterUnlock(selectedMission); setTimeout(closeDialog,550);
      } catch (error) {
        input.value = ''; message.textContent = error.message || String(error); message.classList.add('error'); input.focus();
      } finally {
        cancel.disabled = submit.disabled = false;
        if (!info || !info.unlocked) clear.disabled = true;
      }
    };
    return true;
  }

  function openManual() { return false; }

  function selectedCreateMission() {
    const destination = document.getElementById('pointSaveDestinationI556');
    if (!destination || destination.value !== 'mission') return '';
    return text(document.getElementById('pointMissionI556')?.value);
  }
  function editorMission() {
    const modal = document.getElementById('takMapPointEditorI556');
    if (!modal || !modal.classList.contains('active')) return '';
    const label = document.getElementById('pointEditorContextLabelI556');
    if (text(label?.textContent).toLowerCase() !== 'mission') return '';
    return text(document.getElementById('pointEditorContextI556')?.value);
  }
  function setInlineStatus(id,message) { const node=document.getElementById(id); if(node){node.textContent=message;node.classList.add('error');node.classList.remove('ok');} }

  async function enforceCreateAccess(force=false) {
    const mission=selectedCreateMission(), save=document.getElementById('pointSaveI556');
    if(!save||!mission){if(save&&save.dataset.i576AccessLocked==='1'){delete save.dataset.i576AccessLocked;save.removeAttribute('data-i576-access-locked');save.disabled=false;}return true;}
    let info; try{info=await status(mission,force);}catch(_){return true;}
    if(info.protected&&!info.unlocked){save.dataset.i576AccessLocked='1';save.setAttribute('data-i576-access-locked','1');save.disabled=true;setInlineStatus('pointSaveStatusI556',`Mission is locked. Use Edit beside ${mission} in the Data Sync Missions row to enter its password.`);return false;}
    if(save.dataset.i576AccessLocked==='1'){delete save.dataset.i576AccessLocked;save.removeAttribute('data-i576-access-locked');save.disabled=false;} return true;
  }
  async function enforceEditorAccess(force=false) {
    const mission=editorMission(), save=document.getElementById('pointEditorSaveI556');
    if(!save||!mission)return true;
    let info; try{info=await status(mission,force);}catch(_){return true;}
    if(info.protected&&!info.unlocked){save.dataset.i576AccessLocked='1';save.setAttribute('data-i576-access-locked','1');save.disabled=true;setInlineStatus('pointEditorStatusI556',`Mission is locked. Use Edit beside ${mission} in the Data Sync Missions row to enter its password.`);return false;}
    if(save.dataset.i576AccessLocked==='1'){delete save.dataset.i576AccessLocked;save.removeAttribute('data-i576-access-locked');try{if(typeof window.markEditorDirty==='function')window.markEditorDirty();}catch(_){}} return true;
  }
  function enforceProtectedActions(){void enforceCreateAccess(false);void enforceEditorAccess(false);}

  function installEvents() {
    document.addEventListener('click', event => {
      const manual = event.target?.closest?.('[data-mission-manual-i591]');
      if (manual) { event.preventDefault(); event.stopPropagation(); void openManual(); return; }
      const edit = event.target?.closest?.('[data-mission-edit-i576]');
      if (edit) { event.preventDefault(); event.stopPropagation(); void openDialog(edit.getAttribute('data-mission') || ''); return; }
      const target = event.target?.closest?.('#pointSaveI556,#pointEditorSaveI556');
      if (!target) return;
      const mission = target.id === 'pointSaveI556' ? selectedCreateMission() : editorMission();
      const info = peek(mission);
      if (info && info.protected && !info.unlocked) {
        event.preventDefault(); event.stopImmediatePropagation();
        setInlineStatus(target.id === 'pointSaveI556' ? 'pointSaveStatusI556' : 'pointEditorStatusI556', `Mission is locked. Use Edit beside ${mission} in the Data Sync Missions row to enter its password.`);
      }
    }, true);
    document.addEventListener('change', event => { if(['pointSaveDestinationI556','pointMissionI556'].includes(event.target?.id)) setTimeout(()=>void enforceCreateAccess(true),0); }, true);
    document.addEventListener('click', event => { if(event.target?.closest?.('[data-i556-point-edit],.point-popup-edit-i556')){setTimeout(()=>void enforceEditorAccess(true),120);setTimeout(()=>void enforceEditorAccess(true),500);} }, false);
  }

  function replaceLegacy() {
    const compatible = {version:VERSION,status,open:openDialog,openManual,unlock:(m,p)=>action(m,'unlock',p),clear:m=>action(m,'clear'),peek,ingest,primeStatuses,refresh:rerender,enforceProtectedActions};
    window.TakMapMissionAccessI575 = compatible;
    window.TakMapMissionAccessI574 = compatible;
    window.TakMapMissionAccessI573 = compatible;
    window.TakMapMissionUnlockI572 = {version:VERSION,status,open:openDialog,lock:m=>action(m,'clear'),ensureUnlocked:async m=>{const i=await status(m,true);return !i.protected||i.unlocked;}};
  }

  function boot(){ensureStyles();replaceLegacy();installEvents();try{ingest(currentPayload())}catch(_){}rerender();enforceProtectedActions();void primeStatuses(false);[350,1100,2800].forEach(ms=>setTimeout(()=>void primeStatuses(false),ms));}

  window.TakMapMissionAccessI576 = Object.freeze({
    version:VERSION,status,peek,ingest,primeStatuses,open:openDialog,openManual,unlock:(m,p)=>action(m,'unlock',p),clear:m=>action(m,'clear'),refresh:rerender,enforceProtectedActions,
    audit:()=>({version:VERSION,authoritativeMissionRowHtml:true,refreshStatePreserved:true,coreCacheIdentity:'i576',authenticatedResponseContext:true,statusPrimedForEveryMission:true,unknownStatusForcesDiscovery:true,unlockTriggersEnrichmentRefresh:true,postRenderDecorator:false,observer:false,missionRowFinalPatch:'i577-missionrow-stable',packageVersion:'i602',manualMissionEntryBeforeDiscovery:false,operatorNeverTypesMissionName:true,discoveredMissionNameRequired:true,missionControlFontPx:10,missionControlHeightPx:24,dialogTitle:'Mission Password',equalDialogButtons:true})
  });

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
