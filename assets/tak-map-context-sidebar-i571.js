/* TAK Map i571 authoritative point/route/shape contextual sidebar and unified silver sidebar theme. */
(function (window, document) {
  'use strict';

  const VERSION = 'i571';
  const PANEL_ID = 'takMapContextSidebarI571';
  const BODY_ID = 'takMapContextSidebarBodyI571';
  const state = {
    installed: false,
    panel: null,
    body: null,
    selected: null,
    mode: 'info',
    suppressMapClickUntil: 0,
    hiding: false,
    wrapped: {},
    layerObjects: new WeakMap(),
    keyLayers: new Map(),
    errors: [],
    resizeObserver: null,
    mutationObserver: null,
    deletionObserver: null,
    deleteBusy: false,
    nativeDialogCalls: 0,
  };

  const text = value => String(value == null ? '' : value).trim();
  const esc = value => text(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const finite = value => Number.isFinite(Number(value));

  function mapInstance() {
    const candidates = [];
    try { candidates.push(window.takLeafletMap); } catch (_) {}
    try { if (typeof map !== 'undefined') candidates.push(map); } catch (_) {}
    try { candidates.push(window.map); } catch (_) {}
    for (const candidate of candidates) {
      if (candidate && typeof candidate.on === 'function' && typeof candidate.getContainer === 'function' && typeof candidate.getBounds === 'function') return candidate;
    }
    return null;
  }

  function mapNode() {
    const m = mapInstance();
    try { if (m && typeof m.getContainer === 'function') return m.getContainer(); } catch (_) {}
    return document.getElementById('map') || document.querySelector('.leaflet-container');
  }

  function addStyle() {
    if (document.getElementById('takMapContextSidebarStyleI571')) return;
    const style = document.createElement('style');
    style.id = 'takMapContextSidebarStyleI571';
    style.textContent = `
      :root{--tak-sidebar-silver-i571:#cbd2d8;--tak-sidebar-silver2-i571:#aeb8c0;--tak-sidebar-line-i571:#52606b;--tak-sidebar-glow-i571:rgba(203,210,216,.18)}

      /* Unified silver-accent theme for both sidebars. */
      #sidebar{--sidebar-accent:#cbd2d8!important;--accent:#cbd2d8!important}
      #sidebar .panel{border-color:rgba(191,201,209,.22)!important}
      #sidebar .panel h2,#sidebar .subgroup-title,#sidebar .datasync-section-title,#sidebar .local-section-title{color:#dfe4e8!important;border-color:rgba(203,210,216,.24)!important}
      #sidebar .panel h2:hover,#sidebar .subgroup-title:hover,#sidebar .datasync-section-title:hover,#sidebar .local-section-title:hover{background:rgba(203,210,216,.08)!important}
      #sidebar .panel-toggle,#sidebar .toggle,#sidebar .subgroup-label>.toggle,#sidebar .datasync-section-title>.toggle{color:var(--tak-sidebar-silver-i571)!important}
      #sidebar .chip,#sidebar .search-result-chip,#sidebar [class*="count"],#sidebar [class*="chip"]{border-color:rgba(203,210,216,.42)!important;background:rgba(203,210,216,.12)!important;color:#e7ebee!important}
      #sidebar input[type="checkbox"],#sidebar input[type="radio"],#sidebar input[type="range"]{accent-color:var(--tak-sidebar-silver-i571)!important}
      #sidebar input[type="range"]::-webkit-slider-thumb{background:var(--tak-sidebar-silver-i571)!important;border-color:#eef1f3!important}
      #sidebar input[type="range"]::-moz-range-thumb{background:var(--tak-sidebar-silver-i571)!important;border-color:#eef1f3!important}
      #sidebar input[type="range"]::-webkit-slider-runnable-track{background:linear-gradient(90deg,#8f9aa4,#3b4650)!important}
      #sidebar input[type="range"]::-moz-range-track{background:#56616b!important}
      #sidebar .layer-button:hover,#sidebar button:hover,#sidebar .row:hover,#sidebar .local-data-row:hover{border-color:#aeb8c0!important;background-color:rgba(203,210,216,.10)!important}
      #sidebar .selected-local,#sidebar .active,#sidebar [aria-pressed="true"]{border-color:#cbd2d8!important;box-shadow:inset 3px 0 0 #cbd2d8!important}
      #sidebarTab{border-color:#687681!important;background:linear-gradient(180deg,#26333e,#151f28)!important;color:#dfe4e8!important}
      #reliefOverlayButtonV506{border-color:#56636e!important;background:#18232d!important;color:#dce2e6!important}
      #reliefOverlayButtonV506[aria-pressed="true"]{border-color:#e2e6e9!important;background:linear-gradient(180deg,#dce2e6,#aeb8c0)!important;color:#111920!important;box-shadow:0 0 0 1px rgba(255,255,255,.18)!important}

      #${PANEL_ID}{box-sizing:border-box;position:absolute;right:14px;bottom:var(--tak-context-bottom-i571,54px);width:min(400px,calc(100% - 28px));height:auto;max-width:calc(100% - 28px);z-index:3600;color:#edf1f4;background:linear-gradient(180deg,rgba(17,29,40,.985),rgba(7,15,23,.992));border:1px solid #596671;border-radius:13px;box-shadow:0 22px 64px rgba(0,0,0,.62);transform:translateX(0);opacity:1;transition:transform .22s ease,opacity .18s ease;pointer-events:auto;overflow:visible;contain:layout style}
      #${PANEL_ID}.collapsed{transform:translateX(calc(100% + 26px));opacity:0;pointer-events:none}
      #${PANEL_ID} .tak-context-head-i571{min-height:45px;display:flex;align-items:center;gap:8px;padding:0 8px 0 12px;border-bottom:1px solid rgba(203,210,216,.23);background:linear-gradient(180deg,#1a2833,#111c25);border-radius:12px 12px 0 0}
      #${PANEL_ID} .tak-context-head-copy-i571{min-width:0;flex:1}
      #${PANEL_ID} .tak-context-kicker-i571{color:#9da8b1;font-size:9.5px;font-weight:850;letter-spacing:.1em;text-transform:uppercase}
      #${PANEL_ID} .tak-context-title-i571{overflow:hidden;color:#e7ebee;font-size:13.5px;font-weight:850;line-height:1.2;text-overflow:ellipsis;white-space:nowrap}
      #${PANEL_ID} .tak-context-hide-i571{width:32px;height:32px;display:grid;place-items:center;border:1px solid #60707c;border-radius:8px;background:#17232d;color:#e4e8eb;font-size:20px;line-height:1;cursor:pointer}
      #${PANEL_ID} .tak-context-hide-i571:hover{border-color:#d7dde1;background:#25323d}
      #${BODY_ID}{height:auto;max-height:none;padding:0;overflow:visible!important;overscroll-behavior:contain}
      #${BODY_ID}>*{max-width:100%!important}
      #${PANEL_ID} .feature-popup,#${PANEL_ID} .point-info-popup-i556{width:auto!important;min-width:0!important;max-width:none!important;margin:0!important;border:0!important;border-radius:0 0 12px 12px!important;background:transparent!important;box-shadow:none!important;overflow:visible!important;color:#e5eaed!important}
      #${PANEL_ID} .feature-popup h3{margin:0;padding:11px 12px 8px;border-bottom:1px solid rgba(203,210,216,.16);font-size:15px;overflow-wrap:anywhere}
      #${PANEL_ID} .feature-popup .kvp{display:grid;grid-template-columns:minmax(82px,.42fr) minmax(0,1fr);margin:0;padding:8px 10px 10px;gap:0;border:0;background:transparent}
      #${PANEL_ID} .feature-popup .kvp b,#${PANEL_ID} .feature-popup .kvp span{min-width:0;padding:6px 7px;border-bottom:1px solid rgba(203,210,216,.10);font-size:9px;line-height:1.28;overflow-wrap:anywhere;white-space:normal}
      #${PANEL_ID} .feature-popup .kvp b{color:#9faab3;text-transform:uppercase;letter-spacing:.045em}
      #${PANEL_ID} .feature-popup .kvp span{color:#edf1f4}
      #${PANEL_ID} .point-info-popup-i556{border-radius:0 0 12px 12px!important}
      #${PANEL_ID} .point-popup-head-i556{grid-template-columns:74px minmax(0,1fr)!important;gap:10px!important;padding:10px 11px!important;border-radius:0!important}
      #${PANEL_ID} .point-popup-stage-i556{width:70px!important;height:70px!important}
      #${PANEL_ID} .point-popup-stage-i556 img{width:68px!important;height:68px!important}
      #${PANEL_ID} .point-popup-title-i556{font-size:16px!important;line-height:1.28!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere!important}
      #${PANEL_ID} .point-popup-subtitle-i556,#${PANEL_ID} .point-popup-cot-i556,#${PANEL_ID} .point-popup-path-i556{font-size:11px!important;line-height:1.38!important}#${PANEL_ID} .point-popup-path-i556,#${PANEL_ID} .point-popup-value-i556{display:block!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;-webkit-line-clamp:unset!important;overflow-wrap:anywhere!important}
      #${PANEL_ID} .point-popup-body-i556{padding:7px 10px 10px!important}
      #${PANEL_ID} .point-popup-grid-i556{grid-template-columns:88px minmax(0,1fr)!important}
      #${PANEL_ID} .point-popup-label-i556,#${PANEL_ID} .point-popup-value-i556{padding:6px 7px!important;line-height:1.38!important}#${PANEL_ID} .point-popup-label-i556{font-size:9.5px!important}#${PANEL_ID} .point-popup-value-i556{font-size:11px!important}
      #${PANEL_ID} .point-popup-actions-i556{margin-top:8px!important}
      #${PANEL_ID} .point-popup-edit-i556{width:100%;min-height:36px!important;font-size:12.5px!important;font-weight:850!important;border-color:#9ea9b3!important;background:linear-gradient(180deg,#dce2e6,#adb7bf)!important;color:#111920!important}
      #${PANEL_ID} .point-popup-location-i571{display:flex!important;align-items:center!important;gap:8px!important}
      #${PANEL_ID} .point-popup-location-text-i571{min-width:0;flex:1;overflow-wrap:anywhere}
      #${PANEL_ID} .point-popup-copy-i571{flex:0 0 auto;min-height:28px;padding:0 9px;border:1px solid #71808b;border-radius:7px;color:#e6eaed;background:#17232d;font-size:9.5px;font-weight:850;cursor:pointer}
      #${PANEL_ID} .point-popup-copy-i571:hover{border-color:#cbd2d8;background:#23313c}
      #${PANEL_ID} .point-popup-copy-i571.copied{color:#111920;background:linear-gradient(180deg,#dce2e6,#aeb8c0)}
      #${PANEL_ID} .point-popup-time-i571{font-variant-numeric:tabular-nums}
      #${PANEL_ID} .point-popup-sync-i571{display:inline-flex;align-items:center;gap:6px;padding:4px 8px;border:1px solid rgba(203,210,216,.48);border-radius:999px;background:rgba(203,210,216,.11);font-size:10px;font-weight:850;white-space:nowrap}
      #${PANEL_ID} .point-popup-sync-dot-i571{width:7px;height:7px;flex:0 0 auto;border-radius:50%;background:#d7dde1;box-shadow:0 0 0 3px rgba(203,210,216,.10)}
      #${PANEL_ID} .point-popup-sync-i571.state-pending .point-popup-sync-dot-i571{background:#e5cf8b}
      #${PANEL_ID} .point-popup-sync-i571.state-stale .point-popup-sync-dot-i571{background:#c9a27d}
      #${PANEL_ID} .point-popup-sync-i571.state-conflict .point-popup-sync-dot-i571,#${PANEL_ID} .point-popup-sync-i571.state-remote-deleted .point-popup-sync-dot-i571{background:#d99595}

      /* Existing point editor is adopted into this sidebar; only its content changes in place. */
      #${BODY_ID}>#takMapPointEditorI556{position:static!important;inset:auto!important;width:100%!important;height:auto!important;display:none!important;padding:0!important;background:transparent!important;z-index:auto!important;overflow:visible!important}
      #${BODY_ID}>#takMapPointEditorI556.active{display:block!important}
      #${BODY_ID} #takMapPointEditorI556 .point-editor-card-i556{position:static!important;width:100%!important;max-width:none!important;max-height:none!important;margin:0!important;border:0!important;border-radius:0 0 12px 12px!important;box-shadow:none!important;overflow:visible!important;background:transparent!important;transform:none!important}
      #${BODY_ID} .point-head-i556{min-height:44px!important;padding:0 9px!important;gap:7px!important;border-radius:0!important}
      #${BODY_ID} .point-head-icon-i556{width:28px!important;height:28px!important}
      #${BODY_ID} .point-title-i556{font-size:15px!important}
      #${BODY_ID} .point-close-i556{width:30px!important;height:30px!important}
      #${BODY_ID} .point-body-i556{gap:7px!important;padding:8px 10px!important;overflow:visible!important}
      #${BODY_ID} .point-source-strip-i556{grid-template-columns:29px minmax(0,1fr) auto!important;gap:7px!important;align-items:start!important;padding:7px 8px!important}
      #${BODY_ID} .point-source-strip-i556>div{min-width:0!important}
      #${BODY_ID} .point-source-icon-i556{width:27px!important;height:27px!important}
      #${BODY_ID} .point-source-title-i556{font-size:11px!important}#${BODY_ID} .point-source-meta-i556{font-size:9.5px!important}#${BODY_ID} .point-source-title-i556,#${BODY_ID} .point-source-meta-i556{display:block!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere!important;line-height:1.22!important}
      #${BODY_ID} .point-source-state-i556{align-self:start!important;white-space:nowrap!important;font-size:10px!important}
      #${BODY_ID} .point-form-grid-i556{gap:7px!important}
      #${BODY_ID} .point-field-i556 label{margin-bottom:3px!important;font-size:9.5px!important}
      #${BODY_ID} .point-control-i556{height:34px!important;padding:0 8px!important;font-size:11px!important}
      #${BODY_ID} textarea.point-control-i556{height:48px!important;min-height:48px!important;padding:6px 8px!important;resize:none!important}
      #${BODY_ID} .point-symbol-card-i556{grid-template-columns:60px minmax(0,1fr)!important;gap:7px!important;padding:7px!important}
      #${BODY_ID} .point-symbol-stage-i556{width:56px!important;height:56px!important}
      #${BODY_ID} .point-symbol-stage-i556 img{width:54px!important;height:54px!important}
      #${BODY_ID} .point-symbol-button-i556{grid-column:1/-1;min-height:33px!important;font-size:10.5px!important}
      #${BODY_ID} .point-symbol-path-i556{display:block!important;font-size:10px!important;line-height:1.35!important;white-space:normal!important;overflow:visible!important;-webkit-line-clamp:unset!important;overflow-wrap:anywhere!important}
      #${BODY_ID} .point-status-i556{min-height:30px!important;padding:6px 7px!important;font-size:9.5px!important;line-height:1.35!important}
      #${BODY_ID} .point-actions-i556{min-height:47px!important;padding:7px 10px!important}
      #${BODY_ID} .point-button-i556{min-height:34px!important;padding:0 10px!important;font-size:10.5px!important}

      /* Route/shape legacy editor becomes an in-place sidebar view. */
      #${PANEL_ID} details.popup-edit{margin:8px 10px 10px;border:1px solid #56636f;border-radius:9px;background:#0d1821;overflow:visible}
      #${PANEL_ID} details.popup-edit>summary{min-height:34px;display:flex;align-items:center;justify-content:center;list-style:none;color:#111920;background:linear-gradient(180deg,#dce2e6,#adb7bf);border-radius:8px;font-size:10px;font-weight:850;cursor:pointer}
      #${PANEL_ID} details.popup-edit>summary::-webkit-details-marker{display:none}
      #${PANEL_ID} details.popup-edit[open]>summary{display:none}
      #${PANEL_ID} details.popup-edit label{display:block;padding:5px 8px 0;color:#aab4bc;font-size:8px;font-weight:800;text-transform:uppercase}
      #${PANEL_ID} details.popup-edit input,#${PANEL_ID} details.popup-edit textarea{box-sizing:border-box;width:100%;margin-top:3px;border:1px solid #485662;border-radius:6px;background:#08121a;color:#edf1f4;padding:6px 7px;font-size:10px;text-transform:none}
      #${PANEL_ID} details.popup-edit textarea{resize:none}
      #${PANEL_ID} .popup-edit-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;padding:0 8px}
      #${PANEL_ID} .popup-edit-grid label{padding-left:0;padding-right:0}
      #${PANEL_ID} .popup-edit-actions{display:flex;align-items:center;gap:6px;padding:8px}
      #${PANEL_ID} .popup-edit-actions button{min-height:31px;padding:0 9px;border:1px solid #596773;border-radius:7px;background:#17232d;color:#e9edef;font-size:9px;font-weight:800}
      #${PANEL_ID} .popup-edit-actions button:first-child{background:linear-gradient(180deg,#dce2e6,#adb7bf);color:#111920}
      #${PANEL_ID}.generic-edit .feature-popup>h3,#${PANEL_ID}.generic-edit .feature-popup>.kvp{display:none!important}
      #${PANEL_ID}.generic-edit details.popup-edit{margin-top:10px}

      /* i571 source-safe contextual deletion states. */
      #${PANEL_ID} .tak-context-delete-row-i571{display:flex;gap:8px;padding:0 10px 11px}
      #${PANEL_ID} .tak-context-delete-button-i571{width:100%;min-height:36px;border:1px solid rgba(219,118,111,.64);border-radius:8px;background:rgba(126,39,36,.22);color:#ffd9d6;font-size:12.5px;font-weight:850;cursor:pointer}
      #${PANEL_ID} .tak-context-delete-button-i571:hover,#${PANEL_ID} .tak-context-delete-button-i571:focus-visible{border-color:#e4a09b;background:rgba(158,54,49,.34);outline:none}
      #${PANEL_ID} .tak-context-delete-button-i571:disabled{cursor:not-allowed;opacity:.48;background:#17232d;color:#9da8b1;border-color:#53616d}
      #${PANEL_ID} .tak-context-delete-unavailable-i571{padding:0 12px 11px;color:#9da8b1;font-size:10px;line-height:1.4}
      #${PANEL_ID} .tak-context-delete-state-i571{padding:14px 14px 15px}
      #${PANEL_ID} .tak-context-delete-state-i571 h3{margin:0 0 8px;color:#f1f4f6;font-size:16px;line-height:1.25;overflow-wrap:anywhere}
      #${PANEL_ID} .tak-context-delete-state-i571 p{margin:0;color:#c8d1d7;font-size:11px;line-height:1.5}
      #${PANEL_ID} .tak-context-delete-summary-i571{display:grid;grid-template-columns:88px minmax(0,1fr);margin-top:12px;border:1px solid rgba(203,210,216,.17);border-radius:9px;overflow:hidden;background:rgba(4,10,15,.32)}
      #${PANEL_ID} .tak-context-delete-summary-i571 b,#${PANEL_ID} .tak-context-delete-summary-i571 span{min-width:0;padding:7px 8px;border-bottom:1px solid rgba(203,210,216,.10);font-size:10px;line-height:1.35;overflow-wrap:anywhere}
      #${PANEL_ID} .tak-context-delete-summary-i571 b{color:#9faab3;text-transform:uppercase;letter-spacing:.04em}
      #${PANEL_ID} .tak-context-delete-summary-i571 span{color:#edf1f4}
      #${PANEL_ID} .tak-context-delete-warning-i571{margin-top:11px!important;color:#d9a4a0!important}
      #${PANEL_ID} .tak-context-delete-error-i571{margin-top:11px;padding:9px 10px;border:1px solid rgba(219,118,111,.45);border-radius:8px;background:rgba(126,39,36,.18);color:#ffd9d6!important}
      #${PANEL_ID} .tak-context-delete-actions-i571{display:flex;justify-content:flex-end;gap:8px;margin-top:13px}
      #${PANEL_ID} .tak-context-delete-actions-i571 button{min-width:94px;min-height:34px;border:1px solid #657480;border-radius:8px;background:#17232d;color:#e8ecef;font-size:11px;font-weight:850;cursor:pointer}
      #${PANEL_ID} .tak-context-delete-actions-i571 button:hover,#${PANEL_ID} .tak-context-delete-actions-i571 button:focus-visible{border-color:#cbd2d8;background:#24323d;outline:none}
      #${PANEL_ID} .tak-context-delete-actions-i571 .danger{border-color:rgba(219,118,111,.65);background:rgba(126,39,36,.25);color:#ffd9d6}
      #${PANEL_ID} .tak-context-delete-actions-i571 .danger:hover{background:rgba(158,54,49,.38)}
      #${PANEL_ID} .tak-context-delete-actions-i571 button:disabled{opacity:.55;cursor:wait}
      #${PANEL_ID} .tak-context-delete-spinner-i571{display:inline-block;width:12px;height:12px;margin-right:7px;border:2px solid rgba(203,210,216,.3);border-top-color:#e4e8eb;border-radius:50%;vertical-align:-2px;animation:takContextDeleteSpinI571 .8s linear infinite}
      @keyframes takContextDeleteSpinI571{to{transform:rotate(360deg)}}

      @media(max-width:900px){#${PANEL_ID}{width:min(380px,calc(100% - 22px));right:11px}}
      @media(max-height:760px){#${PANEL_ID}{width:min(390px,calc(100% - 22px))}#${BODY_ID} .point-body-i556{gap:5px!important;padding:6px 8px!important}#${BODY_ID} .point-source-strip-i556{padding:5px 6px!important}#${BODY_ID} .point-control-i556{height:30px!important}#${BODY_ID} textarea.point-control-i556{height:42px!important;min-height:42px!important}#${BODY_ID} .point-symbol-stage-i556{width:48px!important;height:48px!important}#${BODY_ID} .point-symbol-stage-i556 img{width:46px!important;height:46px!important}}
    `;
    document.head.appendChild(style);
  }

  function ensurePanel() {
    if (state.panel && state.panel.isConnected) return state.panel;
    const host = mapNode();
    if (!host) return null;
    try {
      if (window.getComputedStyle(host).position === 'static') {
        host.style.position = 'relative';
        host.dataset.takMapContextPositionI571 = 'relative';
      }
    } catch (_) {}
    const panel = document.createElement('aside');
    panel.id = PANEL_ID;
    panel.className = 'collapsed';
    panel.setAttribute('aria-hidden', 'true');
    panel.setAttribute('aria-label', 'Selected map object details');
    panel.innerHTML = `<div class="tak-context-head-i571"><div class="tak-context-head-copy-i571"><div class="tak-context-kicker-i571" id="takMapContextKickerI571">Object Details</div><div class="tak-context-title-i571" id="takMapContextTitleI571">Selected object</div></div><button type="button" class="tak-context-hide-i571" id="takMapContextHideI571" title="Hide details" aria-label="Hide details">›</button></div><div id="${BODY_ID}"></div>`;
    host.appendChild(panel);
    state.panel = panel;
    state.body = panel.querySelector('#' + BODY_ID);
    try {
      const L = window.L;
      if (L && L.DomEvent) {
        if (typeof L.DomEvent.disableClickPropagation === 'function') L.DomEvent.disableClickPropagation(panel);
        if (typeof L.DomEvent.disableScrollPropagation === 'function') L.DomEvent.disableScrollPropagation(panel);
      }
    } catch (error) { state.errors.push(`leaflet-isolation:${error.message || error}`); }
    ['click','mousedown','pointerdown','touchstart','dblclick','contextmenu','wheel'].forEach(type => {
      panel.addEventListener(type, event => event.stopPropagation(), {capture:false, passive:type === 'touchstart' || type === 'wheel'});
    });
    panel.querySelector('#takMapContextHideI571').addEventListener('click', event => { event.preventDefault(); event.stopPropagation(); hide('button'); });
    state.body.addEventListener('click', handleBodyClick, true);
    state.body.addEventListener('toggle', handleGenericToggle, true);
    positionPanel();
    try {
      if (window.ResizeObserver) {
        state.resizeObserver = new ResizeObserver(positionPanel);
        state.resizeObserver.observe(host);
      }
    } catch (_) {}
    return panel;
  }

  function positionPanel() {
    const panel = ensurePanel();
    const host = mapNode();
    if (!panel || !host) return;
    try {
      const hostRect = host.getBoundingClientRect();
      const scale = host.querySelector('.leaflet-control-scale') || document.querySelector('.leaflet-control-scale');
      let bottom = 14;
      if (scale) {
        const rect = scale.getBoundingClientRect();
        if (rect.width && rect.height) bottom = Math.max(14, Math.ceil(hostRect.bottom - rect.top + 10));
      }
      panel.style.setProperty('--tak-context-bottom-i571', `${bottom}px`);
      const available = Math.max(220, hostRect.height - bottom - 12);
      panel.style.maxHeight = `${available}px`;
      const measured = panel.getBoundingClientRect();
      panel.classList.toggle('compact-height-i571', measured.height > available);
    } catch (error) { state.errors.push(`position:${error.message || error}`); }
  }

  function setHeader(kicker, title) {
    const k = document.getElementById('takMapContextKickerI571');
    const t = document.getElementById('takMapContextTitleI571');
    if (k) k.textContent = text(kicker) || 'Object Details';
    if (t) t.textContent = text(title) || 'Selected object';
  }

  function openPanel() {
    const panel = ensurePanel();
    if (!panel) return;
    panel.classList.remove('collapsed');
    panel.setAttribute('aria-hidden', 'false');
    positionPanel();
    requestAnimationFrame(positionPanel);
  }

  function objectKey(object, source) {
    const registry = window.TakMapIconRegistryI571 || window.TakMapIconRegistryI556;
    try {
      if (registry && registry.isPoint && registry.isPoint(object)) {
        const local = registry.pointLocalId && registry.pointLocalId(object);
        if (local) return `local-point:${local}`;
        const uid = registry.pointUid && registry.pointUid(object);
        const mission = registry.pointMission && registry.pointMission(object);
        if (uid) return `datasync-point:${mission || ''}:${uid}`;
      }
    } catch (_) {}
    const uid = text(object && (object.event_uid || object.cot_uid || object.uid || object.id || object._local_id || object.local_id));
    if (uid) return `${source || 'object'}:${uid}`;
    const name = text(object && (object.callsign || object.name || object.title));
    const center = objectCenter(object, object && object.__layer);
    return `${source || 'object'}:${name}:${center ? center.join(',') : ''}`;
  }

  function kindOf(object) {
    try {
      if (typeof window.dataSyncCategory === 'function') {
        const category = text(window.dataSyncCategory(object));
        if (/route|track|line/i.test(category)) return 'Route';
        if (/shape|area|polygon|circle|rectangle/i.test(category)) return 'Shape';
        if (/point|marker/i.test(category)) return 'Point';
      }
    } catch (_) {}
    const geometry = text(object && (object.geometry || object.kind || object.category || object.type)).toLowerCase();
    if (/route|line|string|track/.test(geometry) || (Array.isArray(object && object.coords) && (object.coords || []).length === 2)) return 'Route';
    if (/shape|area|polygon|circle|rectangle/.test(geometry)) return 'Shape';
    if (finite(object && object.lat) && finite(object && object.lon)) return 'Point';
    return 'Map Object';
  }

  function objectName(object) {
    return text(object && (object.callsign || object.name || object.title || object.uid || object.id)) || kindOf(object);
  }

  function objectCenter(object, layer) {
    try {
      if (layer && typeof layer.getLatLng === 'function') {
        const ll = layer.getLatLng();
        if (ll && finite(ll.lat) && finite(ll.lng)) return [Number(ll.lat), Number(ll.lng)];
      }
      if (layer && typeof layer.getBounds === 'function') {
        const bounds = layer.getBounds();
        const ll = bounds && bounds.getCenter && bounds.getCenter();
        if (ll && finite(ll.lat) && finite(ll.lng)) return [Number(ll.lat), Number(ll.lng)];
      }
    } catch (_) {}
    if (finite(object && object.lat) && finite(object && object.lon)) return [Number(object.lat), Number(object.lon)];
    try {
      if (typeof window.objectCenter === 'function') {
        const value = window.objectCenter(object);
        if (Array.isArray(value) && finite(value[0]) && finite(value[1])) return [Number(value[0]), Number(value[1])];
      }
    } catch (_) {}
    return null;
  }

  function popupContent(layer) {
    try {
      const popup = layer && layer.getPopup && layer.getPopup();
      const content = popup && popup.getContent ? popup.getContent() : (popup && popup._content);
      if (typeof content === 'string') return content;
      if (content && content.outerHTML) return content.outerHTML;
      if (content && content.innerHTML) return content.innerHTML;
    } catch (_) {}
    return '';
  }

  function infoHtml(object, source, layer) {
    const registry = window.TakMapIconRegistryI571 || window.TakMapIconRegistryI556;
    try {
      if (registry && registry.isPoint && registry.isPoint(object) && typeof registry.pointInfoHtml === 'function') {
        return registry.pointInfoHtml(object, registry.isLocalPoint && registry.isLocalPoint(object) ? 'local' : source);
      }
    } catch (_) {}
    try {
      if (typeof window.layerPopupForObject === 'function') return window.layerPopupForObject(object, kindOf(object));
    } catch (_) {}
    const captured = text(layer && layer.__takMapI571InfoHtml) || popupContent(layer);
    if (captured) return captured;
    const center = objectCenter(object, layer);
    return `<div class="feature-popup"><h3>${esc(objectName(object))}</h3><div class="kvp"><b>Category</b><span>${esc(kindOf(object))}</span>${center ? `<b>Coordinates</b><span>${esc(center[0].toFixed(6)+', '+center[1].toFixed(6))}</span>` : ''}<b>Source</b><span>${esc(source || object && object.source || 'TAK Map')}</span></div></div>`;
  }

  function renderInfo() {
    if (!state.selected || !ensurePanel()) return;
    state.mode = 'info';
    state.panel.classList.remove('generic-edit');
    setHeader(kindOf(state.selected.object), objectName(state.selected.object));
    state.body.innerHTML = infoHtml(state.selected.object, state.selected.source, state.selected.layer);
    state.body.querySelectorAll('.leaflet-popup-close-button').forEach(node => node.remove());
    appendInfoDeleteAction();
    sanitizeSidebarDeleteButtons();
    openPanel();
  }

  function centerSelected() {
    const m = mapInstance();
    if (!m || !state.selected) return;
    const center = objectCenter(state.selected.object, state.selected.layer);
    if (!center) return;
    try { m.panTo(center, {animate:true, duration:.25}); } catch (_) { try { m.setView(center, m.getZoom(), {animate:true}); } catch (_) {} }
  }

  function showObject(object, source, layer, shouldCenter) {
    if (!object) return;
    const key = objectKey(object, source);
    state.selected = {object, source:source || 'datasync', layer:layer || object.__layer || null, key, center:objectCenter(object, layer || object.__layer)};
    state.suppressMapClickUntil = Date.now() + 360;
    renderInfo();
    if (shouldCenter !== false) centerSelected();
  }

  function hide(reason) {
    const panel = ensurePanel();
    if (!panel || panel.classList.contains('collapsed')) return;
    state.hiding = true;
    try {
      const editor = document.getElementById('takMapPointEditorI556');
      if (editor && editor.classList.contains('active')) {
        const registry = window.TakMapIconRegistryI571 || window.TakMapIconRegistryI556;
        if (registry && typeof registry.closePointEditor === 'function') registry.closePointEditor(reason || 'hide');
      }
    } catch (_) {}
    panel.classList.add('collapsed');
    panel.classList.remove('generic-edit');
    panel.setAttribute('aria-hidden', 'true');
    state.mode = 'info';
    state.selected = null;
    setTimeout(() => { state.hiding = false; if (state.body) state.body.innerHTML = ''; }, 230);
  }

  function lifecycleApi() {
    return window.TakMapObjectLifecycleV486 || window.TakMapObjectLifecycleV482 || null;
  }

  function canonicalDeleteId(object, source) {
    const lifecycle = lifecycleApi();
    try {
      if (lifecycle && typeof lifecycle.canonicalId === 'function') {
        const value = text(lifecycle.canonicalId(object, source));
        if (value) return value;
      }
    } catch (_) {}
    let value = text(object && (object.canonical_id || object._takCanonicalObjectId || object.object_id || object.local_id || object._local_id));
    if (!value) return '';
    if (value.startsWith('datasync:') || value.startsWith('local:')) return value;
    if (source === 'datasync') return value.startsWith('datasync-') ? `datasync:${value}` : '';
    if (source === 'local') return value.startsWith('local-') ? `local:${value}` : `local:${value}`;
    return '';
  }

  function deleteCapability(object, source) {
    const objectId = canonicalDeleteId(object, source);
    if (!objectId) return {supported:false, objectId:'', reason:'Delete unavailable: this object has no verified source-owned identity.'};
    if (source === 'datasync' && object && object.delete_supported !== true) {
      return {supported:false, objectId, reason:text(object.delete_unavailable_reason) || 'Delete unavailable: OpenTAKServer Mission ownership could not be verified.'};
    }
    if (source !== 'datasync' && source !== 'local') return {supported:false, objectId, reason:'Delete unavailable for this source.'};
    return {supported:true, objectId, reason:''};
  }

  function appendInfoDeleteAction() {
    if (!state.body || !state.selected) return;
    state.body.querySelectorAll('.tak-context-delete-row-i571,.tak-context-delete-unavailable-i571').forEach(node => node.remove());
    const capability = deleteCapability(state.selected.object, state.selected.source);
    const row = document.createElement('div');
    row.className = 'tak-context-delete-row-i571';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'tak-context-delete-button-i571';
    button.dataset.takI571DeleteCurrent = '1';
    button.textContent = `Delete ${kindOf(state.selected.object).replace(' / Area','')}`;
    if (!capability.supported) {
      button.disabled = true;
      button.title = capability.reason;
      button.setAttribute('aria-describedby','takContextDeleteUnavailableI571');
    }
    row.appendChild(button);
    state.body.appendChild(row);
    if (!capability.supported) {
      const note = document.createElement('div');
      note.id = 'takContextDeleteUnavailableI571';
      note.className = 'tak-context-delete-unavailable-i571';
      note.textContent = capability.reason;
      state.body.appendChild(note);
    }
  }

  function sourceLabel(object, source) {
    if (source === 'local') return 'Local Data';
    const mission = text(object && (object.mission_name || object.mission));
    return mission ? `Data Sync · ${mission}` : 'Data Sync';
  }

  function selectedLocation() {
    if (!state.selected) return '';
    const center = objectCenter(state.selected.object, state.selected.layer);
    if (!center) return '';
    try { if (typeof window.formatCoords === 'function') return text(window.formatCoords(center[0], center[1])); } catch (_) {}
    return `${Number(center[0]).toFixed(6)}, ${Number(center[1]).toFixed(6)}`;
  }

  function renderDeleteConfirmation(errorText) {
    if (!state.selected || !ensurePanel()) return;
    state.mode = errorText ? 'delete-error' : 'delete-confirm';
    state.panel.classList.remove('generic-edit');
    const object = state.selected.object;
    const capability = deleteCapability(object, state.selected.source);
    setHeader(errorText ? 'Delete Failed' : `Delete ${kindOf(object).replace(' / Area','')}`, objectName(object));
    const location = selectedLocation();
    const error = text(errorText);
    state.body.innerHTML = `<div class="tak-context-delete-state-i571"><h3>${esc(error ? 'The object was not deleted' : `Delete ${objectName(object)}?`)}</h3><p>${esc(error ? 'TAK Map kept the object and its sidebar open because OpenTAKServer did not confirm deletion.' : 'Review the source-owned object that will be permanently removed.')}</p><div class="tak-context-delete-summary-i571"><b>Type</b><span>${esc(kindOf(object))}</span><b>Source</b><span>${esc(sourceLabel(object,state.selected.source))}</span>${location ? `<b>Location</b><span>${esc(location)}</span>` : ''}</div>${error ? `<p class="tak-context-delete-error-i571">${esc(error)}</p>` : '<p class="tak-context-delete-warning-i571">This action cannot be undone.</p>'}<div class="tak-context-delete-actions-i571"><button type="button" data-i571-delete-cancel>${error ? 'Back' : 'Cancel'}</button><button type="button" class="danger" data-i571-delete-confirm ${capability.supported ? '' : 'disabled'}>${error ? 'Retry Delete' : 'Delete'}</button></div></div>`;
    openPanel();
    positionPanel();
  }

  function renderDeleting() {
    if (!state.selected || !ensurePanel()) return;
    state.mode = 'deleting';
    setHeader('Deleting', objectName(state.selected.object));
    state.body.innerHTML = `<div class="tak-context-delete-state-i571"><h3><span class="tak-context-delete-spinner-i571" aria-hidden="true"></span>Deleting ${esc(objectName(state.selected.object))}</h3><p>Waiting for OpenTAKServer Mission removal, terminal CoT deletion, and absence confirmation.</p><div class="tak-context-delete-actions-i571"><button type="button" disabled>Deleting…</button></div></div>`;
    openPanel();
    positionPanel();
  }

  function deleteFailureFromResult(result, responseStatus) {
    const rows = result && Array.isArray(result.results) ? result.results : [];
    const failed = rows.find(row => row && row.status === 'failed') || rows.find(row => row && row.error);
    const status = Number((failed && failed.http_status) || responseStatus || 0);
    const reason = text((failed && failed.error) || (result && result.error) || 'OpenTAKServer did not confirm deletion.');
    return `${status ? `OpenTAKServer HTTP ${status}: ` : ''}${reason}`;
  }

  async function postCanonicalDelete(objectId) {
    const response = await fetch('/api/tak-map/object-delete', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({object_ids:[objectId]}), cache:'no-store', credentials:'same-origin'});
    let result = {};
    try { result = await response.json(); } catch (_) { throw new Error(`Delete endpoint returned HTTP ${response.status} without a JSON response.`); }
    if (!response.ok) throw new Error(deleteFailureFromResult(result, response.status));
    if (!(result.deleted_ids || []).includes(objectId)) throw new Error(deleteFailureFromResult(result, response.status));
    return result;
  }

  async function refreshAfterDelete(result, source) {
    try { if (result && Array.isArray(result.imports)) { try { lastImports = result.imports; } catch (_) {} window.lastImports = result.imports; } } catch (_) {}
    if (source === 'datasync') {
      try { if (typeof window.refreshDataSync === 'function') await window.refreshDataSync(true,'context-sidebar-delete-i571'); } catch (_) {}
    } else {
      try { if (typeof window.refreshImports === 'function') await window.refreshImports(); } catch (_) {}
      try { if (typeof window.refreshLocalData === 'function') await window.refreshLocalData(); } catch (_) {}
    }
  }

  function removeSelectedLayers() {
    if (!state.selected) return;
    const m = mapInstance();
    const candidates = [state.selected.layer, state.selected.object && state.selected.object.__layer, state.selected.object && state.selected.object.__hitLayer];
    for (const layer of candidates) {
      if (!layer) continue;
      try { if (typeof layer.remove === 'function') layer.remove(); else if (m && typeof m.removeLayer === 'function') m.removeLayer(layer); } catch (_) {}
    }
  }

  async function confirmCurrentDelete() {
    if (state.deleteBusy || !state.selected) return false;
    const selected = state.selected;
    const capability = deleteCapability(selected.object, selected.source);
    if (!capability.supported) { renderDeleteConfirmation(capability.reason); return false; }
    state.deleteBusy = true;
    renderDeleting();
    try {
      const result = await postCanonicalDelete(capability.objectId);
      removeSelectedLayers();
      await refreshAfterDelete(result, selected.source);
      hide('deleted');
      return true;
    } catch (error) {
      renderDeleteConfirmation(text(error && error.message || error));
      return false;
    } finally { state.deleteBusy = false; }
  }

  function beginDeleteForObject(object, source, layer, center) {
    if (!object) return false;
    showObject(object, source || 'datasync', layer || object.__layer || object.__hitLayer || null, center === true);
    renderDeleteConfirmation('');
    return true;
  }

  function deleteDataSyncByIndex(index, event) {
    try { if (event) { event.preventDefault && event.preventDefault(); event.stopPropagation && event.stopPropagation(); event.stopImmediatePropagation && event.stopImmediatePropagation(); } } catch (_) {}
    const data = (window.lastDataSync || (typeof lastDataSync !== 'undefined' && lastDataSync)) || {};
    const object = (data.objects || [])[Number(index)];
    if (!object) return false;
    return beginDeleteForObject(object, 'datasync', object.__layer || object.__hitLayer || null, false);
  }

  function sanitizeDataSyncDeleteButtons(root) {
    const scope = root && root.querySelectorAll ? root : document;
    let buttons = [];
    try { buttons = Array.from(scope.querySelectorAll('#dataSyncRows button[data-tak-delete-source="datasync"],#dataSyncRows button[onclick*="deleteDataSyncItem"]')); } catch (_) {}
    for (const button of buttons) {
      let index = text(button.dataset && button.dataset.takDeleteIndex);
      if (!index) {
        const match = text(button.getAttribute('onclick')).match(/deleteDataSyncItem\((\d+)/);
        if (match) index = match[1];
      }
      if (!index && index !== '0') continue;
      button.removeAttribute('onclick');
      button.removeAttribute('data-tak-delete-source');
      button.removeAttribute('data-tak-delete-index');
      button.dataset.takI571DeleteIndex = index;
      button.title = 'Delete this Data Sync object';
    }
  }

  function sanitizeSidebarDeleteButtons() {
    if (!state.body) return;
    const buttons = Array.from(state.body.querySelectorAll('button[onclick*="deletePopupEdit"],button[data-tak-delete-source]'));
    for (const button of buttons) {
      button.removeAttribute('onclick');
      button.removeAttribute('data-tak-delete-source');
      button.removeAttribute('data-tak-delete-index');
      button.removeAttribute('data-tak-delete-kind');
      button.dataset.takI571DeleteCurrent = '1';
    }
  }

  function installDeleteController() {
    if (window.__takMapDeleteControllerI571Installed) return;
    window.__takMapDeleteControllerI571Installed = true;
    const assign = (name, value) => {
      try { window[name] = value; } catch (_) {}
      try { window.__takI571Assign = value; window.eval(`${name}=window.__takI571Assign`); delete window.__takI571Assign; } catch (_) {}
    };
    assign('deleteDataSyncItem', deleteDataSyncByIndex);
    try { const lifecycle = lifecycleApi(); if (lifecycle) lifecycle.deleteDataSyncItem = deleteDataSyncByIndex; } catch (_) {}
    document.addEventListener('click', event => {
      const target = event.target && event.target.closest && event.target.closest('[data-tak-i571-delete-index],[data-tak-i571-delete-current],[data-i571-delete-confirm],[data-i571-delete-cancel]');
      if (!target) return;
      try { event.preventDefault(); event.stopPropagation(); event.stopImmediatePropagation(); } catch (_) {}
      if (target.hasAttribute('data-i571-delete-cancel')) { renderInfo(); return; }
      if (target.hasAttribute('data-i571-delete-confirm')) { confirmCurrentDelete(); return; }
      if (target.hasAttribute('data-tak-i571-delete-current')) { renderDeleteConfirmation(''); return; }
      deleteDataSyncByIndex(Number(target.dataset.takI571DeleteIndex), event);
    }, true);
    const rows = document.getElementById('dataSyncRows');
    if (rows && window.MutationObserver) {
      state.deletionObserver = new MutationObserver(() => sanitizeDataSyncDeleteButtons(rows));
      state.deletionObserver.observe(rows, {childList:true, subtree:true, attributes:true, attributeFilter:['onclick','data-tak-delete-source','data-tak-delete-index']});
    }
    if (state.body && window.MutationObserver) {
      state.mutationObserver = new MutationObserver(() => sanitizeSidebarDeleteButtons());
      state.mutationObserver.observe(state.body, {childList:true, subtree:true});
    }
    sanitizeDataSyncDeleteButtons(document);
    sanitizeSidebarDeleteButtons();
  }

  async function copyLocation(button) {
    if (!button) return;
    const host = button.closest('.point-popup-location-i571');
    const value = text(host && host.querySelector('.point-popup-location-text-i571') && host.querySelector('.point-popup-location-text-i571').textContent);
    if (!value) return;
    let copied = false;
    try {
      if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
        await navigator.clipboard.writeText(value);
        copied = true;
      }
    } catch (_) {}
    if (!copied) {
      try {
        const helper = document.createElement('textarea');
        helper.value = value;
        helper.setAttribute('readonly', '');
        helper.style.position = 'fixed';
        helper.style.opacity = '0';
        document.body.appendChild(helper);
        helper.select();
        copied = document.execCommand('copy');
        helper.remove();
      } catch (_) {}
    }
    if (!copied) return;
    const original = button.textContent;
    button.textContent = 'Copied';
    button.classList.add('copied');
    button.setAttribute('aria-label', 'Location copied');
    setTimeout(() => {
      if (!button.isConnected) return;
      button.textContent = original || 'Copy';
      button.classList.remove('copied');
      button.setAttribute('aria-label', 'Copy location');
    }, 1200);
  }

  function handleBodyClick(event) {
    const deleteCurrent = event.target && event.target.closest && event.target.closest('[data-tak-i571-delete-current]');
    if (deleteCurrent) {
      event.preventDefault(); event.stopPropagation(); try { event.stopImmediatePropagation(); } catch (_) {}
      renderDeleteConfirmation(''); return;
    }
    const copy = event.target && event.target.closest && event.target.closest('[data-point-copy-location]');
    if (copy) {
      event.preventDefault();
      event.stopPropagation();
      try { event.stopImmediatePropagation(); } catch (_) {}
      copyLocation(copy);
      return;
    }
    const edit = event.target && event.target.closest && event.target.closest('[data-i556-point-edit],[data-i571-point-edit]');
    if (!edit) return;
    event.preventDefault();
    event.stopPropagation();
    try { event.stopImmediatePropagation(); } catch (_) {}
    const registry = window.TakMapIconRegistryI571 || window.TakMapIconRegistryI556;
    if (!registry || typeof registry.openPointEditor !== 'function') return;
    const source = text(edit.getAttribute('data-point-source')) || 'datasync';
    const reference = source === 'local' ? text(edit.getAttribute('data-point-local-id')) : text(edit.getAttribute('data-point-uid'));
    const mission = text(edit.getAttribute('data-point-mission'));
    state.mode = 'edit';
    setHeader('Edit Point', objectName(state.selected && state.selected.object));
    registry.openPointEditor(source, reference, mission);
    setTimeout(adoptPointEditor, 0);
  }

  function adoptPointEditor() {
    if (!state.body) return;
    const modal = document.getElementById('takMapPointEditorI556');
    if (!modal) return;
    if (modal.parentNode !== state.body) state.body.replaceChildren(modal);
    modal.classList.add('active');
    state.mode = 'edit';
    state.panel.classList.remove('generic-edit');
    openPanel();
    sanitizeSidebarDeleteButtons();
    positionPanel();
  }

  function handleGenericToggle(event) {
    const details = event.target;
    if (!details || !details.matches || !details.matches('details.popup-edit')) return;
    if (details.open) {
      state.mode = 'edit';
      state.panel.classList.add('generic-edit');
      setHeader(`Edit ${kindOf(state.selected && state.selected.object)}`, objectName(state.selected && state.selected.object));
    } else {
      state.mode = 'info';
      state.panel.classList.remove('generic-edit');
      setHeader(kindOf(state.selected && state.selected.object), objectName(state.selected && state.selected.object));
    }
    positionPanel();
  }

  function onPointEditorOpening(source, reference, mission) {
    state.mode = 'edit';
    setHeader('Edit Point', objectName(state.selected && state.selected.object) || reference);
    openPanel();
    setTimeout(adoptPointEditor, 0);
  }

  function onPointSaved(point, source) {
    if (point && state.selected) {
      state.selected.object = Object.assign({}, state.selected.object || {}, point);
      state.selected.source = source || state.selected.source;
      state.selected.center = objectCenter(state.selected.object, state.selected.layer);
    }
  }

  function onPointEditorClosed(reason, previous, previousSource) {
    if (state.hiding || !state.panel || state.panel.classList.contains('collapsed')) return;
    state.mode = 'info';
    state.panel.classList.remove('generic-edit');
    if (state.selected) renderInfo();
    else if (previous) showObject(previous, previousSource || 'datasync', previous.__layer || null, false);
  }

  function layerClickHandler(event) {
    const layer = event && (event.target || event.sourceTarget) || this;
    const record = state.layerObjects.get(layer);
    if (!record) return;
    state.suppressMapClickUntil = Date.now() + 360;
    try { if (event.originalEvent && window.L && window.L.DomEvent) window.L.DomEvent.stop(event.originalEvent); } catch (_) {}
    showObject(record.object, record.source, layer, true);
  }

  function bindObjectLayer(layer, object, source) {
    if (!layer || !object || typeof layer.on !== 'function') return layer;
    const key = objectKey(object, source);
    const previous = state.layerObjects.get(layer);
    if (previous && previous.key === key) { previous.object = object; previous.source = source; }
    try { if (!layer.__takMapI571InfoHtml) layer.__takMapI571InfoHtml = popupContent(layer); } catch (_) {}
    try { if (typeof layer.unbindPopup === 'function') layer.unbindPopup(); } catch (_) {}
    try { layer.off('mouseover'); layer.off('mouseout'); layer.off('popupopen'); layer.off('popupclose'); layer.off('click'); } catch (_) {}
    try { layer.on('click', layerClickHandler); } catch (error) { state.errors.push(`bind:${error.message || error}`); }
    const record = {object, source:source || 'datasync', key};
    state.layerObjects.set(layer, record);
    state.keyLayers.set(key, layer);
    try { layer.options = layer.options || {}; layer.options.bubblingMouseEvents = false; } catch (_) {}
    return layer;
  }

  function scanObjects() {
    const rows = [];
    try {
      const data = (typeof lastDataSync !== 'undefined' && lastDataSync && lastDataSync.objects) || (window.lastDataSync && window.lastDataSync.objects) || [];
      for (const object of data) rows.push([object, 'datasync']);
    } catch (_) {}
    try {
      const imported = typeof window.importedFeatures === 'function' ? window.importedFeatures() : (typeof importedFeatures === 'function' ? importedFeatures() : []);
      for (const object of imported || []) rows.push([object, 'local']);
    } catch (_) {}
    for (const [object, source] of rows) {
      if (object && object.__layer) bindObjectLayer(object.__layer, object, source);
      if (object && object.__hitLayer) bindObjectLayer(object.__hitLayer, object, source);
      if (state.selected && objectKey(object, source) === state.selected.key) {
        state.selected.object = object;
        state.selected.source = source;
        state.selected.layer = object.__layer || object.__hitLayer || state.selected.layer;
        state.selected.center = objectCenter(object, state.selected.layer);
      }
    }
    if (state.selected && state.mode === 'info' && state.panel && !state.panel.classList.contains('collapsed')) renderInfo();
  }

  function assignGlobal(name, value) {
    try { window[name] = value; } catch (_) {}
    try { window.__takMapI571Global = value; window.eval(`${name}=window.__takMapI571Global`); delete window.__takMapI571Global; } catch (_) {}
  }

  function wrapRuntime() {
    if (!state.wrapped.addObjectLayer && typeof window.addObjectLayer === 'function') {
      const base = window.addObjectLayer;
      const wrapper = function (group, object, sourceKey) {
        const layer = base.apply(this, arguments);
        setTimeout(() => {
          if (object && object.__layer) bindObjectLayer(object.__layer, object, sourceKey || 'datasync');
          if (object && object.__hitLayer) bindObjectLayer(object.__hitLayer, object, sourceKey || 'datasync');
          if (layer) bindObjectLayer(layer, object, sourceKey || 'datasync');
        }, 0);
        return layer;
      };
      wrapper.__takMapContextI571 = true;
      state.wrapped.addObjectLayer = base;
      assignGlobal('addObjectLayer', wrapper);
    }
    for (const name of ['drawDataSyncObjects','drawImportedObjects']) {
      if (!state.wrapped[name] && typeof window[name] === 'function') {
        const base = window[name];
        const wrapper = function () { const result = base.apply(this, arguments); setTimeout(scanObjects, 0); setTimeout(scanObjects, 80); return result; };
        wrapper.__takMapContextI571 = true;
        state.wrapped[name] = base;
        assignGlobal(name, wrapper);
      }
    }
    if (!state.wrapped.centerDataSyncIndex && typeof window.centerDataSyncIndex === 'function') {
      const base = window.centerDataSyncIndex;
      const wrapper = async function (index) {
        const object = ((window.lastDataSync || (typeof lastDataSync !== 'undefined' && lastDataSync)) || {}).objects?.[Number(index)];
        if (object) { showObject(object, 'datasync', object.__layer || object.__hitLayer, true); return; }
        return base.apply(this, arguments);
      };
      state.wrapped.centerDataSyncIndex = base;
      assignGlobal('centerDataSyncIndex', wrapper);
    }
    if (!state.wrapped.centerLocalItem && typeof window.centerLocalItem === 'function') {
      const base = window.centerLocalItem;
      const wrapper = function (kind, id, event) {
        if (event && event.stopPropagation) event.stopPropagation();
        let object = null;
        try { object = typeof window.localDataFeatureById === 'function' ? window.localDataFeatureById(id) : (typeof localDataFeatureById === 'function' ? localDataFeatureById(id) : null); } catch (_) {}
        if (object) { showObject(object, 'local', object.__layer || object.__hitLayer, true); return; }
        return base.apply(this, arguments);
      };
      state.wrapped.centerLocalItem = base;
      assignGlobal('centerLocalItem', wrapper);
    }
    if (!state.wrapped.renderDataSyncRowsI571 && typeof window.renderDataSyncRows === 'function') {
      const base = window.renderDataSyncRows;
      const wrapper = function () { const result = base.apply(this, arguments); sanitizeDataSyncDeleteButtons(document); return result; };
      wrapper.__takMapContextI571 = true;
      state.wrapped.renderDataSyncRowsI571 = base;
      assignGlobal('renderDataSyncRows', wrapper);
    }
    if (!state.wrapped.chooseSearchItem && typeof window.chooseSearchItem === 'function') {
      const base = window.chooseSearchItem;
      const wrapper = function (id) {
        try {
          const item = (window.mapSearchItems || (typeof mapSearchItems !== 'undefined' && mapSearchItems) || []).find(row => row.id === id);
          const record = item && item.layer && state.layerObjects.get(item.layer);
          if (record) { showObject(record.object, record.source, item.layer, true); return; }
        } catch (_) {}
        return base.apply(this, arguments);
      };
      state.wrapped.chooseSearchItem = base;
      assignGlobal('chooseSearchItem', wrapper);
    }
  }

  function selectedStillVisible() {
    if (!state.selected) return false;
    const m = mapInstance();
    const center = objectCenter(state.selected.object, state.selected.layer) || state.selected.center;
    if (!m || !center) return true;
    try { return !!m.getBounds().contains(center); } catch (_) { return true; }
  }

  function installMapEvents() {
    const m = mapInstance();
    if (!m || m.__takMapContextSidebarI571) return false;
    m.__takMapContextSidebarI571 = true;
    m.on('click', event => {
      if (Date.now() < state.suppressMapClickUntil) return;
      const target = event && event.originalEvent && event.originalEvent.target;
      if (target && state.panel && state.panel.contains(target)) return;
      hide('map');
    });
    m.on('moveend zoomend', () => {
      positionPanel();
      if (state.selected && !selectedStillVisible()) hide('offscreen');
    });
    m.on('resize', positionPanel);
    return true;
  }

  function boot() {
    addStyle();
    ensurePanel();
    installDeleteController();
    wrapRuntime();
    installMapEvents();
    scanObjects();
    document.querySelectorAll('.iteration-chip,.iteration-marker').forEach(node => node.textContent = VERSION);
    [100,300,700,1300,2600,5200].forEach(delay => setTimeout(() => { installDeleteController(); wrapRuntime(); installMapEvents(); scanObjects(); sanitizeDataSyncDeleteButtons(document); positionPanel(); }, delay));
    setInterval(() => { installDeleteController(); wrapRuntime(); installMapEvents(); scanObjects(); sanitizeDataSyncDeleteButtons(document); }, 2500);
    window.addEventListener('resize', positionPanel, {passive:true});
    window.addEventListener('orientationchange', () => setTimeout(positionPanel, 80), {passive:true});
    state.installed = true;
  }

  const api = Object.freeze({
    version: VERSION,
    bindObjectLayer,
    showObject,
    hide,
    onPointEditorOpening,
    onPointSaved,
    onPointEditorClosed,
    beginDelete: beginDeleteForObject,
    confirmDelete: confirmCurrentDelete,
    deleteDataSyncItem: deleteDataSyncByIndex,
    refresh: scanObjects,
    diagnostics: () => ({
      version: VERSION,
      installed: state.installed,
      open: !!(state.panel && !state.panel.classList.contains('collapsed')),
      mode: state.mode,
      selectedKey: state.selected && state.selected.key || '',
      boundLayers: state.keyLayers.size,
      bottomAnchored: !!state.panel,
      leafletPopupLifecycleUsed: false,
      silverTheme: !!document.getElementById('takMapContextSidebarStyleI571'),
      contextualDelete: true,
      nativeDeleteDialogs: false,
      sharedDeleteController: true,
      deleteMode: state.mode.startsWith('delete') || state.mode === 'deleting',
      errors: state.errors.slice(),
    }),
  });
  window.TakMapContextSidebarI571 = api;
  window.TakMapDeleteControllerI571 = api;
  window.TakMapContextSidebarI562 = api;

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true});
  else boot();
})(window, document);
