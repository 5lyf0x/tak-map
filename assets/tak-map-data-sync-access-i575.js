/* TAK Map i575 authoritative Mission-row access controls and sidebar visual polish. */
(() => {
  'use strict';
  if (window.TakMapMissionAccessI575) return;

  const VERSION = 'i575';
  const API = '/api/tak-map/data-sync-mission-access-i573';
  const state = {status:new Map(), pending:new Map(), activeMission:''};
  const text = value => String(value == null ? '' : value).trim();
  const key = mission => text(mission).toLowerCase();

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

  function normalize(mission, body) {
    body = Object.assign({}, body || {});
    const protectedMission = Boolean(body.protected != null ? body.protected : body.password_protected);
    return Object.assign(body, {
      ok:true,
      version:VERSION,
      mission:text(mission),
      protected:protectedMission,
      password_protected:protectedMission,
      unlocked:Boolean(!protectedMission || body.unlocked),
      locked:Boolean(protectedMission && !body.unlocked),
    });
  }

  function ingest(payload) {
    if (!payload || typeof payload !== 'object') return 0;
    const rows = payload.mission_access_i575 || payload.mission_access_i573 || payload.mission_access_i572 || [];
    let count = 0;
    if (Array.isArray(rows)) {
      for (const row of rows) {
        const mission = text(row && row.mission);
        if (!mission) continue;
        state.status.set(key(mission), normalize(mission, row));
        count += 1;
      }
    }
    return count;
  }

  function embeddedAccess(mission) {
    let payload = null;
    try { payload = typeof lastDataSync !== 'undefined' ? lastDataSync : window.lastDataSync; }
    catch (_) { payload = window.lastDataSync; }
    const rows = (payload && (payload.mission_access_i575 || payload.mission_access_i573 || payload.mission_access_i572)) || [];
    const found = Array.isArray(rows) ? rows.find(row => key(row && row.mission) === key(mission)) : null;
    if (!found) return null;
    const info = normalize(mission, found);
    state.status.set(key(mission), info);
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
      const info = normalize(mission, body);
      state.status.set(k, info);
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
    const info = normalize(mission, body);
    state.status.set(key(mission), info);
    return info;
  }

  function ensureStyles() {
    if (document.getElementById('takMapMissionAccessStyleI575')) return;
    const style = document.createElement('style');
    style.id = 'takMapMissionAccessStyleI575';
    style.textContent = `
      #dataSyncRows .tak-mission-card-i575{display:flex!important;align-items:center!important;gap:10px!important}
      #dataSyncRows .tak-mission-main-i575{min-width:0;flex:1;display:flex;flex-direction:column;gap:2px}
      #dataSyncRows .tak-mission-access-i575{margin-left:auto;flex:0 0 auto;display:flex;align-items:center;gap:6px}
      #dataSyncRows .tak-mission-control-i575{font-family:Rajdhani,"Arial Narrow",Arial,sans-serif!important;font-size:10px!important;line-height:1!important;font-weight:800!important;letter-spacing:0!important;white-space:nowrap!important;min-height:24px!important;height:24px!important}
      #dataSyncRows .tak-mission-state-i575{display:inline-flex;align-items:center;justify-content:center;min-width:60px;padding:0 8px;border:1px solid #596874;border-radius:999px;background:#17242e;color:#ccd4da}
      #dataSyncRows .tak-mission-state-i575.unlocked{border-color:rgba(117,181,143,.70);background:rgba(40,104,67,.22);color:#ccebd8}
      #dataSyncRows .tak-mission-state-i575.locked{border-color:rgba(205,164,99,.72);background:rgba(112,73,22,.24);color:#f0d59f}
      #dataSyncRows .tak-mission-edit-i575{min-width:45px!important;padding:0 8px!important;margin:0!important}

      #takMapMissionAccessDialogI575{position:fixed;inset:0;z-index:7800;display:flex;align-items:center;justify-content:center;padding:20px;background:rgba(0,0,0,.68)}
      #takMapMissionAccessDialogI575[hidden]{display:none!important}
      #takMapMissionAccessDialogI575 .mission-access-card-i575{position:relative;z-index:1;width:min(450px,calc(100vw - 32px));overflow:hidden;border:1px solid #74828d;border-radius:13px;background:linear-gradient(180deg,#192733,#0b151e);box-shadow:0 28px 90px rgba(0,0,0,.78);color:#edf1f4}
      #takMapMissionAccessDialogI575 .mission-access-head-i575{padding:15px 17px 12px;border-bottom:1px solid rgba(203,210,216,.22)}
      #takMapMissionAccessDialogI575 h2{margin:0 0 5px;font-size:17px}
      #takMapMissionAccessDialogI575 p{margin:0;color:#b8c2ca;font-size:11.5px;line-height:1.45}
      #takMapMissionAccessDialogI575 .mission-access-body-i575{padding:14px 17px 17px}
      #takMapMissionAccessDialogI575 label{display:block;margin-bottom:6px;color:#d7dde2;font-size:11px;font-weight:800}
      #takMapMissionAccessDialogI575 input{box-sizing:border-box;width:100%;height:39px;padding:0 11px;border:1px solid #687682;border-radius:8px;background:#08121a;color:#f2f5f7;font:inherit;outline:none}
      #takMapMissionAccessDialogI575 input:focus{border-color:#d4dbe0;box-shadow:0 0 0 2px rgba(203,210,216,.18)}
      #takMapMissionAccessDialogI575 .mission-access-current-i575{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px;padding:9px 10px;border:1px solid rgba(203,210,216,.18);border-radius:8px;background:rgba(4,10,15,.34);font-size:11px}
      #takMapMissionAccessDialogI575 .mission-access-status-i575{min-height:19px;margin-top:8px;color:#c8d0d6;font-size:10.5px;line-height:1.4}
      #takMapMissionAccessDialogI575 .mission-access-status-i575.error{color:#efb0aa}
      #takMapMissionAccessDialogI575 .mission-access-status-i575.ok{color:#bce2ca}
      #takMapMissionAccessDialogI575 .mission-access-actions-i575{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:13px}
      #takMapMissionAccessDialogI575 .mission-access-actions-i575 button{box-sizing:border-box;width:100%;min-width:0;min-height:36px;height:36px;margin:0;padding:0 10px;border:1px solid #687682;border-radius:8px;background:#17242e;color:#e9edf0;font-size:10px;font-weight:800;white-space:nowrap;cursor:pointer}
      #takMapMissionAccessDialogI575 .mission-access-actions-i575 button.primary{border-color:#e0e5e8;background:linear-gradient(180deg,#dde3e7,#aeb8bf);color:#111920}
      #takMapMissionAccessDialogI575 .mission-access-actions-i575 button.clear{border-color:rgba(205,125,116,.58);color:#f1c5c1;background:rgba(112,36,31,.2)}
      #takMapMissionAccessDialogI575 button:disabled{opacity:.55;cursor:wait}

      #sidebar,.sidebar,#dataSyncRows,#dataSyncRows .datasync-section-list{scrollbar-color:#7f8d97 #111a21!important;scrollbar-width:thin!important}
      #sidebar::-webkit-scrollbar,.sidebar::-webkit-scrollbar,#dataSyncRows::-webkit-scrollbar,#dataSyncRows .datasync-section-list::-webkit-scrollbar{width:10px;height:10px}
      #sidebar::-webkit-scrollbar-track,.sidebar::-webkit-scrollbar-track,#dataSyncRows::-webkit-scrollbar-track,#dataSyncRows .datasync-section-list::-webkit-scrollbar-track{background:#111a21!important}
      #sidebar::-webkit-scrollbar-thumb,.sidebar::-webkit-scrollbar-thumb,#dataSyncRows::-webkit-scrollbar-thumb,#dataSyncRows .datasync-section-list::-webkit-scrollbar-thumb{background:linear-gradient(180deg,#98a4ac,#64727c)!important;border:2px solid #111a21!important;border-radius:999px!important}
      #sidebar::-webkit-scrollbar-thumb:hover,.sidebar::-webkit-scrollbar-thumb:hover,#dataSyncRows::-webkit-scrollbar-thumb:hover,#dataSyncRows .datasync-section-list::-webkit-scrollbar-thumb:hover{background:linear-gradient(180deg,#b0bac1,#798790)!important}
      .sidebar .panel>h2:hover,.sidebar .panel>h2:focus-visible,.sidebar .tak-card-header-v491:hover,.sidebar .tak-card-header-v491:focus-visible{background:transparent!important;color:#c8d2da!important;box-shadow:none!important}
      #adsbMenuHostV316 .adsb-stepper-buttons{background:rgba(123,137,147,.10)!important;border-left-color:rgba(123,137,147,.48)!important}
      #adsbMenuHostV316 .adsb-stepper-buttons button{color:#c8d0d6!important;background:linear-gradient(180deg,rgba(118,132,142,.34),rgba(64,76,85,.28))!important;border-color:rgba(133,147,157,.58)!important;text-shadow:none!important}
      #adsbMenuHostV316 .adsb-stepper-buttons button:hover,#adsbMenuHostV316 .adsb-stepper-buttons button:focus{color:#fff!important;background:linear-gradient(180deg,rgba(145,158,167,.46),rgba(78,90,99,.40))!important;border-color:rgba(175,185,192,.75)!important}
      #takMapPointEditorI556 [data-i575-access-locked="1"],#pointEditPanel [data-i575-access-locked="1"]{opacity:.58;cursor:not-allowed!important}
    `;
    document.head.appendChild(style);
  }

  function dialog() {
    ensureStyles();
    let root = document.getElementById('takMapMissionAccessDialogI575');
    if (root) return root;
    root = document.createElement('div');
    root.id = 'takMapMissionAccessDialogI575';
    root.hidden = true;
    root.innerHTML = `
      <form class="mission-access-card-i575" autocomplete="off">
        <div class="mission-access-head-i575"><h2>Mission Password</h2><p class="mission-access-copy-i575"></p></div>
        <div class="mission-access-body-i575">
          <div class="mission-access-current-i575"><span>Status</span><b class="mission-access-state-i575">Locked</b></div>
          <label for="takMapMissionPasswordI575">Enter or replace password</label>
          <input id="takMapMissionPasswordI575" type="password" autocomplete="new-password" maxlength="512" spellcheck="false">
          <div class="mission-access-status-i575" aria-live="polite"></div>
          <div class="mission-access-actions-i575">
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
    const root = document.getElementById('takMapMissionAccessDialogI575');
    if (!root) return;
    const input = root.querySelector('input');
    if (input) input.value = '';
    root.hidden = true;
    state.activeMission = '';
  }

  function rerender() {
    try {
      let payload = null;
      try { payload = typeof lastDataSync !== 'undefined' ? lastDataSync : window.lastDataSync; } catch (_) { payload = window.lastDataSync; }
      ingest(payload);
      if (typeof window.renderDataSyncRows === 'function') window.renderDataSyncRows(); else if (typeof renderDataSyncRows === 'function') renderDataSyncRows();
    } catch (_) {}
    setTimeout(enforceProtectedActions, 10);
  }

  async function openDialog(mission) {
    mission = text(mission);
    if (!mission) return false;
    const root = dialog();
    const form = root.querySelector('form');
    const input = root.querySelector('input');
    const copy = root.querySelector('.mission-access-copy-i575');
    const current = root.querySelector('.mission-access-state-i575');
    const message = root.querySelector('.mission-access-status-i575');
    const submit = root.querySelector('button[type="submit"]');
    const cancel = root.querySelector('[data-cancel]');
    const clear = root.querySelector('[data-clear]');
    state.activeMission = mission;
    root.hidden = false;
    copy.textContent = `${mission} is password protected in OpenTAKServer. The accepted password is stored encrypted for only your signed-in TAK Map account.`;
    message.textContent = 'Checking Mission access…';
    message.className = 'mission-access-status-i575';
    input.value = '';
    let info;
    try { info = await status(mission, true); }
    catch (error) { info = normalize(mission,{protected:true,unlocked:false}); message.textContent = error.message || String(error); message.classList.add('error'); }
    current.textContent = info.unlocked ? 'Unlocked' : 'Locked';
    clear.disabled = !info.password_stored_server_side && !info.credential_configured && !info.unlocked;
    if (!message.classList.contains('error')) message.textContent = info.unlocked ? 'A password is stored and currently accepted by OpenTAKServer.' : 'Enter the Mission password to unlock protected read and write operations.';
    setTimeout(() => input.focus(), 0);

    cancel.onclick = closeDialog;
    clear.onclick = async () => {
      clear.disabled = cancel.disabled = submit.disabled = true;
      message.textContent = 'Clearing the stored password…'; message.className = 'mission-access-status-i575';
      try {
        info = await action(mission,'clear');
        current.textContent = 'Locked'; input.value = '';
        message.textContent = 'Stored Mission password cleared. Protected publication is now disabled.'; message.classList.add('ok');
        rerender();
      } catch (error) { message.textContent = error.message || String(error); message.classList.add('error'); }
      finally { clear.disabled = true; cancel.disabled = submit.disabled = false; }
    };
    form.onsubmit = async event => {
      event.preventDefault();
      const password = input.value;
      if (!password) { message.textContent = 'Enter the Mission password.'; message.className = 'mission-access-status-i575 error'; return; }
      clear.disabled = cancel.disabled = submit.disabled = true;
      message.textContent = 'Validating with OpenTAKServer…'; message.className = 'mission-access-status-i575';
      try {
        info = await action(mission,'unlock',password);
        input.value = ''; current.textContent = 'Unlocked';
        message.textContent = 'Password accepted and stored securely for this Mission.'; message.classList.add('ok');
        clear.disabled = false; rerender(); setTimeout(closeDialog,550);
      } catch (error) {
        input.value = ''; message.textContent = error.message || String(error); message.classList.add('error'); input.focus();
      } finally {
        cancel.disabled = submit.disabled = false;
        if (!info || !info.unlocked) clear.disabled = true;
      }
    };
    return true;
  }

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
    if(!save||!mission){if(save&&save.dataset.i575AccessLocked==='1'){delete save.dataset.i575AccessLocked;save.removeAttribute('data-i575-access-locked');save.disabled=false;}return true;}
    let info; try{info=await status(mission,force);}catch(_){return true;}
    if(info.protected&&!info.unlocked){save.dataset.i575AccessLocked='1';save.setAttribute('data-i575-access-locked','1');save.disabled=true;setInlineStatus('pointSaveStatusI556',`Mission is locked. Use Edit beside ${mission} in the Data Sync Missions row to enter its password.`);return false;}
    if(save.dataset.i575AccessLocked==='1'){delete save.dataset.i575AccessLocked;save.removeAttribute('data-i575-access-locked');save.disabled=false;} return true;
  }
  async function enforceEditorAccess(force=false) {
    const mission=editorMission(), save=document.getElementById('pointEditorSaveI556');
    if(!save||!mission)return true;
    let info; try{info=await status(mission,force);}catch(_){return true;}
    if(info.protected&&!info.unlocked){save.dataset.i575AccessLocked='1';save.setAttribute('data-i575-access-locked','1');save.disabled=true;setInlineStatus('pointEditorStatusI556',`Mission is locked. Use Edit beside ${mission} in the Data Sync Missions row to enter its password.`);return false;}
    if(save.dataset.i575AccessLocked==='1'){delete save.dataset.i575AccessLocked;save.removeAttribute('data-i575-access-locked');try{if(typeof window.markEditorDirty==='function')window.markEditorDirty();}catch(_){}} return true;
  }
  function enforceProtectedActions(){void enforceCreateAccess(false);void enforceEditorAccess(false);}

  function installEvents() {
    document.addEventListener('click', event => {
      const edit = event.target?.closest?.('[data-mission-edit-i575]');
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
    window.TakMapMissionAccessI573 = {version:VERSION,status,open:openDialog,unlock:(m,p)=>action(m,'unlock',p),clear:m=>action(m,'clear'),peek,ingest,refresh:rerender,enforceProtectedActions};
    window.TakMapMissionUnlockI572 = {version:VERSION,status,open:openDialog,lock:m=>action(m,'clear'),ensureUnlocked:async m=>{const i=await status(m,true);return !i.protected||i.unlocked;}};
  }

  function boot(){ensureStyles();replaceLegacy();installEvents();try{let payload=null;try{payload=typeof lastDataSync!=='undefined'?lastDataSync:window.lastDataSync}catch(_){payload=window.lastDataSync}ingest(payload)}catch(_){}rerender();enforceProtectedActions();}

  window.TakMapMissionAccessI575 = Object.freeze({
    version:VERSION,status,peek,ingest,open:openDialog,unlock:(m,p)=>action(m,'unlock',p),clear:m=>action(m,'clear'),refresh:rerender,enforceProtectedActions,
    audit:()=>({version:VERSION,authoritativeMissionRowHtml:true,refreshStatePreserved:true,coreCacheIdentity:'i575',authenticatedResponseContext:true,postRenderDecorator:false,observer:false,missionControlFontPx:10,missionControlHeightPx:24,dialogTitle:'Mission Password',equalDialogButtons:true})
  });

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
