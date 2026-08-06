/* TAK Map i573 explicit per-Mission password management and locked-save guard. */
(() => {
  'use strict';
  if (window.TakMapMissionAccessI573) return;

  const VERSION = 'i573';
  const API = '/api/tak-map/data-sync-mission-access-i573';
  const state = {
    status: new Map(),
    pending: new Map(),
    renderBase: null,
    renderWrapper: null,
    observer: null,
    activeMission: '',
  };
  const text = value => String(value == null ? '' : value).trim();
  const key = mission => text(mission).toLowerCase();

  async function readJson(response) {
    const raw = await response.text();
    let body = {};
    try { body = raw ? JSON.parse(raw) : {}; }
    catch (_) { body = {error: raw || `HTTP ${response.status}`}; }
    if (!response.ok || body.ok === false) {
      const error = new Error(body.error || `HTTP ${response.status}`);
      error.status = response.status;
      error.payload = body;
      throw error;
    }
    return body;
  }

  function missionName(row) {
    try {
      if (typeof window.missionNameFromAny === 'function') return text(window.missionNameFromAny(row));
    } catch (_) {}
    return text(typeof row === 'string' ? row : row && (row.name || row.mission_name || row.missionName || row.uid));
  }

  function embeddedAccess(mission) {
    let payload = null;
    try { payload = typeof lastDataSync !== 'undefined' ? lastDataSync : window.lastDataSync; } catch (_) { payload = window.lastDataSync; }
    const rows = (payload && (payload.mission_access_i573 || payload.mission_access_i572)) || [];
    const target = key(mission);
    const found = Array.isArray(rows) ? rows.find(row => key(row && row.mission) === target) : null;
    if (!found) return null;
    const normalized = Object.assign({}, found, {
      ok: true,
      version: VERSION,
      mission: mission,
      protected: Boolean(found.protected != null ? found.protected : found.password_protected),
      unlocked: Boolean(found.unlocked),
      locked: Boolean((found.protected != null ? found.protected : found.password_protected) && !found.unlocked),
    });
    state.status.set(target, normalized);
    return normalized;
  }

  async function status(mission, force = false) {
    mission = text(mission);
    if (!mission) return {ok:true, version:VERSION, mission:'', protected:false, unlocked:true, locked:false};
    const k = key(mission);
    if (!force && state.status.has(k)) return state.status.get(k);
    if (!force) {
      const embedded = embeddedAccess(mission);
      if (embedded) return embedded;
    }
    if (state.pending.has(k)) return state.pending.get(k);
    const task = readJson(await fetch(`${API}?mission=${encodeURIComponent(mission)}`, {
      cache:'no-store', credentials:'same-origin'
    })).then(body => {
      const normalized = Object.assign({}, body, {
        version: VERSION,
        mission,
        protected: Boolean(body.protected),
        unlocked: Boolean(!body.protected || body.unlocked),
        locked: Boolean(body.protected && !body.unlocked),
      });
      state.status.set(k, normalized);
      return normalized;
    }).finally(() => state.pending.delete(k));
    state.pending.set(k, task);
    return task;
  }

  async function action(mission, actionName, password = '') {
    const body = await readJson(await fetch(API, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      credentials:'same-origin',
      cache:'no-store',
      body:JSON.stringify({action:actionName, mission, password})
    }));
    const normalized = Object.assign({}, body, {
      version:VERSION,
      mission,
      protected:Boolean(body.protected),
      unlocked:Boolean(!body.protected || body.unlocked),
      locked:Boolean(body.protected && !body.unlocked),
    });
    state.status.set(key(mission), normalized);
    return normalized;
  }

  function ensureStyles() {
    if (document.getElementById('takMapMissionAccessStyleI573')) return;
    const style = document.createElement('style');
    style.id = 'takMapMissionAccessStyleI573';
    style.textContent = `
      #dataSyncRows .tak-mission-card-i573{display:flex!important;align-items:center!important;gap:10px!important}
      #dataSyncRows .tak-mission-main-i573{min-width:0;flex:1;display:flex;flex-direction:column;gap:2px}
      #dataSyncRows .tak-mission-access-i573{margin-left:auto;flex:0 0 auto;display:flex;align-items:center;gap:7px}
      #dataSyncRows .tak-mission-state-i573{display:inline-flex;align-items:center;min-height:24px;padding:0 8px;border:1px solid #596874;border-radius:999px;background:#17242e;color:#ccd4da;font-size:9.5px;font-weight:850;letter-spacing:.025em;white-space:nowrap}
      #dataSyncRows .tak-mission-state-i573.unlocked{border-color:rgba(117,181,143,.7);background:rgba(40,104,67,.22);color:#ccebd8}
      #dataSyncRows .tak-mission-state-i573.locked{border-color:rgba(205,164,99,.72);background:rgba(112,73,22,.24);color:#f0d59f}
      #dataSyncRows .tak-mission-edit-i573{min-width:54px!important;padding:5px 9px!important}
      #takMapMissionAccessDialogI573{position:fixed;inset:0;z-index:7800;display:flex;align-items:center;justify-content:center;padding:20px;background:rgba(0,0,0,.68)}
      #takMapMissionAccessDialogI573[hidden]{display:none!important}
      #takMapMissionAccessDialogI573 .mission-access-card-i573{position:relative;z-index:1;width:min(440px,calc(100vw - 32px));overflow:hidden;border:1px solid #74828d;border-radius:13px;background:linear-gradient(180deg,#192733,#0b151e);box-shadow:0 28px 90px rgba(0,0,0,.78);color:#edf1f4}
      #takMapMissionAccessDialogI573 .mission-access-head-i573{padding:15px 17px 12px;border-bottom:1px solid rgba(203,210,216,.22)}
      #takMapMissionAccessDialogI573 h2{margin:0 0 5px;font-size:17px}
      #takMapMissionAccessDialogI573 p{margin:0;color:#b8c2ca;font-size:11.5px;line-height:1.45}
      #takMapMissionAccessDialogI573 .mission-access-body-i573{padding:14px 17px 17px}
      #takMapMissionAccessDialogI573 label{display:block;margin-bottom:6px;color:#d7dde2;font-size:11px;font-weight:800}
      #takMapMissionAccessDialogI573 input{box-sizing:border-box;width:100%;height:39px;padding:0 11px;border:1px solid #687682;border-radius:8px;background:#08121a;color:#f2f5f7;font:inherit;outline:none}
      #takMapMissionAccessDialogI573 input:focus{border-color:#d4dbe0;box-shadow:0 0 0 2px rgba(203,210,216,.18)}
      #takMapMissionAccessDialogI573 .mission-access-current-i573{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px;padding:9px 10px;border:1px solid rgba(203,210,216,.18);border-radius:8px;background:rgba(4,10,15,.34);font-size:11px}
      #takMapMissionAccessDialogI573 .mission-access-current-i573 b{color:#f0f3f5}
      #takMapMissionAccessDialogI573 .mission-access-status-i573{min-height:19px;margin-top:8px;color:#c8d0d6;font-size:10.5px;line-height:1.4}
      #takMapMissionAccessDialogI573 .mission-access-status-i573.error{color:#efb0aa}
      #takMapMissionAccessDialogI573 .mission-access-status-i573.ok{color:#bce2ca}
      #takMapMissionAccessDialogI573 .mission-access-actions-i573{display:flex;align-items:center;justify-content:flex-end;gap:8px;margin-top:13px}
      #takMapMissionAccessDialogI573 button{min-width:88px;min-height:34px;border:1px solid #687682;border-radius:8px;background:#17242e;color:#e9edf0;font-weight:800;cursor:pointer}
      #takMapMissionAccessDialogI573 button.primary{border-color:#e0e5e8;background:linear-gradient(180deg,#dde3e7,#aeb8bf);color:#111920}
      #takMapMissionAccessDialogI573 button.clear{margin-right:auto;border-color:rgba(205,125,116,.58);color:#f1c5c1;background:rgba(112,36,31,.2)}
      #takMapMissionAccessDialogI573 button:disabled{opacity:.55;cursor:wait}
      #takMapPointEditorI556 [data-i573-access-locked="1"],#pointEditPanel [data-i573-access-locked="1"]{opacity:.58;cursor:not-allowed!important}
    `;
    document.head.appendChild(style);
  }

  function dialog() {
    ensureStyles();
    let root = document.getElementById('takMapMissionAccessDialogI573');
    if (root) return root;
    root = document.createElement('div');
    root.id = 'takMapMissionAccessDialogI573';
    root.hidden = true;
    root.innerHTML = `
      <form class="mission-access-card-i573" autocomplete="off">
        <div class="mission-access-head-i573"><h2>Mission password</h2><p class="mission-access-copy-i573"></p></div>
        <div class="mission-access-body-i573">
          <div class="mission-access-current-i573"><span>Status</span><b class="mission-access-state-i573">Locked</b></div>
          <label for="takMapMissionPasswordI573">Enter or replace password</label>
          <input id="takMapMissionPasswordI573" type="password" autocomplete="new-password" maxlength="512" spellcheck="false">
          <div class="mission-access-status-i573" aria-live="polite"></div>
          <div class="mission-access-actions-i573">
            <button type="button" class="clear" data-clear>Clear Stored Password</button>
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
    const root = document.getElementById('takMapMissionAccessDialogI573');
    if (!root) return;
    const input = root.querySelector('input');
    if (input) input.value = '';
    root.hidden = true;
    state.activeMission = '';
  }

  async function openDialog(mission) {
    mission = text(mission);
    if (!mission) return false;
    const root = dialog();
    const form = root.querySelector('form');
    const input = root.querySelector('input');
    const copy = root.querySelector('.mission-access-copy-i573');
    const current = root.querySelector('.mission-access-state-i573');
    const message = root.querySelector('.mission-access-status-i573');
    const clear = root.querySelector('[data-clear]');
    const cancel = root.querySelector('[data-cancel]');
    const submit = root.querySelector('button[type="submit"]');
    state.activeMission = mission;
    root.hidden = false;
    copy.textContent = `${mission} is password protected in OpenTAKServer. The accepted password is stored encrypted for only your signed-in TAK Map account.`;
    message.textContent = 'Checking Mission access…';
    message.className = 'mission-access-status-i573';
    input.value = '';
    let info;
    try { info = await status(mission, true); }
    catch (error) { info = {protected:true, unlocked:false, locked:true}; message.textContent = error.message || String(error); message.classList.add('error'); }
    current.textContent = info.unlocked ? 'Unlocked' : 'Locked';
    clear.disabled = !info.password_stored_server_side && !info.unlocked;
    if (!message.classList.contains('error')) message.textContent = info.unlocked ? 'A password is stored and currently accepted by OpenTAKServer.' : 'Enter the Mission password to unlock protected read and write operations.';
    setTimeout(() => input.focus(), 0);

    cancel.onclick = closeDialog;
    clear.onclick = async () => {
      clear.disabled = cancel.disabled = submit.disabled = true;
      message.textContent = 'Clearing the stored password…';
      message.className = 'mission-access-status-i573';
      try {
        info = await action(mission, 'clear');
        current.textContent = 'Locked';
        message.textContent = 'Stored Mission password cleared. Protected publication is now disabled.';
        message.classList.add('ok');
        input.value = '';
        refreshUi();
      } catch (error) {
        message.textContent = error.message || String(error);
        message.classList.add('error');
      } finally {
        clear.disabled = true; cancel.disabled = submit.disabled = false;
      }
    };
    form.onsubmit = async event => {
      event.preventDefault();
      const password = input.value;
      if (!password) { message.textContent = 'Enter the Mission password.'; message.className = 'mission-access-status-i573 error'; return; }
      clear.disabled = cancel.disabled = submit.disabled = true;
      message.textContent = 'Validating with OpenTAKServer…';
      message.className = 'mission-access-status-i573';
      try {
        info = await action(mission, 'unlock', password);
        input.value = '';
        current.textContent = 'Unlocked';
        message.textContent = 'Password accepted and stored securely for this Mission.';
        message.classList.add('ok');
        clear.disabled = false;
        refreshUi();
        setTimeout(closeDialog, 550);
      } catch (error) {
        input.value = '';
        message.textContent = error.message || String(error);
        message.classList.add('error');
        input.focus();
      } finally {
        cancel.disabled = submit.disabled = false;
        if (!info || !info.unlocked) clear.disabled = true;
      }
    };
    return true;
  }

  function accessForMission(mission) {
    return state.status.get(key(mission)) || embeddedAccess(mission);
  }

  function missionRows() {
    try {
      const payload = typeof lastDataSync !== 'undefined' ? lastDataSync : window.lastDataSync;
      return payload && Array.isArray(payload.missions) ? payload.missions : [];
    } catch (_) { return []; }
  }

  function missionsSection() {
    const box = document.getElementById('dataSyncRows');
    if (!box) return null;
    return Array.from(box.querySelectorAll('.datasync-section')).find(section => {
      const label = section.querySelector('.section-label');
      return text(label && label.textContent).toLowerCase() === 'missions';
    }) || null;
  }

  function decorateMissionRows() {
    ensureStyles();
    const section = missionsSection();
    if (!section) return;
    const cards = Array.from(section.querySelectorAll('.datasync-section-list > .sync-card'));
    const rows = missionRows();
    cards.forEach((card, index) => {
      const row = rows[index];
      const mission = missionName(row) || text(card.querySelector('b') && card.querySelector('b').textContent);
      if (!mission) return;
      card.classList.add('tak-mission-card-i573');
      card.dataset.i573Mission = mission;
      let main = card.querySelector('.tak-mission-main-i573');
      if (!main) {
        main = document.createElement('div'); main.className = 'tak-mission-main-i573';
        while (card.firstChild) main.appendChild(card.firstChild);
        card.appendChild(main);
      }
      let controls = card.querySelector('.tak-mission-access-i573');
      if (!controls) { controls = document.createElement('div'); controls.className = 'tak-mission-access-i573'; card.appendChild(controls); }
      const embedded = accessForMission(mission);
      const protectedMission = Boolean((row && (row.passwordProtected === true || row.password_protected === true)) || (embedded && embedded.protected));
      if (!protectedMission) { controls.replaceChildren(); controls.hidden = true; return; }
      controls.hidden = false;
      const unlocked = Boolean(embedded && embedded.unlocked);
      const signature = `${mission}|${unlocked ? 'unlocked' : 'locked'}`;
      if (controls.dataset.i573Signature !== signature) {
        controls.dataset.i573Signature = signature;
        controls.innerHTML = `<span class="tak-mission-state-i573 ${unlocked ? 'unlocked' : 'locked'}">${unlocked ? 'Unlocked' : 'Locked'}</span><button type="button" class="layer-button tak-mission-edit-i573">Edit</button>`;
        controls.querySelector('button').addEventListener('click', event => { event.preventDefault(); event.stopPropagation(); void openDialog(mission); });
      }
      if (!embedded) void status(mission, true).then(() => { decorateMissionRows(); enforceProtectedActions(); }).catch(() => {});
    });
  }

  function installRenderWrapper() {
    const current = window.renderDataSyncRows;
    if (typeof current !== 'function') return false;
    if (current.__takMapI573MissionAccess) return true;
    const wrapper = function () {
      const result = current.apply(this, arguments);
      setTimeout(decorateMissionRows, 0);
      setTimeout(enforceProtectedActions, 0);
      return result;
    };
    wrapper.__takMapI573MissionAccess = true;
    wrapper.__takMapI573Base = current;
    state.renderBase = current;
    state.renderWrapper = wrapper;
    window.renderDataSyncRows = wrapper;
    try { renderDataSyncRows = wrapper; } catch (_) {}
    return true;
  }

  function setInlineStatus(nodeId, message, error = true) {
    const node = document.getElementById(nodeId);
    if (!node) return;
    if (node.textContent !== message) node.textContent = message;
    node.classList.toggle('error', error);
    if (error) node.classList.remove('ok');
  }

  function selectedCreateMission() {
    const destination = document.getElementById('pointSaveDestinationI556');
    if (!destination || destination.value !== 'mission') return '';
    const select = document.getElementById('pointMissionI556');
    return text(select && select.value);
  }

  function editorMission() {
    const modal = document.getElementById('takMapPointEditorI556');
    if (!modal || !modal.classList.contains('active')) return '';
    const label = document.getElementById('pointEditorContextLabelI556');
    if (text(label && label.textContent).toLowerCase() !== 'mission') return '';
    const input = document.getElementById('pointEditorContextI556');
    return text(input && input.value);
  }

  async function enforceCreateAccess(force = false) {
    const mission = selectedCreateMission();
    const save = document.getElementById('pointSaveI556');
    if (!save || !mission) { if (save && save.dataset.i573AccessLocked === '1') { delete save.dataset.i573AccessLocked; save.disabled = false; } return true; }
    let info;
    try { info = await status(mission, force); } catch (_) { return true; }
    const locked = Boolean(info.protected && !info.unlocked);
    if (locked) {
      save.dataset.i573AccessLocked = '1'; save.setAttribute('data-i573-access-locked','1'); save.disabled = true;
      setInlineStatus('pointSaveStatusI556', `Mission is locked. Use Edit beside ${mission} in the Data Sync Missions row to enter its password.`);
      return false;
    }
    if (save.dataset.i573AccessLocked === '1') { delete save.dataset.i573AccessLocked; save.removeAttribute('data-i573-access-locked'); save.disabled = false; }
    return true;
  }

  async function enforceEditorAccess(force = false) {
    const mission = editorMission();
    const save = document.getElementById('pointEditorSaveI556');
    if (!save || !mission) return true;
    let info;
    try { info = await status(mission, force); } catch (_) { return true; }
    const locked = Boolean(info.protected && !info.unlocked);
    if (locked) {
      save.dataset.i573AccessLocked = '1'; save.setAttribute('data-i573-access-locked','1'); save.disabled = true;
      setInlineStatus('pointEditorStatusI556', `Mission is locked. Use Edit beside ${mission} in the Data Sync Missions row to enter its password.`);
      return false;
    }
    if (save.dataset.i573AccessLocked === '1') {
      delete save.dataset.i573AccessLocked; save.removeAttribute('data-i573-access-locked');
      try { if (typeof window.markEditorDirty === 'function') window.markEditorDirty(); else if (typeof markEditorDirty === 'function') markEditorDirty(); } catch (_) {}
    }
    return true;
  }

  function enforceProtectedActions() {
    void enforceCreateAccess(false);
    void enforceEditorAccess(false);
  }

  function refreshUi() {
    try {
      if (typeof window.renderDataSyncRows === 'function') window.renderDataSyncRows();
      else decorateMissionRows();
    } catch (_) { decorateMissionRows(); }
    setTimeout(enforceProtectedActions, 20);
  }

  function installGuards() {
    document.addEventListener('click', event => {
      const target = event.target && event.target.closest ? event.target.closest('#pointSaveI556,#pointEditorSaveI556') : null;
      if (!target) return;
      const mission = target.id === 'pointSaveI556' ? selectedCreateMission() : editorMission();
      if (!mission) return;
      const info = accessForMission(mission);
      if (info && info.protected && !info.unlocked) {
        event.preventDefault(); event.stopImmediatePropagation();
        if (target.id === 'pointSaveI556') setInlineStatus('pointSaveStatusI556', `Mission is locked. Use Edit beside ${mission} in the Data Sync Missions row to enter its password.`);
        else setInlineStatus('pointEditorStatusI556', `Mission is locked. Use Edit beside ${mission} in the Data Sync Missions row to enter its password.`);
      }
    }, true);
    document.addEventListener('change', event => {
      if (event.target && (event.target.id === 'pointSaveDestinationI556' || event.target.id === 'pointMissionI556')) setTimeout(() => void enforceCreateAccess(true), 0);
    }, true);
    document.addEventListener('input', event => {
      if (event.target && event.target.closest && event.target.closest('#takMapPointEditorI556')) setTimeout(() => void enforceEditorAccess(false), 0);
    }, false);
    document.addEventListener('click', event => {
      if (event.target && event.target.closest && event.target.closest('[data-i556-point-edit],.point-popup-edit-i556')) {
        setTimeout(() => void enforceEditorAccess(true), 120);
        setTimeout(() => void enforceEditorAccess(true), 500);
      }
    }, false);
  }

  function installObserver() {
    if (state.observer || !document.body) return;
    state.observer = new MutationObserver(mutations => {
      let missionRowsChanged = false, editorChanged = false;
      for (const mutation of mutations) {
        const target = mutation.target;
        if (target && target.id === 'dataSyncRows') missionRowsChanged = true;
        if (target && target.closest && target.closest('#dataSyncRows')) missionRowsChanged = true;
        if (target && target.closest && target.closest('#takMapPointEditorI556,#pointEditPanel')) editorChanged = true;
      }
      if (missionRowsChanged) setTimeout(decorateMissionRows, 0);
      if (editorChanged) setTimeout(enforceProtectedActions, 0);
    });
    state.observer.observe(document.body, {subtree:true, childList:true, attributes:true, attributeFilter:['class','disabled','value']});
  }

  function replaceLegacyUnlock() {
    window.TakMapMissionUnlockI572 = {
      version: VERSION,
      status,
      open: openDialog,
      lock: mission => action(mission, 'clear'),
      ensureUnlocked: async mission => {
        const info = await status(mission, true);
        return Boolean(!info.protected || info.unlocked);
      }
    };
  }

  function boot() {
    ensureStyles();
    replaceLegacyUnlock();
    installGuards();
    installObserver();
    installRenderWrapper();
    decorateMissionRows();
    enforceProtectedActions();
    [250,800,1800,4000].forEach(ms => setTimeout(() => { installRenderWrapper(); decorateMissionRows(); enforceProtectedActions(); }, ms));
  }

  window.TakMapMissionAccessI573 = Object.freeze({
    version:VERSION,
    status,
    open:openDialog,
    unlock:(mission,password)=>action(mission,'unlock',password),
    clear:mission=>action(mission,'clear'),
    refresh:refreshUi,
    enforceProtectedActions,
    audit:() => ({version:VERSION,statusCount:state.status.size,legacyAutomaticPromptDisabled:true,explicitMissionRowEdit:true})
  });

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true});
  else boot();
})();
