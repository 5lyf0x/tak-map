/* TAK Map i643 contextual sidebar: validated native TAK Shape save transaction, persistent edit sessions, center translation handle, compact in-place controls. */
(function (window, document) {
  'use strict';

  const VERSION = 'i654';
  const PANEL_ID = 'takMapContextSidebarI572';
  const BODY_ID = 'takMapContextSidebarBodyI572';
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
    panelHost: null,
    gatewayOverlayMounted: false,
    windowResizeBound: false,
    infoSignature: '',
    pendingInfoSignature: '',
    shapeEdit: {active:false,snapshot:null,draft:null,draftKey:'',baseObject:null,deferredObject:null,confirmedObject:null,handles:[],labels:[],map:null,eventsBound:false,saveBusy:false,dirty:false,revision:0,lastSaveError:'',lastSaveConfirmation:''},
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
    if (document.getElementById('takMapContextSidebarStyleI572')) return;
    const style = document.createElement('style');
    style.id = 'takMapContextSidebarStyleI572';
    style.textContent = `
      :root{--tak-sidebar-silver-i572:#cbd2d8;--tak-sidebar-silver2-i572:#aeb8c0;--tak-sidebar-line-i572:#52606b;--tak-sidebar-glow-i572:rgba(203,210,216,.18)}

      /* Unified silver-accent theme for both sidebars. */
      #sidebar{--sidebar-accent:#cbd2d8!important;--accent:#cbd2d8!important}
      #sidebar .panel{border-color:rgba(191,201,209,.22)!important}
      #sidebar .panel h2,#sidebar .subgroup-title,#sidebar .datasync-section-title,#sidebar .local-section-title{color:#dfe4e8!important;border-color:rgba(203,210,216,.24)!important}
      
      #sidebar .panel-toggle,#sidebar .toggle,#sidebar .subgroup-label>.toggle,#sidebar .datasync-section-title>.toggle{color:var(--tak-sidebar-silver-i572)!important}
      #sidebar .chip,#sidebar .search-result-chip,#sidebar [class*="count"],#sidebar [class*="chip"]{border-color:rgba(203,210,216,.42)!important;background:rgba(203,210,216,.12)!important;color:#e7ebee!important}
      #sidebar input[type="checkbox"],#sidebar input[type="radio"],#sidebar input[type="range"]{accent-color:var(--tak-sidebar-silver-i572)!important}
      #sidebar input[type="range"]::-webkit-slider-thumb{background:var(--tak-sidebar-silver-i572)!important;border-color:#eef1f3!important}
      #sidebar input[type="range"]::-moz-range-thumb{background:var(--tak-sidebar-silver-i572)!important;border-color:#eef1f3!important}
      #sidebar input[type="range"]::-webkit-slider-runnable-track{background:linear-gradient(90deg,#8f9aa4,#3b4650)!important}
      #sidebar input[type="range"]::-moz-range-track{background:#56616b!important}
      #sidebar .layer-button:hover,#sidebar button:hover,#sidebar .local-data-row:hover{border-color:#aeb8c0!important;background-color:rgba(203,210,216,.10)!important}
      #sidebar .selected-local,#sidebar .active,#sidebar [aria-pressed="true"]{border-color:#cbd2d8!important;box-shadow:inset 3px 0 0 #cbd2d8!important}
      #sidebarTab{border-color:#687681!important;background:linear-gradient(180deg,#26333e,#151f28)!important;color:#dfe4e8!important}
      #reliefOverlayButtonV506{border-color:#56636e!important;background:#18232d!important;color:#dce2e6!important}
      #reliefOverlayButtonV506[aria-pressed="true"]{border-color:#e2e6e9!important;background:linear-gradient(180deg,#dce2e6,#aeb8c0)!important;color:#111920!important;box-shadow:0 0 0 1px rgba(255,255,255,.18)!important}

      #${PANEL_ID}{box-sizing:border-box;position:absolute;right:14px;bottom:var(--tak-context-bottom-i572,54px);width:min(320px,calc(100% - 24px));height:auto;max-width:min(320px,calc(100% - 24px));z-index:4700;color:#edf1f4;background:linear-gradient(180deg,rgba(17,29,40,.985),rgba(7,15,23,.992));border:1px solid #596671;border-radius:13px;box-shadow:0 22px 64px rgba(0,0,0,.62);transform:translateX(0);opacity:1;transition:transform .22s ease,opacity .18s ease;pointer-events:auto;overflow:visible;contain:layout style}
      #${PANEL_ID}.collapsed{transform:translateX(calc(100% + 26px));opacity:0;pointer-events:none}
      #${PANEL_ID} .tak-context-head-i572{min-height:45px;display:flex;align-items:center;gap:8px;padding:0 8px 0 12px;border-bottom:1px solid rgba(203,210,216,.23);background:linear-gradient(180deg,#1a2833,#111c25);border-radius:12px 12px 0 0}
      #${PANEL_ID} .tak-context-head-copy-i572{min-width:0;flex:1}
      #${PANEL_ID} .tak-context-kicker-i572{color:#9da8b1;font-size:9.5px;font-weight:850;letter-spacing:.1em;text-transform:uppercase}
      #${PANEL_ID} .tak-context-title-i572{overflow:hidden;color:#e7ebee;font-size:13.5px;font-weight:850;line-height:1.2;text-overflow:ellipsis;white-space:nowrap}
      #${PANEL_ID} .tak-context-hide-i572{width:32px;height:32px;display:grid;place-items:center;border:1px solid #60707c;border-radius:8px;background:#17232d;color:#e4e8eb;font-size:20px;line-height:1;cursor:pointer}
      #${PANEL_ID} .tak-context-hide-i572:hover{border-color:#d7dde1;background:#25323d}
      #${BODY_ID}{box-sizing:border-box;width:100%;min-width:0;max-width:100%;height:auto;max-height:none;margin:0;padding:0;overflow:visible!important;overscroll-behavior:contain;background:rgba(8,13,18,.97)}
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
      #${PANEL_ID} .point-popup-location-i572{display:flex!important;align-items:center!important;gap:8px!important}
      #${PANEL_ID} .point-popup-location-text-i572{min-width:0;flex:1;overflow-wrap:anywhere}
      #${PANEL_ID} .point-popup-copy-i572{flex:0 0 auto;min-height:28px;padding:0 9px;border:1px solid #71808b;border-radius:7px;color:#e6eaed;background:#17232d;font-size:9.5px;font-weight:850;cursor:pointer}
      #${PANEL_ID} .point-popup-copy-i572:hover{border-color:#cbd2d8;background:#23313c}
      #${PANEL_ID} .point-popup-copy-i572.copied{color:#111920;background:linear-gradient(180deg,#dce2e6,#aeb8c0)}
      #${PANEL_ID} .point-popup-time-i572{font-variant-numeric:tabular-nums}
      #${PANEL_ID} .point-popup-sync-i572{display:inline-flex;align-items:center;gap:6px;padding:4px 8px;border:1px solid rgba(203,210,216,.48);border-radius:999px;background:rgba(203,210,216,.11);font-size:10px;font-weight:850;white-space:nowrap}
      #${PANEL_ID} .point-popup-sync-dot-i572{width:7px;height:7px;flex:0 0 auto;border-radius:50%;background:#d7dde1;box-shadow:0 0 0 3px rgba(203,210,216,.10)}
      #${PANEL_ID} .point-popup-sync-i572.state-pending .point-popup-sync-dot-i572{background:#e5cf8b}
      #${PANEL_ID} .point-popup-sync-i572.state-stale .point-popup-sync-dot-i572{background:#c9a27d}
      #${PANEL_ID} .point-popup-sync-i572.state-conflict .point-popup-sync-dot-i572,#${PANEL_ID} .point-popup-sync-i572.state-remote-deleted .point-popup-sync-dot-i572{background:#d99595}

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
      #${PANEL_ID} details.popup-edit{box-sizing:border-box;width:100%;margin:0;border:0;border-radius:9px;background:transparent;overflow:visible}
      #${PANEL_ID} details.popup-edit>summary{display:none!important}
      #${PANEL_ID} details.popup-edit>summary::-webkit-details-marker{display:none}
      #${PANEL_ID} details.popup-edit[open]>summary{display:none!important}
      #${PANEL_ID} .tak-shape-edit-toggle-i639{box-sizing:border-box;width:100%;min-height:36px;display:flex;align-items:center;justify-content:center;margin:12px 0 0;border:1px solid #9ea9b3;border-radius:8px;background:linear-gradient(180deg,#dce2e6,#adb7bf);color:#111920;font-size:12px;font-weight:850;cursor:pointer}
      #${PANEL_ID} .tak-shape-edit-toggle-i639:hover,#${PANEL_ID} .tak-shape-edit-toggle-i639:focus-visible{filter:brightness(1.05);outline:none}
      #${PANEL_ID} .tak-v322-popup{box-sizing:border-box!important;width:100%!important;min-width:0!important;max-width:100%!important;margin:0!important;border-radius:0!important;background:transparent!important;overflow:visible!important}
      #${PANEL_ID} .tak-v322-bar{box-sizing:border-box!important;width:100%!important;margin:0!important}
      #${PANEL_ID} .tak-v322-inner{box-sizing:border-box!important;width:100%!important;margin:0!important;padding:14px 15px 13px!important}
      #${PANEL_ID} .tak-v322-table{width:100%!important}
      #${PANEL_ID} .tak-geometry-i638 span,#${PANEL_ID} .tak-geometry-i639 span{font-variant-numeric:tabular-nums}

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

      /* i639 Shape editor: in-place fields, silver/gray TAK Map controls, compact action spacing. */
      #${PANEL_ID}.shape-context-i639 .tak-context-head-i572{min-height:34px}
      #${PANEL_ID}.shape-context-i639 .tak-context-title-i572{display:none!important}
      #${PANEL_ID}.shape-context-i639 .tak-v322-inner{padding-bottom:4px!important}
      #${PANEL_ID}.shape-context-i639 .tak-shape-edit-toggle-i639{margin:8px 0 2px!important;border-color:#aeb8c0!important;background:linear-gradient(180deg,#e0e5e8,#aeb7be)!important;color:#111920!important}
      #${PANEL_ID}.shape-context-i639 .tak-context-delete-row-i572{padding:5px 15px 9px!important}
      #${PANEL_ID}.shape-context-i639 .tak-context-delete-button-i572{border-color:#7f8b95!important;background:linear-gradient(180deg,#4e5b65,#2b353d)!important;color:#f0f3f5!important}
      #${PANEL_ID}.shape-context-i639 .tak-context-delete-button-i572:hover,#${PANEL_ID}.shape-context-i639 .tak-context-delete-button-i572:focus-visible{border-color:#cbd2d8!important;background:linear-gradient(180deg,#65727c,#39444d)!important;color:#fff!important}
      #${PANEL_ID}.shape-context-i639 .tak-v322-actions,#${PANEL_ID}.shape-context-i639 .popup-edit-actions{padding:6px 0 2px!important;margin:0!important;gap:7px!important;background:transparent!important;border:0!important}
      #${PANEL_ID}.shape-context-i639 .tak-v322-actions button,#${PANEL_ID}.shape-context-i639 .popup-edit-actions button{min-height:31px!important;border:1px solid #7b8892!important;border-radius:7px!important;background:linear-gradient(180deg,#4d5a64,#2a353d)!important;color:#f0f3f5!important;font-weight:850!important}
      #${PANEL_ID}.shape-context-i639 .tak-v322-actions button:first-child,#${PANEL_ID}.shape-context-i639 .popup-edit-actions button:first-child{border-color:#b8c1c8!important;background:linear-gradient(180deg,#e0e5e8,#aeb7be)!important;color:#111920!important}
      #${PANEL_ID}.shape-context-i639 .tak-v322-actions button:hover,#${PANEL_ID}.shape-context-i639 .popup-edit-actions button:hover{filter:brightness(1.08)!important}
      #${PANEL_ID}.shape-context-i639 .tak-v322-title{font-weight:400!important}
      #${PANEL_ID}.shape-context-i639 .tak-shape-name-input-i639{box-sizing:border-box!important;width:100%!important;min-height:31px!important;margin:0!important;padding:5px 7px!important;border:1px solid #71808b!important;border-radius:7px!important;background:#08121a!important;color:#f1f4f6!important;font-size:14px!important;font-weight:400!important}
      #${PANEL_ID}.shape-context-i639 .tak-shape-center-input-i639,#${PANEL_ID}.shape-context-i639 .tak-shape-notes-input-i639{box-sizing:border-box!important;width:100%!important;margin:0!important;padding:5px 7px!important;border:1px solid #61707b!important;border-radius:6px!important;background:#08121a!important;color:#edf1f4!important;font-size:10.5px!important;text-transform:none!important}
      #${PANEL_ID}.shape-context-i639 .tak-shape-notes-input-i639{min-height:54px!important;resize:vertical!important}
      #${PANEL_ID}.shape-context-i639.shape-editing-i639 details.popup-edit{display:block!important;margin:0!important;padding:0!important;border:0!important;background:transparent!important}
      #${PANEL_ID}.shape-context-i639.shape-editing-i639 .tak-shape-edit-toggle-i639{display:none!important}
      #${PANEL_ID}.shape-context-i639 .tak-shape-edit-actions-i640{display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;width:100%!important;max-width:none!important;gap:8px!important;padding:7px 0 2px!important;margin:0!important}
      #${PANEL_ID}.shape-context-i639 .tak-shape-edit-actions-i640 button{box-sizing:border-box!important;width:100%!important;max-width:none!important;min-width:0!important;flex:1 1 0!important;min-height:33px!important;border:1px solid #8a969f!important;border-radius:7px!important;background:linear-gradient(180deg,#d9dfe3,#9da8b0)!important;color:#111920!important;font-size:11.5px!important;font-weight:800!important}
      #${PANEL_ID}.shape-context-i639 .tak-shape-edit-actions-i640 button:hover,#${PANEL_ID}.shape-context-i639 .tak-shape-edit-actions-i640 button:focus-visible{filter:brightness(1.06)!important;outline:none}
      #${PANEL_ID}.shape-context-i639 .tak-shape-edit-actions-i640 button:disabled{opacity:.55!important;cursor:wait!important}
      #${PANEL_ID}.shape-context-i639 .popup-edit-status{padding:4px 0 0!important;color:#c5ced4!important;font-size:10px!important;min-height:0!important}
      .tak-shape-vector-wrap-i639{background:transparent!important;border:0!important}
      .tak-shape-vector-i639{display:block;box-sizing:border-box;width:14px;height:14px;border:2px solid #f1f4f6;border-radius:3px;background:#6f7b84;box-shadow:0 0 0 2px rgba(15,24,31,.92),0 2px 8px rgba(0,0,0,.7);cursor:move}
      .tak-shape-vector-i639.center{width:16px;height:16px;border-radius:999px;background:#cbd2d8;box-shadow:0 0 0 2px rgba(15,24,31,.95),0 0 0 4px rgba(203,210,216,.28),0 2px 8px rgba(0,0,0,.7)}
      .tak-shape-vector-i639.major{transform:rotate(45deg);background:#9ea9b3}
      .tak-shape-vector-i639.minor{transform:rotate(45deg);background:#707d87}
      .tak-shape-distance-wrap-i639{background:transparent!important;border:0!important;overflow:visible!important;pointer-events:none!important}
      .tak-shape-distance-i639{display:inline-block;transform:translate(-50%,-50%);white-space:nowrap;padding:2px 5px;border:1px solid rgba(203,210,216,.68);border-radius:5px;background:rgba(12,20,27,.91);color:#eef2f4;font-size:10px;font-weight:850;line-height:1.15;box-shadow:0 2px 7px rgba(0,0,0,.55)}

      /* i572 source-safe contextual deletion states. */
      #${PANEL_ID} .tak-context-delete-row-i572{box-sizing:border-box;display:flex;justify-content:center;gap:8px;width:100%;margin:0;padding:12px 15px 11px}
      #${PANEL_ID} .tak-context-delete-button-i572{box-sizing:border-box;width:100%;max-width:none;margin:0;min-height:36px;border:1px solid rgba(219,118,111,.64);border-radius:8px;background:rgba(126,39,36,.22);color:#ffd9d6;font-size:12.5px;font-weight:850;cursor:pointer}
      #${PANEL_ID} .tak-context-delete-button-i572:hover,#${PANEL_ID} .tak-context-delete-button-i572:focus-visible{border-color:#e4a09b;background:rgba(158,54,49,.34);outline:none}
      #${PANEL_ID} .tak-context-delete-button-i572:disabled{cursor:not-allowed;opacity:.48;background:#17232d;color:#9da8b1;border-color:#53616d}
      #${PANEL_ID} .tak-context-delete-unavailable-i572{padding:0 12px 11px;color:#9da8b1;font-size:10px;line-height:1.4}
      #${PANEL_ID} .tak-context-delete-state-i572{padding:14px 14px 15px}
      #${PANEL_ID} .tak-context-delete-state-i572 h3{margin:0 0 8px;color:#f1f4f6;font-size:16px;line-height:1.25;overflow-wrap:anywhere}
      #${PANEL_ID} .tak-context-delete-state-i572 p{margin:0;color:#c8d1d7;font-size:11px;line-height:1.5}
      #${PANEL_ID} .tak-context-delete-summary-i572{display:grid;grid-template-columns:88px minmax(0,1fr);margin-top:12px;border:1px solid rgba(203,210,216,.17);border-radius:9px;overflow:hidden;background:rgba(4,10,15,.32)}
      #${PANEL_ID} .tak-context-delete-summary-i572 b,#${PANEL_ID} .tak-context-delete-summary-i572 span{min-width:0;padding:7px 8px;border-bottom:1px solid rgba(203,210,216,.10);font-size:10px;line-height:1.35;overflow-wrap:anywhere}
      #${PANEL_ID} .tak-context-delete-summary-i572 b{color:#9faab3;text-transform:uppercase;letter-spacing:.04em}
      #${PANEL_ID} .tak-context-delete-summary-i572 span{color:#edf1f4}
      #${PANEL_ID} .tak-context-delete-warning-i572{margin-top:11px!important;color:#d9a4a0!important}
      #${PANEL_ID} .tak-context-delete-error-i572{margin-top:11px;padding:9px 10px;border:1px solid rgba(219,118,111,.45);border-radius:8px;background:rgba(126,39,36,.18);color:#ffd9d6!important}
      #${PANEL_ID} .tak-context-delete-actions-i572{display:flex;justify-content:flex-end;gap:8px;margin-top:13px}
      #${PANEL_ID} .tak-context-delete-actions-i572 button{min-width:94px;min-height:34px;border:1px solid #657480;border-radius:8px;background:#17232d;color:#e8ecef;font-size:11px;font-weight:850;cursor:pointer}
      #${PANEL_ID} .tak-context-delete-actions-i572 button:hover,#${PANEL_ID} .tak-context-delete-actions-i572 button:focus-visible{border-color:#cbd2d8;background:#24323d;outline:none}
      #${PANEL_ID} .tak-context-delete-actions-i572 .danger{border-color:rgba(219,118,111,.65);background:rgba(126,39,36,.25);color:#ffd9d6}
      #${PANEL_ID} .tak-context-delete-actions-i572 .danger:hover{background:rgba(158,54,49,.38)}
      #${PANEL_ID} .tak-context-delete-actions-i572 button:disabled{opacity:.55;cursor:wait}
      #${PANEL_ID} .tak-context-delete-spinner-i572{display:inline-block;width:12px;height:12px;margin-right:7px;border:2px solid rgba(203,210,216,.3);border-top-color:#e4e8eb;border-radius:50%;vertical-align:-2px;animation:takContextDeleteSpinI572 .8s linear infinite}
      @keyframes takContextDeleteSpinI572{to{transform:rotate(360deg)}}

      /* i618 shared top-level, content-aware context sizing. */
      #${PANEL_ID}.tak-context-top-overlay-i618{position:fixed!important;z-index:2147482000!important;display:flex!important;flex-direction:column!important;width:min(320px,calc(100vw - 24px))!important;max-width:min(320px,calc(100vw - 24px))!important;overflow:hidden!important;contain:layout style!important;scrollbar-gutter:auto!important}
      #${PANEL_ID}.tak-context-top-overlay-i618 .tak-context-head-i572{flex:0 0 auto!important}
      #${PANEL_ID}.tak-context-top-overlay-i618 #${BODY_ID}{flex:1 1 auto!important;min-height:0!important;max-height:none!important;overflow-y:auto!important;overflow-x:hidden!important;scrollbar-gutter:auto!important;scrollbar-width:none!important}
      #${PANEL_ID}.tak-context-top-overlay-i618:not(.gateway-data-readonly-i615) #${BODY_ID}::-webkit-scrollbar{width:0!important;height:0!important;display:none!important}

      /* i615 dedicated read-only Gateway Data context mode. */
      #${PANEL_ID}.gateway-data-readonly-i615{--tak-gateway-readonly-accent-i615:#8da4b2}
      #${PANEL_ID}.gateway-data-readonly-i615,#${PANEL_ID}.gateway-data-readonly-i615 *{animation:none!important}
      #${PANEL_ID}.gateway-data-readonly-i615 .tak-context-head-i572{background:#14212a!important}
      #${PANEL_ID}.gateway-data-readonly-i615 .feature-popup::before,#${PANEL_ID}.gateway-data-readonly-i615 .feature-popup::after,#${PANEL_ID}.gateway-data-readonly-i615 [class*="pulse"],#${PANEL_ID}.gateway-data-readonly-i615 [class*="flash"]{display:none!important;content:none!important}
      #${PANEL_ID}.gateway-data-readonly-i615 details.popup-edit,#${PANEL_ID}.gateway-data-readonly-i615 .popup-edit,#${PANEL_ID}.gateway-data-readonly-i615 .tak-context-delete-row-i572,#${PANEL_ID}.gateway-data-readonly-i615 .tak-context-delete-unavailable-i572,#${PANEL_ID}.gateway-data-readonly-i615 .point-popup-actions-i556,#${PANEL_ID}.gateway-data-readonly-i615 .point-popup-edit-i556,#${PANEL_ID}.gateway-data-readonly-i615 [data-i556-point-edit],#${PANEL_ID}.gateway-data-readonly-i615 [data-i572-point-edit],#${PANEL_ID}.gateway-data-readonly-i615 [data-tak-i572-delete-current],#${PANEL_ID}.gateway-data-readonly-i615 input[type="color"]{display:none!important}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-feature-popup-v491{border:0!important;background:transparent!important;box-shadow:none!important}
      /* i617 top-overlay Gateway Data presentation with themed scrolling. */
      #${PANEL_ID}.gateway-data-readonly-i615.gateway-data-top-overlay-i617{position:fixed!important;z-index:2147482000!important;display:flex!important;flex-direction:column!important;width:clamp(430px,34vw,560px)!important;max-width:calc(100vw - 28px)!important;max-height:calc(100vh - 28px)!important;overflow:hidden!important;contain:layout style!important}
      #${PANEL_ID}.gateway-data-readonly-i615.gateway-data-top-overlay-i617.gateway-data-nifc-i620{width:292px!important;max-width:min(430px,calc(100vw - 28px))!important}
      #${PANEL_ID}.gateway-data-readonly-i615.gateway-data-top-overlay-i617 .tak-context-head-i572{flex:0 0 auto!important}
      #${PANEL_ID}.gateway-data-readonly-i615.gateway-data-top-overlay-i617 #${BODY_ID}{flex:1 1 auto!important;min-height:0!important;max-height:none!important;overflow-y:auto!important;overflow-x:hidden!important;overscroll-behavior:contain!important;scrollbar-width:thin!important;scrollbar-color:#4f7181 #0b161c!important}
      #${PANEL_ID}.gateway-data-readonly-i615.gateway-data-top-overlay-i617 #${BODY_ID}::-webkit-scrollbar{width:12px!important}
      #${PANEL_ID}.gateway-data-readonly-i615.gateway-data-top-overlay-i617 #${BODY_ID}::-webkit-scrollbar-track{background:#0b161c!important;border-left:1px solid rgba(72,100,112,.25)!important}
      #${PANEL_ID}.gateway-data-readonly-i615.gateway-data-top-overlay-i617 #${BODY_ID}::-webkit-scrollbar-thumb{min-height:52px!important;border:3px solid #0b161c!important;border-radius:999px!important;background:linear-gradient(180deg,#5a7d8d,#446474)!important}
      #${PANEL_ID}.gateway-data-readonly-i615.gateway-data-top-overlay-i617 #${BODY_ID}::-webkit-scrollbar-thumb:hover{background:linear-gradient(180deg,#6f96a7,#5b8295)!important}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-context-i617>h3{display:none!important}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-context-i617 .kvp{grid-template-columns:112px minmax(0,1fr)!important;padding:8px 14px 14px!important}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-context-i617 .kvp b,#${PANEL_ID}.gateway-data-readonly-i615 .gateway-context-i617 .kvp span{box-sizing:border-box!important;max-width:100%!important;padding:8px 7px!important;font-size:11px!important;line-height:1.42!important;overflow-wrap:anywhere!important;word-break:normal!important;white-space:normal!important}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-context-i617 .kvp span{font-size:11.5px!important}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-areas-i617,#${PANEL_ID}.gateway-data-readonly-i615 .gateway-area-list-i617{min-width:0;max-width:100%;margin:0;padding:0}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-area-list-i617{display:grid;gap:6px;list-style:none}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-area-list-i617 li{position:relative;min-width:0;padding-left:14px;line-height:1.38;overflow-wrap:anywhere}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-area-list-i617 li::before{content:'';position:absolute;left:1px;top:.65em;width:5px;height:5px;border-radius:50%;background:#8bd8f3}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-areas-more-i617{margin-top:9px;border:0;background:transparent}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-areas-more-i617>summary{list-style:none;color:#9fe3fb;font-size:10.5px;font-weight:900;cursor:pointer}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-areas-more-i617>summary::-webkit-details-marker{display:none}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-areas-more-i617[open]>summary{margin-bottom:8px}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-areas-show-fewer-i617{display:none}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-areas-more-i617[open] .gateway-areas-show-all-i617{display:none}
      #${PANEL_ID}.gateway-data-readonly-i615 .gateway-areas-more-i617[open] .gateway-areas-show-fewer-i617{display:inline}
      @media(max-width:620px){#${PANEL_ID}.gateway-data-readonly-i615.gateway-data-top-overlay-i617{width:calc(100vw - 24px)!important;max-width:none!important}#${PANEL_ID}.gateway-data-readonly-i615 .gateway-context-i617 .kvp{grid-template-columns:96px minmax(0,1fr)!important}}

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
        host.dataset.takMapContextPositionI572 = 'relative';
      }
    } catch (_) {}
    const panel = document.createElement('aside');
    panel.id = PANEL_ID;
    panel.className = 'collapsed';
    panel.setAttribute('aria-hidden', 'true');
    panel.setAttribute('aria-label', 'Selected map object details');
    panel.innerHTML = `<div class="tak-context-head-i572"><div class="tak-context-head-copy-i572"><div class="tak-context-kicker-i572" id="takMapContextKickerI572">Object Details</div><div class="tak-context-title-i572" id="takMapContextTitleI572">Selected object</div></div><button type="button" class="tak-context-hide-i572" id="takMapContextHideI572" title="Hide details" aria-label="Hide details">›</button></div><div id="${BODY_ID}"></div>`;
    host.appendChild(panel);
    state.panelHost = host;
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
    panel.querySelector('#takMapContextHideI572').addEventListener('click', event => { event.preventDefault(); event.stopPropagation(); hide('button'); });
    state.body.addEventListener('click', handleBodyClick, true);
    state.body.addEventListener('toggle', handleGenericToggle, true);
    positionPanel();
    if (!state.windowResizeBound) {
      state.windowResizeBound = true;
      window.addEventListener('resize', positionPanel, {passive:true});
    }
    try {
      if (window.ResizeObserver) {
        state.resizeObserver = new ResizeObserver(positionPanel);
        state.resizeObserver.observe(host);
      }
    } catch (_) {}
    return panel;
  }

  function mountGatewayOverlay() {
    const panel = ensurePanel();
    if (!panel) return false;
    if (panel.parentNode !== document.body) document.body.appendChild(panel);
    panel.classList.add('tak-context-top-overlay-i618','gateway-data-top-overlay-i617');
    state.gatewayOverlayMounted = true;
    positionPanel();
    return true;
  }

  function restorePanelHost() {
    const panel = state.panel;
    const host = mapNode() || state.panelHost;
    if (!panel || !host) return false;
    if (panel.parentNode !== document.body) document.body.appendChild(panel);
    panel.classList.add('tak-context-top-overlay-i618');
    panel.classList.remove('gateway-data-top-overlay-i617');
    state.gatewayOverlayMounted = false;
    positionPanel();
    return true;
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
      panel.style.setProperty('--tak-context-bottom-i572', `${bottom}px`);
      const available = Math.max(220, hostRect.height - bottom - 12);
      panel.style.maxHeight = `${available}px`;
      if (state.gatewayOverlayMounted || panel.classList.contains('gateway-data-top-overlay-i617') || panel.classList.contains('tak-context-top-overlay-i618')) {
        panel.style.position = 'fixed';
        panel.style.right = `${Math.max(12, Math.ceil(window.innerWidth - hostRect.right + 14))}px`;
        panel.style.bottom = `${Math.max(12, Math.ceil(window.innerHeight - hostRect.bottom + bottom))}px`;
        panel.style.top = 'auto';
        panel.style.left = 'auto';
      }
      try { if (window.TakMapContextPanelSizingI618) window.TakMapContextPanelSizingI618.schedule(); } catch (_) {}
      const measured = panel.getBoundingClientRect();
      panel.classList.toggle('compact-height-i572', measured.height > available);
    } catch (error) { state.errors.push(`position:${error.message || error}`); }
  }

  function setHeader(kicker, title) {
    const k = document.getElementById('takMapContextKickerI572');
    const t = document.getElementById('takMapContextTitleI572');
    if (k) k.textContent = text(kicker) || 'Object Details';
    if (t) { const value=text(title); t.textContent=value; t.hidden=!value; }
  }

  function openPanel() {
    const panel = ensurePanel();
    if (!panel) return;
    panel.classList.remove('collapsed');
    panel.setAttribute('aria-hidden', 'false');
    positionPanel();
    requestAnimationFrame(positionPanel);
    try { if (window.TakMapContextPanelSizingI618) window.TakMapContextPanelSizingI618.schedule(); } catch (_) {}
  }

  function objectKey(object, source) {
    const registry = window.TakMapIconRegistryI572 || window.TakMapIconRegistryI556;
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
    const registry = window.TakMapIconRegistryI572 || window.TakMapIconRegistryI556;
    try {
      if (registry && registry.isPoint && registry.isPoint(object) && typeof registry.pointInfoHtml === 'function') {
        return registry.pointInfoHtml(object, registry.isLocalPoint && registry.isLocalPoint(object) ? 'local' : source);
      }
    } catch (_) {}
    try {
      if (typeof window.layerPopupForObject === 'function') return window.layerPopupForObject(object, kindOf(object));
    } catch (_) {}
    const captured = text(layer && layer.__takMapI572InfoHtml) || popupContent(layer);
    if (captured) return captured;
    const center = objectCenter(object, layer);
    return `<div class="feature-popup"><h3>${esc(objectName(object))}</h3><div class="kvp"><b>Category</b><span>${esc(kindOf(object))}</span>${center ? `<b>Coordinates</b><span>${esc(center[0].toFixed(6)+', '+center[1].toFixed(6))}</span>` : ''}<b>Source</b><span>${esc(source || object && object.source || 'TAK Map')}</span></div></div>`;
  }


  function selectedInfoSignature(object, source) {
    if (!object) return '';
    const fields = {
      key: objectKey(object, effectiveSource(object, source)), source: effectiveSource(object, source), kind: kindOf(object), name: objectName(object),
      uid: text(object.uid || object.cot_uid || object.event_uid || object.id), type: text(object.cot_type || object.type || object.event_type),
      mission: missionNames(object), category: text(object.category || object.kind || object.geometry || object.shape_kind_i636),
      coords: object.coords || object.points || object.coordinates || null, lat: object.lat, lon: object.lon,
      remarks: text(object.remarks || object.notes || object.description), added: text(object.added || object.created || object.time || object.timestamp || object.updated),
      style: [object.color, object.fill_color, object.opacity, object.fill_opacity, object.weight, object.line_style],
      major: object.major_m_i636, minor: object.minor_m_i636, angle: object.angle_deg_i636, closed: object.shape_closed_i636,
      deleteSupported: object.delete_supported, deleteReason: object.delete_unavailable_reason,
    };
    try { return JSON.stringify(fields); } catch (_) { return String(fields.key || ''); }
  }

  function flattenCoords(value, out) {
    out = out || [];
    if (!value) return out;
    if (Array.isArray(value)) {
      if (value.length >= 2 && finite(value[0]) && finite(value[1]) && !Array.isArray(value[0])) {
        let a=Number(value[0]), b=Number(value[1]);
        if (Math.abs(a) > 90 && Math.abs(b) <= 90) out.push([b,a]); else out.push([a,b]);
      } else for (const child of value) flattenCoords(child,out);
      return out;
    }
    if (finite(value.lat) && finite(value.lng != null ? value.lng : value.lon)) out.push([Number(value.lat),Number(value.lng != null ? value.lng : value.lon)]);
    return out;
  }

  function geometryPoints(object, layer) {
    let points=[];
    try { points=flattenCoords(object && (object.coords || object.points || object.coordinates || object.geometry && object.geometry.coordinates),[]); } catch (_) {}
    if (points.length) return points;
    try { if (layer && typeof layer.getLatLngs === 'function') points=flattenCoords(layer.getLatLngs(),[]); } catch (_) {}
    return points;
  }

  function haversineMeters(a,b) {
    const R=6371008.8, rad=Math.PI/180;
    const lat1=a[0]*rad,lat2=b[0]*rad,dlat=(b[0]-a[0])*rad,dlon=(b[1]-a[1])*rad;
    const h=Math.sin(dlat/2)**2+Math.cos(lat1)*Math.cos(lat2)*Math.sin(dlon/2)**2;
    return 2*R*Math.asin(Math.min(1,Math.sqrt(h)));
  }

  function polygonAreaMeters(points) {
    if (!points || points.length < 3) return 0;
    const R=6371008.8, rad=Math.PI/180;
    const lat0=points.reduce((a,p)=>a+p[0],0)/points.length*rad;
    const lon0=points.reduce((a,p)=>a+p[1],0)/points.length;
    const xy=points.map(p=>[R*(p[1]-lon0)*rad*Math.cos(lat0),R*p[0]*rad]);
    let sum=0; for(let i=0;i<xy.length;i++){const a=xy[i],b=xy[(i+1)%xy.length];sum+=a[0]*b[1]-b[0]*a[1];}
    return Math.abs(sum)/2;
  }

  function perimeterMeters(points,closed) {
    if (!points || points.length < 2) return 0;
    let total=0; for(let i=1;i<points.length;i++) total+=haversineMeters(points[i-1],points[i]);
    if (closed && points.length>2) total+=haversineMeters(points[points.length-1],points[0]);
    return total;
  }

  function bearingDegrees(a,b) {
    const rad=Math.PI/180,deg=180/Math.PI,lat1=a[0]*rad,lat2=b[0]*rad,dlon=(b[1]-a[1])*rad;
    let v=Math.atan2(Math.sin(dlon)*Math.cos(lat2),Math.cos(lat1)*Math.sin(lat2)-Math.sin(lat1)*Math.cos(lat2)*Math.cos(dlon))*deg;
    v=(v+360)%360; return v>=180?v-180:v;
  }

  function measurementSystem() {
    try {
      const loc=new Intl.Locale((navigator.languages&&navigator.languages[0])||navigator.language||'en-US');
      let system='';
      try { if (typeof loc.getMeasurementSystem === 'function') system=text(loc.getMeasurementSystem()); } catch (_) {}
      try { if (!system && loc.measurementSystem) system=text(loc.measurementSystem); } catch (_) {}
      if (/us|imperial/i.test(system)) return 'us';
      if (/metric/i.test(system)) return 'metric';
      const region=text(loc.region).toUpperCase();
      return ['US','LR','MM'].includes(region)?'us':'metric';
    } catch (_) { return /^en-US\b/i.test(navigator.language||'')?'us':'metric'; }
  }

  function numberFmt(value, digits) {
    try { return new Intl.NumberFormat(undefined,{maximumFractionDigits:digits,minimumFractionDigits:0}).format(value); } catch (_) { return Number(value).toFixed(digits); }
  }

  function formatDistanceMeters(meters) {
    if (!finite(meters) || Number(meters)<=0) return '';
    meters=Number(meters); if (measurementSystem()==='us') { const feet=meters*3.280839895; return feet>=5280?`${numberFmt(feet/5280,2)} mi`:`${numberFmt(feet,feet<100?1:0)} ft`; }
    return meters>=1000?`${numberFmt(meters/1000,2)} km`:`${numberFmt(meters,meters<100?1:0)} m`;
  }

  function formatAreaMeters(area) {
    if (!finite(area) || Number(area)<=0) return '';
    area=Number(area); if (measurementSystem()==='us') { const sqft=area*10.763910417, acres=area/4046.8564224, sqmi=area/2589988.110336; if (sqmi>=1) return `${numberFmt(sqft,0)} sq ft · ${numberFmt(sqmi,2)} sq mi`; if (acres>=0.1) return `${numberFmt(sqft,0)} sq ft · ${numberFmt(acres,2)} ac`; return `${numberFmt(sqft,0)} sq ft`; }
    const ha=area/10000, sqkm=area/1e6; if (sqkm>=1) return `${numberFmt(area,0)} m² · ${numberFmt(sqkm,2)} km²`; if (ha>=0.1) return `${numberFmt(area,0)} m² · ${numberFmt(ha,2)} ha`; return `${numberFmt(area,0)} m²`;
  }

  function geometryRows(object, layer) {
    const kind=kindOf(object), shape=text(object && (object.shape_kind_i636 || object.category || object.geometry || object.kind)).toLowerCase();
    const cot=text(object && (object.cot_type || object.type)).toLowerCase();
    const points=geometryPoints(object,layer); const rows=[];
    const push=(label,value)=>{ if(text(value)) rows.push([label,text(value)]); };
    if (kind==='Route') { push('Length',formatDistanceMeters(perimeterMeters(points,false))); return rows; }
    if (kind!=='Shape') return rows;
    const isCircle=/circle/.test(shape)||cot==='u-d-c-c'||cot==='u-r-b-c-c';
    const isEllipse=/ellipse/.test(shape)||cot==='u-d-c-e';
    const isRectangle=/rect|square/.test(shape)||cot==='u-d-r';
    const closed=object && typeof object.shape_closed_i636==='boolean'?!!object.shape_closed_i636:!(/freehand|line/.test(shape)&&cot!=='u-d-p');
    const major=Number(object && object.major_m_i636),minor=Number(object && object.minor_m_i636),angle=Number(object && object.angle_deg_i636);
    if (isCircle && Number.isFinite(major) && major>0) {
      push('Area',formatAreaMeters(Math.PI*major*major)); push('Circumference',formatDistanceMeters(2*Math.PI*major)); return rows;
    }
    if (isEllipse && Number.isFinite(major) && major>0 && Number.isFinite(minor) && minor>0) {
      const a=major,b=minor,h=((a-b)*(a-b))/((a+b)*(a+b)); const peri=Math.PI*(a+b)*(1+3*h/(10+Math.sqrt(4-3*h)));
      push('Area',formatAreaMeters(Math.PI*a*b)); push('Perimeter',formatDistanceMeters(peri)); return rows;
    }
    if (isRectangle && points.length>=4) {
      push('Area',formatAreaMeters(polygonAreaMeters(points))); push('Perimeter',formatDistanceMeters(perimeterMeters(points,true))); return rows;
    }
    if (points.length>=2) {
      if (closed && points.length>=3) { push('Area',formatAreaMeters(polygonAreaMeters(points))); push('Perimeter',formatDistanceMeters(perimeterMeters(points,true))); }
      else push('Length',formatDistanceMeters(perimeterMeters(points,false)));
    }
    return rows;
  }

  function applySourcePresentation() {
    if (!state.body || !state.selected) return;
    const popup=state.body.querySelector('.tak-v322-popup'); if (!popup) return;
    const label=sourceLabel(state.selected.object,state.selected.source), kind=kindOf(state.selected.object);
    const sub=popup.querySelector('.tak-v322-sub'); if (sub) sub.textContent=`${kind} · ${label}`;
    popup.dataset.source=label.startsWith('Data Sync')?'Data Sync':'Local Data';
    popup.querySelectorAll('[data-popup-source]').forEach(node=>node.setAttribute('data-popup-source',label.startsWith('Data Sync')?'Data Sync':'Local Data'));
  }

  function applyGeometryPresentation() {
    if (!state.body || !state.selected) return;
    const table=state.body.querySelector('.tak-v322-table'); if (!table) return;
    table.querySelectorAll('.tak-geometry-i638,.tak-geometry-i639').forEach(node=>node.remove());
    const oldRows=Array.from(table.querySelectorAll('.tak-v322-row')).filter(row=>/^(area|distance|length|width|height|perimeter|radius|diameter|circumference|major axis|minor axis|rotation)$/i.test(text(row.querySelector('b')&&row.querySelector('b').textContent)));
    oldRows.forEach(row=>row.remove());
    const rows=geometryRows(activeShapeObjectI640(),state.shapeEdit.active?null:state.selected.layer); if (!rows.length) return;
    const anchor=Array.from(table.querySelectorAll('.tak-v322-row')).find(row=>/^added$/i.test(text(row.querySelector('b')&&row.querySelector('b').textContent))) || null;
    for (const [label,value] of rows) { const row=document.createElement('div'); row.className='tak-v322-row tak-geometry-i639'; row.innerHTML=`<b>${esc(label)}</b><span>${esc(value)}</span>`; if(anchor)table.insertBefore(row,anchor);else table.appendChild(row); }
  }

  function applyShapeFieldLabels() {
    if (!state.body || !state.selected || kindOf(state.selected.object)!=='Shape') return;
    const table=state.body.querySelector('.tak-v322-table'); if(!table)return;
    let notesRow=null;
    for(const row of Array.from(table.querySelectorAll('.tak-v322-row'))){
      const label=row.querySelector('b'); if(!label)continue;
      const name=text(label.textContent);
      if(/^(lat\/lon|coordinates)$/i.test(name)) label.textContent='Center';
      if(/^(category|rotation)$/i.test(name)) { row.remove(); continue; }
      if(/^notes$/i.test(name)) notesRow=row;
    }
    if(notesRow&&notesRow.parentNode===table)table.appendChild(notesRow);
  }

  function shapeKindI639(object){
    const cot=text(object&&(object.cot_type||object.type)).toLowerCase();
    const kind=text(object&&(object.shape_kind_i636||object.shape_type||object.category||object.geometry)).toLowerCase();
    if(cot==='u-d-r'||/rect|square/.test(kind))return 'rectangle';
    if(cot==='u-d-c-c'||cot==='u-r-b-c-c'||/circle/.test(kind))return 'circle';
    if(cot==='u-d-c-e'||/ellipse/.test(kind))return 'ellipse';
    if(cot==='u-d-f'||cot==='u-d-f-m'||/freehand|telestrat|line/.test(kind))return 'freeform';
    return 'polygon';
  }
  function cloneI639(value){try{return JSON.parse(JSON.stringify(value))}catch(_){return value}}
  function normalizePointI639(p){if(Array.isArray(p)&&finite(p[0])&&finite(p[1]))return [Number(p[0]),Number(p[1])];if(p&&finite(p.lat)&&finite(p.lng!=null?p.lng:p.lon))return [Number(p.lat),Number(p.lng!=null?p.lng:p.lon)];return null}
  function shapePointsFromI640(object,layer){
    let pts=[];try{pts=flattenCoords(object&&(object.coords||object.points||object.coordinates||object.geometry&&object.geometry.coordinates),[])}catch(_){}
    if(!pts.length&&layer)try{if(typeof layer.getLatLngs==='function')pts=flattenCoords(layer.getLatLngs(),[])}catch(_){}
    return pts.map(normalizePointI639).filter(Boolean);
  }
  function activeShapeObjectI640(){return state.shapeEdit.active&&state.shapeEdit.draft?state.shapeEdit.draft:(state.selected&&state.selected.object)}
  function currentShapePointsI639(){const o=activeShapeObjectI640();return shapePointsFromI640(o,state.shapeEdit.active?null:(state.selected&&state.selected.layer))}
  function shapeCenterI639(object){
    const o=(state.shapeEdit.active&&state.shapeEdit.draft&&(object===state.selected?.object||object===state.shapeEdit.draft))?state.shapeEdit.draft:object;
    const k=shapeKindI639(o); if((k==='circle'||k==='ellipse')&&finite(o&&o.lat)&&finite(o&&o.lon))return [Number(o.lat),Number(o.lon)];
    const pts=shapePointsFromI640(o,null); if(!pts.length)return objectCenter(o,state.shapeEdit.active?null:(state.selected&&state.selected.layer));
    if((k==='rectangle'||k==='polygon')&&pts.length>=3){
      const origin=[pts.reduce((a,p)=>a+p[0],0)/pts.length,pts.reduce((a,p)=>a+p[1],0)/pts.length],xy=pts.map(p=>xyFromI639(origin,p));let twice=0,cx=0,cy=0;
      for(let i=0;i<xy.length;i++){const a=xy[i],b=xy[(i+1)%xy.length],cross=a[0]*b[1]-b[0]*a[1];twice+=cross;cx+=(a[0]+b[0])*cross;cy+=(a[1]+b[1])*cross;}
      if(Math.abs(twice)>1e-6)return llFromI639(origin,[cx/(3*twice),cy/(3*twice)]);
    }
    return [pts.reduce((a,p)=>a+p[0],0)/pts.length,pts.reduce((a,p)=>a+p[1],0)/pts.length];
  }
  function xyFromI639(origin,p){const R=6378137,rad=Math.PI/180,cos=Math.max(1e-6,Math.cos(origin[0]*rad));return [(p[1]-origin[1])*rad*R*cos,(p[0]-origin[0])*rad*R]}
  function llFromI639(origin,xy){const R=6378137,rad=Math.PI/180,cos=Math.max(1e-6,Math.cos(origin[0]*rad));return [origin[0]+xy[1]/R/rad,origin[1]+xy[0]/(R*cos)/rad]}
  function norm2I639(v){const n=Math.hypot(v[0],v[1]);return n>1e-9?[v[0]/n,v[1]/n]:[1,0]}
  function midpointI639(a,b){return [(a[0]+b[0])/2,(a[1]+b[1])/2]}
  function bearing360I639(a,b){const rad=Math.PI/180,deg=180/Math.PI,lat1=a[0]*rad,lat2=b[0]*rad,dlon=(b[1]-a[1])*rad;return (Math.atan2(Math.sin(dlon)*Math.cos(lat2),Math.cos(lat1)*Math.sin(lat2)-Math.sin(lat1)*Math.cos(lat2)*Math.cos(dlon))*deg+360)%360}
  function destinationI639(center,bearing,distance){const R=6371008.8,rad=Math.PI/180,br=Number(bearing)*rad,lat1=center[0]*rad,lon1=center[1]*rad,dr=Number(distance)/R;const lat2=Math.asin(Math.sin(lat1)*Math.cos(dr)+Math.cos(lat1)*Math.sin(dr)*Math.cos(br));const lon2=lon1+Math.atan2(Math.sin(br)*Math.sin(dr)*Math.cos(lat1),Math.cos(dr)-Math.sin(lat1)*Math.sin(lat2));return [lat2/rad,((lon2/rad+540)%360)-180]}
  function ellipseCoordsI639(center,major,minor,angle,count){
    count=count||72;const out=[],a=(Number(angle)||0)*Math.PI/180;const ux=[Math.sin(a),Math.cos(a)],uy=[Math.sin(a+Math.PI/2),Math.cos(a+Math.PI/2)];
    for(let i=0;i<count;i++){const t=2*Math.PI*i/count,x=Number(major)*Math.cos(t),y=Number(minor)*Math.sin(t);out.push(llFromI639(center,[ux[0]*x+uy[0]*y,ux[1]*x+uy[1]*y]));}return out;
  }
  function makeShapeDraftI640(object){
    const o=object||{},coords=shapePointsFromI640(o,state.selected&&state.selected.layer);
    return {coords:cloneI639(coords),lat:o.lat,lon:o.lon,major_m_i636:o.major_m_i636,minor_m_i636:o.minor_m_i636,angle_deg_i636:o.angle_deg_i636,name:o.name,callsign:o.callsign,notes:o.notes,remarks:o.remarks,shape_kind_i636:o.shape_kind_i636,shape_type:o.shape_type,shape_closed_i636:o.shape_closed_i636,category:o.category,geometry:o.geometry,kind:o.kind,cot_type:o.cot_type,type:o.type,uid:o.uid,cot_uid:o.cot_uid,event_uid:o.event_uid,id:o.id,is_mission_object:o.is_mission_object,mission_memberships:cloneI639(o.mission_memberships||[]),mission_names:cloneI639(o.mission_names||[]),mission_name:o.mission_name,mission:o.mission,raw_cot_i636:o.raw_cot_i636};
  }
  function snapshotShapeI639(){const o=state.selected&&state.selected.object;if(!o)return null;return makeShapeDraftI640(o)}
  function markShapeDirtyI640(){if(!state.shapeEdit.active)return;state.shapeEdit.dirty=true;state.shapeEdit.revision=Number(state.shapeEdit.revision||0)+1}
  function applyGeometryObjectI640(target,source){if(!target||!source)return;target.coords=cloneI639(source.coords||[]);target.lat=source.lat;target.lon=source.lon;target.major_m_i636=source.major_m_i636;target.minor_m_i636=source.minor_m_i636;target.angle_deg_i636=source.angle_deg_i636;}
  function applyDraftToLayerI640(layer){
    if(!layer||!state.shapeEdit.active||!state.shapeEdit.draft)return;const pts=currentShapePointsI639();
    try{if(typeof layer.setLatLngs==='function')layer.setLatLngs(pts)}catch(error){state.errors.push(`shape-layer:${error.message||error}`)}
    try{if(typeof layer.redraw==='function')layer.redraw()}catch(_){}
  }
  function activeShapeLayersI640(){const out=[],add=x=>{if(x&&!out.includes(x))out.push(x)};if(state.selected){add(state.selected.layer);add(state.selected.object&&state.selected.object.__layer);add(state.selected.object&&state.selected.object.__hitLayer)}const d=state.shapeEdit.deferredObject;add(d&&d.__layer);add(d&&d.__hitLayer);return out}
  function updateLayerGeometryI639(){
    if(!state.selected)return;for(const layer of activeShapeLayersI640())applyDraftToLayerI640(layer);state.selected.center=shapeCenterI639(activeShapeObjectI640());
  }
  function setShapePointsI639(points){const o=state.shapeEdit.active&&state.shapeEdit.draft?state.shapeEdit.draft:(state.selected&&state.selected.object);if(!o)return;o.coords=points.map(p=>[Number(p[0]),Number(p[1])]);const pts=shapePointsFromI640(o,null);if(pts.length){o.lat=pts.reduce((a,p)=>a+p[0],0)/pts.length;o.lon=pts.reduce((a,p)=>a+p[1],0)/pts.length;}markShapeDirtyI640();updateLayerGeometryI639()}
  function setEllipseGeometryI639(center,major,minor,angle){const o=state.shapeEdit.active&&state.shapeEdit.draft?state.shapeEdit.draft:(state.selected&&state.selected.object);if(!o)return;o.lat=center[0];o.lon=center[1];o.major_m_i636=Math.max(.01,Number(major)||.01);o.minor_m_i636=Math.max(.01,Number(minor)||.01);o.angle_deg_i636=((Number(angle)||0)%360+360)%360;o.coords=ellipseCoordsI639(center,o.major_m_i636,o.minor_m_i636,o.angle_deg_i636,72);markShapeDirtyI640();updateLayerGeometryI639()}
  function restoreShapeI639(){const snap=state.shapeEdit.snapshot,o=state.shapeEdit.baseObject||state.selected&&state.selected.object;if(!snap||!o)return;applyGeometryObjectI640(o,snap);o.name=snap.name;o.callsign=snap.callsign;o.notes=snap.notes;o.remarks=snap.remarks;const draft=state.shapeEdit.draft;state.shapeEdit.draft=snap;updateLayerGeometryI639();state.shapeEdit.draft=draft}
  function clearMapEditorsI639(){
    for(const marker of [...(state.shapeEdit.handles||[]),...(state.shapeEdit.labels||[])]){try{marker.remove()}catch(_){try{const m=mapInstance();if(m)m.removeLayer(marker)}catch(__){}}}
    state.shapeEdit.handles=[];state.shapeEdit.labels=[];
  }
  function vectorIconI639(role){return window.L&&L.divIcon?L.divIcon({className:'tak-shape-vector-wrap-i639',html:`<span class="tak-shape-vector-i639 ${esc(role||'vertex')}"></span>`,iconSize:[16,16],iconAnchor:[8,8]}):null}
  function addHandleI639(latlng,role,onDrag){const m=mapInstance();if(!m||!window.L||!L.marker)return null;const marker=L.marker(latlng,{draggable:true,keyboard:false,bubblingMouseEvents:false,zIndexOffset:12000,icon:vectorIconI639(role)}).addTo(m);marker.on('drag',ev=>{try{onDrag([ev.target.getLatLng().lat,ev.target.getLatLng().lng],ev.target);syncHandlesToDraftI640();syncShapeEditUiI639()}catch(error){state.errors.push(`shape-drag:${error.message||error}`)}});marker.on('dragend',()=>{syncHandlesToDraftI640();syncShapeEditUiI639()});marker.on('click',ev=>{try{if(ev.originalEvent&&window.L&&L.DomEvent)L.DomEvent.stop(ev.originalEvent)}catch(_){}});state.shapeEdit.handles.push(marker);return marker}
  function rectangleDragI639(index,newPoint){const pts=currentShapePointsI639();if(pts.length<4)return;const i=index%4,o=(i+2)%4,a=(i+1)%4,b=(i+3)%4,origin=pts[o];const av=xyFromI639(origin,pts[a]),bv=xyFromI639(origin,pts[b]),dv=xyFromI639(origin,newPoint),u=norm2I639(av),v=norm2I639(bv);const du=dv[0]*u[0]+dv[1]*u[1],dv2=dv[0]*v[0]+dv[1]*v[1];pts[a]=llFromI639(origin,[u[0]*du,u[1]*du]);pts[b]=llFromI639(origin,[v[0]*dv2,v[1]*dv2]);pts[i]=llFromI639(origin,[u[0]*du+v[0]*dv2,u[1]*du+v[1]*dv2]);setShapePointsI639(pts)}
  function polygonDragI639(index,newPoint){const pts=currentShapePointsI639();if(index<0||index>=pts.length)return;pts[index]=newPoint;setShapePointsI639(pts)}
  function translateToCenterI639(center){
    const o=activeShapeObjectI640();if(!o)return;const old=shapeCenterI639(o);if(!old)return;const kind=shapeKindI639(o);
    if(kind==='circle'||kind==='ellipse')setEllipseGeometryI639(center,Number(o.major_m_i636)||1,Number(o.minor_m_i636)||Number(o.major_m_i636)||1,Number(o.angle_deg_i636)||0);
    else{const delta=xyFromI639(old,center),pts=currentShapePointsI639().map(p=>{const xy=xyFromI639(old,p);return llFromI639(old,[xy[0]+delta[0],xy[1]+delta[1]])});setShapePointsI639(pts)}
    syncHandlesToDraftI640();
  }
  function syncHandlesToDraftI640(){
    if(!state.shapeEdit.active)return;const o=activeShapeObjectI640(),kind=shapeKindI639(o),hs=state.shapeEdit.handles||[],pts=currentShapePointsI639(),c=shapeCenterI639(o);
    try{
      if(!c||!hs.length)return;if(hs[0])hs[0].setLatLng(c);
      if(kind==='rectangle'||kind==='polygon'||kind==='freeform'){pts.forEach((p,i)=>{const h=hs[i+1];if(h)h.setLatLng(p)});return}
      const major=Number(o.major_m_i636)||1,minor=Number(o.minor_m_i636)||major,angle=Number(o.angle_deg_i636)||0;if(hs[1])hs[1].setLatLng(destinationI639(c,angle,major));if(kind==='ellipse'&&hs[2])hs[2].setLatLng(destinationI639(c,angle+90,minor));
    }catch(error){state.errors.push(`shape-handle-sync:${error.message||error}`)}
  }
  function rebuildHandlesI639(){
    clearMapEditorsI639();if(!state.shapeEdit.active||!state.selected)return;const o=activeShapeObjectI640(),kind=shapeKindI639(o),pts=currentShapePointsI639(),center=shapeCenterI639(o);if(!center)return;
    addHandleI639(center,'center',np=>translateToCenterI639(np));
    if(kind==='rectangle'&&pts.length>=4){pts.slice(0,4).forEach((p,i)=>addHandleI639(p,'vertex',np=>rectangleDragI639(i,np)))}
    else if(kind==='polygon'||kind==='freeform'){pts.forEach((p,i)=>addHandleI639(p,'vertex',np=>polygonDragI639(i,np)))}
    else if(kind==='circle'||kind==='ellipse'){
      let major=Number(o.major_m_i636),minor=Number(o.minor_m_i636),angle=Number(o.angle_deg_i636)||0;if(!Number.isFinite(major)||major<=0)major=pts.length?haversineMeters(center,pts[0]):10;if(!Number.isFinite(minor)||minor<=0)minor=major;
      addHandleI639(destinationI639(center,angle,major),'major',np=>{const c=shapeCenterI639(o),r=haversineMeters(c,np),br=bearing360I639(c,np);setEllipseGeometryI639(c,r,kind==='circle'?r:(Number(o.minor_m_i636)||minor),br)});
      if(kind==='ellipse')addHandleI639(destinationI639(center,angle+90,minor),'minor',np=>{const c=shapeCenterI639(o),r=haversineMeters(c,np);setEllipseGeometryI639(c,Number(o.major_m_i636)||major,r,Number(o.angle_deg_i636)||angle)});
    }
    syncHandlesToDraftI640();refreshDistanceLabelsI639();
  }
  function labelMarkerI639(mid,label){const m=mapInstance();if(!m||!window.L||!L.marker||!L.divIcon)return null;const marker=L.marker(mid,{interactive:false,keyboard:false,bubblingMouseEvents:false,zIndexOffset:11500,icon:L.divIcon({className:'tak-shape-distance-wrap-i639',html:`<span class="tak-shape-distance-i639">${esc(label)}</span>`,iconSize:null,iconAnchor:[0,0]})}).addTo(m);state.shapeEdit.labels.push(marker);return marker}
  function refreshDistanceLabelsI639(){
    for(const marker of state.shapeEdit.labels||[])try{marker.remove()}catch(_){}state.shapeEdit.labels=[];if(!state.shapeEdit.active||!state.selected)return;const m=mapInstance();if(!m||typeof m.latLngToContainerPoint!=='function')return;const o=activeShapeObjectI640(),kind=shapeKindI639(o),segments=[];
    if(kind==='circle'||kind==='ellipse'){const hs=state.shapeEdit.handles||[],center=hs[0]&&hs[0].getLatLng&&hs[0].getLatLng();if(center)for(let i=1;i<hs.length;i++){const ll=hs[i].getLatLng();segments.push([[center.lat,center.lng],[ll.lat,ll.lng]])}}
    else{const pts=currentShapePointsI639(),closed=kind==='rectangle'||(o&&o.shape_closed_i636!==false&&kind!=='freeform');for(let i=1;i<pts.length;i++)segments.push([pts[i-1],pts[i]]);if(closed&&pts.length>2)segments.push([pts[pts.length-1],pts[0]])}
    const occupied=[];for(const seg of segments){const dist=haversineMeters(seg[0],seg[1]),label=formatDistanceMeters(dist);if(!label)continue;let a,b;try{a=m.latLngToContainerPoint(seg[0]);b=m.latLngToContainerPoint(seg[1])}catch(_){continue}const px=Math.hypot(b.x-a.x,b.y-a.y),need=Math.max(76,label.length*7+22);if(px<need)continue;const midPx={x:(a.x+b.x)/2,y:(a.y+b.y)/2},box={l:midPx.x-need/2,r:midPx.x+need/2,t:midPx.y-13,b:midPx.y+13};if(occupied.some(q=>!(box.r<q.l||box.l>q.r||box.b<q.t||box.t>q.b)))continue;occupied.push(box);labelMarkerI639(midpointI639(seg[0],seg[1]),label)}
  }
  function findRowI639(label){if(!state.body)return null;return Array.from(state.body.querySelectorAll('.tak-v322-row')).find(row=>new RegExp(`^${label}$`,'i').test(text(row.querySelector('b')&&row.querySelector('b').textContent)))||null}
  function updateCenterEditorI639(){const input=state.body&&state.body.querySelector('.tak-shape-center-input-i639'),c=state.selected&&shapeCenterI639(activeShapeObjectI640());if(input&&c)input.value=`${c[0].toFixed(6)}, ${c[1].toFixed(6)}`;const details=state.body&&state.body.querySelector('details.popup-edit');if(details&&c){const la=details.querySelector('[name="lat"]'),lo=details.querySelector('[name="lon"]');if(la)la.value=c[0].toFixed(6);if(lo)lo.value=c[1].toFixed(6)}}
  function syncShapeEditUiI639(){if(!state.shapeEdit.active)return;updateCenterEditorI639();applyGeometryPresentation();syncHandlesToDraftI640();refreshDistanceLabelsI639()}
  function parseCenterI639(value){const m=text(value).match(/^\s*([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\s*$/);if(!m)return null;const lat=Number(m[1]),lon=Number(m[2]);return Number.isFinite(lat)&&Number.isFinite(lon)&&lat>=-90&&lat<=90&&lon>=-180&&lon<=180?[lat,lon]:null}
  function shapePayloadI639(name,notes){const o=activeShapeObjectI640(),c=shapeCenterI639(o);return {kind:shapeKindI639(o),cot_type:text(o.cot_type||o.type),uid:text(o.uid||o.cot_uid||o.event_uid||o.id),is_mission_object:!!o.is_mission_object,mission_names:missionNames(o),coords:currentShapePointsI639(),center:c,closed:o.shape_closed_i636!==false,major_m:Number(o.major_m_i636),minor_m:Number(o.minor_m_i636),angle_deg:Number(o.angle_deg_i636)||0,raw_cot_i636:text(o.raw_cot_i636),name:text(name),notes:text(notes)}}
  function shapeUidI641(object){return text(object&&(object.uid||object.cot_uid||object.event_uid||object.id)).trim().toLowerCase()}
  function geometryOfI641(object){if(!object)return null;const kind=shapeKindI639(object),center=shapeCenterI639(object);return {kind,cot_type:text(object.cot_type||object.type).toLowerCase(),uid:shapeUidI641(object),coords:shapePointsFromI640(object,null),center,major_m:Number(object.major_m_i636!=null?object.major_m_i636:object.major_m),minor_m:Number(object.minor_m_i636!=null?object.minor_m_i636:object.minor_m),angle_deg:Number(object.angle_deg_i636!=null?object.angle_deg_i636:object.angle_deg)||0}}
  function geometryMatchesI641(candidate,target){
    if(!candidate||!target)return false;const a=candidate.kind?candidate:geometryOfI641(candidate),b=target.kind?target:geometryOfI641(target);if(!a||!b)return false;
    if(text(a.kind).toLowerCase()!==text(b.kind).toLowerCase())return false;if(b.uid&&a.uid&&text(a.uid).toLowerCase()!==text(b.uid).toLowerCase())return false;
    const close=(x,y,t)=>Number.isFinite(Number(x))&&Number.isFinite(Number(y))&&Math.abs(Number(x)-Number(y))<=t;
    if((b.kind==='circle'||b.kind==='ellipse')){if(!a.center||!b.center||!close(a.center[0],b.center[0],2e-6)||!close(a.center[1],b.center[1],2e-6))return false;if(!close(a.major_m,b.major_m,.25))return false;if(b.kind==='ellipse'&&!close(a.minor_m,b.minor_m,.25))return false;return true;}
    const ac=(a.coords||[]),bc=(b.coords||[]);if(ac.length!==bc.length||!ac.length)return false;const same=(p,q)=>close(p&&p[0],q&&q[0],2e-6)&&close(p&&p[1],q&&q[1],2e-6);for(let shift=0;shift<bc.length;shift++){let f=true,r=true;for(let i=0;i<ac.length;i++){if(!same(ac[i],bc[(i+shift)%bc.length]))f=false;if(!same(ac[i],bc[(shift-i+bc.length*4)%bc.length]))r=false}if(f||r)return true}return false;
  }
  function payloadGeometryI641(payload){if(!payload||typeof payload!=='object')return null;const out={kind:text(payload.kind).toLowerCase(),cot_type:text(payload.cot_type).toLowerCase(),uid:text(payload.uid).toLowerCase(),coords:(payload.coords||[]).map(normalizePointI639).filter(Boolean),center:normalizePointI639(payload.center),major_m:Number(payload.major_m),minor_m:Number(payload.minor_m),angle_deg:Number(payload.angle_deg)||0};return out}
  function findReadbackObjectI641(data,target){const rows=data&&Array.isArray(data.objects)?data.objects:[],uid=text(target&&target.uid).toLowerCase();if(uid){const hit=rows.find(o=>shapeUidI641(o)===uid);if(hit)return hit}return rows.find(o=>{try{return objectKey(o,effectiveSource(o,'datasync'))===state.shapeEdit.draftKey}catch(_){return false}})||null}
  function sleepI641(ms){return new Promise(resolve=>setTimeout(resolve,ms))}
  async function confirmSavedDraftI641(target,result,source,status){
    const echoed=payloadGeometryI641(result&&result.shape_geometry_i639);if(!echoed||!geometryMatchesI641(echoed,target))throw new Error('Saved geometry response did not match the visible edit draft.');
    const persisted=!!(result&&result.shape_edit_i639&&result.shape_edit_i639.persisted_overlay);const mission=!!(target&&target.is_mission_object)||String(source||'').toLowerCase()==='datasync';
    if(!mission){if(!persisted)throw new Error('Local Shape persistence was not confirmed.');return {method:'persistent-overlay',object:null};}
    const tx=result&&(result.shape_edit_i643||result.shape_edit_i642);if(!tx||!tx.authoritative_mission_readback_confirmed){const stage=text(tx&&tx.stage),failed=text(tx&&tx.failed_mission);throw new Error('Saved Shape was not authoritatively confirmed as native TAK geometry'+(failed?` for ${failed}`:'')+(stage?` (${stage})`:'.'));}
    if(result&&result.shape_edit_i643&&!result.shape_edit_i643.authoritative_global_readback_confirmed)throw new Error('Saved native Shape was not confirmed by global TAK CoT geometry read-back.');
    if(status)status.textContent='Saved · Native TAK Shape verified';return {method:'native-shape-global-mission-readback-i643',object:null};
  }
  function commitDraftI640(result,name,notes,confirmedObject){
    const draft=state.shapeEdit.draft,base=state.shapeEdit.baseObject||state.selected&&state.selected.object;if(!draft||!base)return;const targets=[base,state.shapeEdit.deferredObject,confirmedObject].filter(Boolean);for(const o of targets){applyGeometryObjectI640(o,draft);o.name=name;o.callsign=name;o.notes=notes;o.remarks=notes;if(result&&result.shape_geometry_i639&&result.shape_geometry_i639.raw_cot_i636)o.raw_cot_i636=result.shape_geometry_i639.raw_cot_i636}
    if(result&&result.shape_geometry_i639)draft.raw_cot_i636=result.shape_geometry_i639.raw_cot_i636||draft.raw_cot_i636;const chosen=(confirmedObject&&confirmedObject.__layer)?confirmedObject:((state.shapeEdit.deferredObject&&state.shapeEdit.deferredObject.__layer)?state.shapeEdit.deferredObject:base);state.selected.object=chosen;state.selected.layer=chosen.__layer||chosen.__hitLayer||state.selected.layer;state.selected.center=shapeCenterI639(draft);
  }
  async function saveShapeEditI639(event){
    if(event){event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation()}if(state.shapeEdit.saveBusy||!state.shapeEdit.active||!state.selected)return;const details=state.body.querySelector('details.popup-edit'),save=details&&details.querySelector('[data-i640-shape-save]'),cancel=details&&details.querySelector('[data-i640-shape-cancel]'),nameInput=state.body.querySelector('.tak-shape-name-input-i639'),notesInput=state.body.querySelector('.tak-shape-notes-input-i639'),status=details&&details.querySelector('.popup-edit-status');const name=text(nameInput&&nameInput.value)||objectName(state.shapeEdit.baseObject||state.selected.object),notes=text(notesInput&&notesInput.value);const key=state.shapeEdit.draftKey||text(details&&details.dataset.key)||objectKey(state.selected.object,state.selected.source),source=text(details&&details.dataset.source)||state.selected.source;
    state.shapeEdit.saveBusy=true;state.shapeEdit.lastSaveError='';state.shapeEdit.lastSaveConfirmation='';if(save)save.disabled=true;if(cancel)cancel.disabled=true;if(status)status.textContent='Saving…';
    try{
      const target=shapePayloadI639(name,notes);const targetGeometry=payloadGeometryI641(target);const payload={key,source,name,notes,lat:target.center&&target.center[0],lon:target.center&&target.center[1],shape_geometry_i639:target};const response=await fetch('/api/tak-map/popup-edit',{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});let result={};try{result=await response.json()}catch(_){throw new Error(`HTTP ${response.status}: invalid server response`)}if(!response.ok||!result.ok)throw new Error(result.error||`HTTP ${response.status}`);
      if(result.shape_geometry_i639&&result.shape_geometry_i639.raw_cot_i636)state.shapeEdit.draft.raw_cot_i636=result.shape_geometry_i639.raw_cot_i636;reassertActiveShapeDraftI640();const confirmation=await confirmSavedDraftI641(targetGeometry,result,source,status);state.shapeEdit.lastSaveConfirmation=confirmation.method;state.shapeEdit.confirmedObject=confirmation.object||null;commitDraftI640(result,name,notes,confirmation.object||null);
      clearMapEditorsI639();state.shapeEdit.active=false;state.shapeEdit.snapshot=null;state.shapeEdit.draft=null;state.shapeEdit.draftKey='';state.shapeEdit.baseObject=null;state.shapeEdit.deferredObject=null;state.shapeEdit.confirmedObject=null;state.shapeEdit.dirty=false;state.mode='info';state.panel.classList.remove('shape-editing-i639');renderInfo(true);try{if(typeof window.refreshCot==='function')await window.refreshCot()}catch(_){}try{if(typeof window.refreshLocalData==='function')await window.refreshLocalData()}catch(_){}
    }catch(error){state.shapeEdit.lastSaveError=String(error.message||error);if(status)status.textContent='Save failed: '+state.shapeEdit.lastSaveError;state.errors.push(`shape-save:${state.shapeEdit.lastSaveError}`);reassertActiveShapeDraftI640()}
    finally{state.shapeEdit.saveBusy=false;if(save&&save.isConnected)save.disabled=false;if(cancel&&cancel.isConnected)cancel.disabled=false}
  }
  function cancelShapeEditI639(event,render){if(event){event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation()}if(!state.shapeEdit.active)return;restoreShapeI639();clearMapEditorsI639();state.shapeEdit.active=false;state.shapeEdit.draft=null;state.shapeEdit.draftKey='';state.shapeEdit.baseObject=null;state.shapeEdit.deferredObject=null;state.shapeEdit.confirmedObject=null;state.shapeEdit.snapshot=null;state.shapeEdit.saveBusy=false;state.shapeEdit.dirty=false;state.shapeEdit.lastSaveError='';state.shapeEdit.lastSaveConfirmation='';state.mode='info';if(state.panel)state.panel.classList.remove('shape-editing-i639');if(render!==false)renderInfo(true)}
  function makeShapeActionButtonsI640(details){
    const actions=details&&details.querySelector('.tak-v322-actions,.popup-edit-actions');if(!actions)return;actions.className='tak-v322-actions popup-edit-actions tak-shape-edit-actions-i640';actions.replaceChildren();
    const save=document.createElement('button');save.type='button';save.textContent='Save';save.dataset.i640ShapeSave='1';save.dataset.i641ShapeSave='1';save.addEventListener('click',saveShapeEditI639,true);
    const cancel=document.createElement('button');cancel.type='button';cancel.textContent='Cancel';cancel.dataset.i640ShapeCancel='1';cancel.dataset.i641ShapeCancel='1';cancel.addEventListener('click',ev=>cancelShapeEditI639(ev,true),true);
    actions.append(save,cancel);
  }
  function enterShapeEditI639(){
    if(!state.body||!state.selected||kindOf(state.selected.object)!=='Shape'||state.shapeEdit.active)return;const popup=state.body.querySelector('.tak-v322-popup'),details=popup&&popup.querySelector('details.popup-edit');if(!popup||!details)return;state.shapeEdit.active=true;state.shapeEdit.snapshot=snapshotShapeI639();state.shapeEdit.draft=makeShapeDraftI640(state.selected.object);state.shapeEdit.baseObject=state.selected.object;state.shapeEdit.draftKey=state.selected.key||objectKey(state.selected.object,state.selected.source);state.shapeEdit.deferredObject=null;state.shapeEdit.dirty=false;state.shapeEdit.revision=0;state.shapeEdit.lastSaveError='';state.shapeEdit.lastSaveConfirmation='';state.shapeEdit.confirmedObject=null;state.mode='shape-edit-i643';state.panel.classList.add('shape-editing-i639');setHeader('Edit Shape','');details.open=true;const toggle=popup.querySelector('.tak-shape-edit-toggle-i639');if(toggle)toggle.style.display='none';
    const title=popup.querySelector('.tak-v322-title'),nameInput=details.querySelector('[name="name"]'),centerInput=details.querySelector('[name="latlon"]'),notesInput=details.querySelector('[name="notes"]'),fields=details.querySelector('.tak-v322-edit-fields');if(nameInput&&title){nameInput.classList.add('tak-shape-name-input-i639');nameInput.setAttribute('aria-label','Name');nameInput.addEventListener('input',markShapeDirtyI640);title.replaceChildren(nameInput)}
    let centerRow=findRowI639('Center');if(!centerRow)centerRow=findRowI639('Lat/Lon')||findRowI639('Coordinates');if(centerRow){const label=centerRow.querySelector('b'),value=centerRow.querySelector('span');if(label)label.textContent='Center';if(centerInput&&value){centerInput.classList.add('tak-shape-center-input-i639');centerInput.setAttribute('aria-label','Center');value.replaceChildren(centerInput);centerInput.addEventListener('change',()=>{const c=parseCenterI639(centerInput.value);if(c){translateToCenterI639(c);syncShapeEditUiI639()}else updateCenterEditorI639()})}}
    let notesRow=findRowI639('Notes');if(!notesRow&&notesInput){const table=popup.querySelector('.tak-v322-table'),anchor=findRowI639('Added');notesRow=document.createElement('div');notesRow.className='tak-v322-row tak-edit-notes-row-i639';notesRow.innerHTML='<b>Notes</b><span></span>';if(anchor)table.insertBefore(notesRow,anchor);else table.appendChild(notesRow)}if(notesRow&&notesInput){notesInput.classList.add('tak-shape-notes-input-i639');notesInput.setAttribute('aria-label','Notes');notesInput.addEventListener('input',markShapeDirtyI640);notesRow.querySelector('span').replaceChildren(notesInput);const table=popup.querySelector('.tak-v322-table');if(table&&notesRow.parentNode===table)table.appendChild(notesRow)}
    if(fields)fields.style.display='none';const catInput=details.querySelector('[name="category"]');if(catInput)catInput.disabled=true;makeShapeActionButtonsI640(details);rebuildHandlesI639();syncShapeEditUiI639();try{nameInput&&nameInput.focus()}catch(_){}
  }
  function installShapeEditToggle(openWanted){
    if(!state.body||!state.selected||kindOf(state.selected.object)!=='Shape')return;const popup=state.body.querySelector('.tak-v322-popup'),details=popup&&popup.querySelector('details.popup-edit');if(!details)return;const summary=details.querySelector('summary');if(summary)summary.style.setProperty('display','none','important');if(!state.shapeEdit.active)details.open=false;
    let button=popup.querySelector('.tak-shape-edit-toggle-i639');if(!button){button=document.createElement('button');button.type='button';button.className='tak-shape-edit-toggle-i639';details.parentNode.insertBefore(button,details);button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();enterShapeEditI639()})}button.textContent='Edit';button.style.display=state.shapeEdit.active?'none':'';
  }
  function activeShapeMatchesI640(object,source){return !!(state.shapeEdit.active&&state.shapeEdit.draftKey&&object&&objectKey(object,effectiveSource(object,source))===state.shapeEdit.draftKey)}
  function protectActiveShapeLayerI640(layer,object,source){if(!activeShapeMatchesI640(object,source)||!layer)return false;state.shapeEdit.deferredObject=object;state.selected.layer=layer;state.selected.center=shapeCenterI639(state.shapeEdit.draft);applyDraftToLayerI640(layer);syncHandlesToDraftI640();refreshDistanceLabelsI639();return true}
  function reassertActiveShapeDraftI640(){if(!state.shapeEdit.active||!state.shapeEdit.draft)return;updateLayerGeometryI639();syncHandlesToDraftI640();updateCenterEditorI639();applyGeometryPresentation();refreshDistanceLabelsI639()}

  // i684: presentation-only. Never shorten or rewrite the saved route geometry.
  function formatRouteDetailsI684(){
    if(!state.body||!state.selected||kindOf(state.selected.object)!=='Route')return;
    const table=state.body.querySelector('.tak-v322-table');if(!table)return;
    for(const row of Array.from(table.querySelectorAll('.tak-v322-row'))){
      const label=row.querySelector('b');if(!label)continue;
      const key=text(label.textContent);
      if(/^points$/i.test(key)){row.remove();continue}
      if(!/^notes$/i.test(key))continue;
      const cell=row.querySelector('span');if(!cell)continue;
      const original=cell.textContent||'';
      const lineKeys=/\b(Method|Direction|Route Type|Order|Prefix|Line Style|Notes)\s*:\s*/gi;
      const matches=Array.from(original.matchAll(lineKeys));
      if(!matches.length){cell.style.whiteSpace='pre-line';continue}
      const entries=[];
      if(original.slice(0,matches[0].index).trim())entries.push(original.slice(0,matches[0].index).trim());
      for(let i=0;i<matches.length;i++){
        const current=matches[i],next=matches[i+1];
        const value=original.slice(current.index+current[0].length,next?next.index:original.length).trim();
        if(value)entries.push(current[1]+': '+value);
      }
      if(!entries.length){cell.textContent='';continue}
      cell.replaceChildren();
      entries.forEach(value=>{const line=document.createElement('div');line.textContent=value;line.style.marginBottom='3px';line.style.overflowWrap='anywhere';cell.appendChild(line)});
    }
  }
  function decorateInfo(openWanted) { applySourcePresentation(); applyShapeFieldLabels(); applyGeometryPresentation(); formatRouteDetailsI684(); installShapeEditToggle(openWanted); }

  function renderInfo(force) {
    if (!state.selected || !ensurePanel()) return;
    const previousMode=state.mode;
    const signature=selectedInfoSignature(state.selected.object,state.selected.source);
    const openEdit=!!(state.body && state.body.querySelector('details.popup-edit[open]'));
    if (!force && previousMode==='info' && state.infoSignature===signature && state.body && state.body.firstElementChild) return;
    if (!force && previousMode==='info' && openEdit) { state.pendingInfoSignature=signature; return; }
    restorePanelHost();
    state.mode = 'info';
    const shapeContext=kindOf(state.selected.object)==='Shape';
    state.panel.classList.remove('generic-edit','gateway-data-readonly-i615','gateway-data-nifc-i620','shape-editing-i639');
    state.panel.classList.toggle('shape-context-i639',shapeContext);
    state.panel.removeAttribute('data-context-mode');
    state.panel.removeAttribute('data-gateway-source-key-i620');
    if (state.body) delete state.body.dataset.gatewayReadonlySignatureI615;
    setHeader(kindOf(state.selected.object), shapeContext?'':objectName(state.selected.object));
    state.body.innerHTML = infoHtml(state.selected.object, state.selected.source, state.selected.layer);
    state.body.querySelectorAll('.leaflet-popup-close-button').forEach(node => node.remove());
    decorateInfo(openEdit);
    appendInfoDeleteAction();
    appendRouteEditActionI667();
    combineLocalRouteActionsI668();
    sanitizeSidebarDeleteButtons();
    state.infoSignature=signature; state.pendingInfoSignature='';
    openPanel();
  }

  function centerSelected() {
    const m = mapInstance();
    if (!m || !state.selected) return;
    const center = objectCenter(state.selected.object, state.selected.layer);
    if (!center) return;
    try { m.panTo(center, {animate:true, duration:.25}); } catch (_) { try { m.setView(center, m.getZoom(), {animate:true}); } catch (_) {} }
  }

  // i684: The Object Details panel uses its own selection lifecycle, not
  // Leaflet popupopen. Tell the elevation profile when the authoritative
  // selection changes; do not clone or serialize a full route geometry.
  function announceSelectionI684(selected) {
    try {
      const item = selected || null;
      window.dispatchEvent(new CustomEvent('tak-map-context-selection-i684', {
        detail: item ? {
          selected: true, kind: kindOf(item.object), object: item.object,
          source: item.source, key: item.key
        } : { selected: false }
      }));
    } catch (error) { console.warn('[TAK Map] context selection notification failed', error); }
  }

  function showObject(object, source, layer, shouldCenter) {
    if (!object) return;
    if (state.shapeEdit.active) cancelShapeEditI639(null,false);
    if (object.__gatewayDataI614 || object.__gatewayDataReadOnlyI615 || source === 'gateway-data') {
      return showReadOnly({
        object, layer:layer || object.__layer || null,
        key:`gateway-data:${text(object.uid || object.id)}`,
        kicker:`Gateway Data · ${text(object.gateway_source_label) || 'Gateway Data'}`,
        title:objectName(object),
        html:text(object.__gatewayDataHtmlI615 || (layer && layer.__takGatewayReadOnlyHtmlI615) || layer && layer.__takMapI570InfoHtml),
        signature:text(object.__gatewayDataSignatureI615 || '')
      });
    }
    source=effectiveSource(object,source);
    const key = objectKey(object, source);
    state.selected = {object, source:source || 'datasync', layer:layer || object.__layer || null, key, center:objectCenter(object, layer || object.__layer)};
    state.suppressMapClickUntil = Date.now() + 360;
    state.infoSignature=''; state.pendingInfoSignature='';
    renderInfo(true);
    announceSelectionI684(state.selected);
    if (shouldCenter !== false) centerSelected();
  }

  function showReadOnly(options) {
    options = options || {};
    const object = options.object || {};
    const layer = options.layer || object.__layer || null;
    const panel = ensurePanel();
    if (!panel || !state.body) return false;
    mountGatewayOverlay();
    const key = text(options.key) || `gateway-data:${text(object.uid || object.id || object.name || object.title)}`;
    const html = text(options.html) || `<div class="feature-popup gateway-feature-popup-v491" data-gateway-context-uid="${esc(text(object.uid || object.id))}"><h3>${esc(text(options.title) || objectName(object))}</h3><div class="kvp"><b>Source</b><span>${esc(text(object.gateway_source_label) || 'Gateway Data')}</span></div></div>`;
    const signature = text(options.signature) || `${key}|${html}`;
    const sameSelection = !!(state.selected && state.selected.key === key && state.mode === 'gateway-data-readonly');
    state.selected = {object, source:'gateway-data-readonly', layer, key, center:objectCenter(object, layer)};
    state.mode = 'gateway-data-readonly';
    state.suppressMapClickUntil = Date.now() + 360;
    const gatewaySourceKey = text(object.gateway_source_key || object.source_key || '').toLowerCase();
    panel.classList.remove('generic-edit');
    panel.classList.add('gateway-data-readonly-i615');
    panel.classList.toggle('gateway-data-nifc-i620', gatewaySourceKey === 'nifc_fire_perimeters');
    if (gatewaySourceKey) panel.setAttribute('data-gateway-source-key-i620', gatewaySourceKey);
    else panel.removeAttribute('data-gateway-source-key-i620');
    panel.setAttribute('data-context-mode','gateway-data-readonly');
    setHeader(text(options.kicker) || `Gateway Data · ${text(object.gateway_source_label) || 'Gateway Data'}`, text(options.title) || objectName(object));
    if (!sameSelection || state.body.dataset.gatewayReadonlySignatureI615 !== signature) {
      state.body.innerHTML = html;
      state.body.dataset.gatewayReadonlySignatureI615 = signature;
    }
    state.body.querySelectorAll('.leaflet-popup-close-button,details.popup-edit,.popup-edit,.tak-context-delete-row-i572,.tak-context-delete-unavailable-i572,[data-i556-point-edit],[data-i572-point-edit],[data-tak-i572-delete-current]').forEach(node => node.remove());
    openPanel();
    announceSelectionI684(state.selected);
    return true;
  }

  function hide(reason) {
    if (state.shapeEdit.active) { state.suppressMapClickUntil=Date.now()+360; reassertActiveShapeDraftI640(); return false; }
    const panel = ensurePanel();
    if (!panel || panel.classList.contains('collapsed')) return;
    state.hiding = true;
    try {
      const editor = document.getElementById('takMapPointEditorI556');
      if (editor && editor.classList.contains('active')) {
        const registry = window.TakMapIconRegistryI572 || window.TakMapIconRegistryI556;
        if (registry && typeof registry.closePointEditor === 'function') registry.closePointEditor(reason || 'hide');
      }
    } catch (_) {}
    panel.classList.add('collapsed');
    panel.classList.remove('generic-edit','gateway-data-readonly-i615','gateway-data-top-overlay-i617','gateway-data-nifc-i620');
    panel.classList.add('tak-context-top-overlay-i618');
    panel.removeAttribute('data-context-mode');
    panel.removeAttribute('data-gateway-source-key-i620');
    panel.setAttribute('aria-hidden', 'true');
    restorePanelHost();
    state.mode = 'info';
    state.selected = null; state.infoSignature=''; state.pendingInfoSignature='';
    announceSelectionI684(null);
    setTimeout(() => { state.hiding = false; if (state.body) { state.body.innerHTML = ''; delete state.body.dataset.gatewayReadonlySignatureI615; } }, 230);
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

  // i667: Local saved routes must expose Edit Route in the contextual sidebar.
  // Previous popupopen handlers are removed when this sidebar owns the selection.
  function locateSavedRouteI667(object){
    if(!object||!window.takRouteEditorI654)return null;
    const id=String(object.object_id||object.local_id||'');
    const importId=String(object.import_id||'');
    if(!id||!importId||!object.route_revision_i659)return null;
    let imports=[];
    try{imports=Array.isArray(lastImports)?lastImports:(window.lastImports||[])}catch(_){imports=window.lastImports||[]}
    for(const file of imports){
      if(String(file.id||'')!==importId)continue;
      for(const feature of file.features||[]){
        if(String(feature.object_id||feature.local_id||'')===id&&feature.kind==='route'
            &&String(feature.route_revision_i659||'')===String(object.route_revision_i659))
          return {feature,file};
      }
    }
    return null;
  }
  function appendRouteEditActionI667(){
    if(!state.body||!state.selected||state.selected.source!=='local'||kindOf(state.selected.object)!=='Route')return;
    state.body.querySelectorAll('.tak-context-route-edit-row-i667').forEach(x=>x.remove());
    const entry=locateSavedRouteI667(state.selected.object);
    const row=document.createElement('div');row.className='tak-context-route-edit-row-i667';
    row.style.cssText='margin:12px 0 9px;';
    const button=document.createElement('button');button.type='button';
    button.dataset.takI667EditRoute='1';button.textContent='Edit Route';
    button.style.cssText='display:block;width:100%;border:1px solid #94a4b0;border-radius:9px;background:linear-gradient(#d7dce0,#bfc9d0);color:#15212a;font-weight:800;font-size:13px;padding:10px 14px;cursor:pointer;';
    if(!entry){button.disabled=true;button.title='Refresh the saved route to confirm its editable revision and identity';button.style.opacity='.55'}
    row.appendChild(button);
    const del=state.body.querySelector('.tak-context-delete-row-i572');
    if(del)state.body.insertBefore(row,del);else state.body.appendChild(row);
  }
  function combineLocalRouteActionsI668(){
    if(!state.body||!state.selected||state.selected.source!=='local'||kindOf(state.selected.object)!=='Route')return;
    const edit=state.body.querySelector('.tak-context-route-edit-row-i667');
    const del=state.body.querySelector('.tak-context-delete-row-i572');
    if(!edit||!del)return;
    const eb=edit.querySelector('button'),db=del.querySelector('button');
    if(!eb||!db)return;
    const row=document.createElement('div');row.className='tak-context-route-actions-i668';
    row.style.cssText='box-sizing:border-box;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:8px;width:100%;margin:12px 0 9px;padding:0 12px 12px;align-items:stretch;';
    eb.textContent='Edit';db.textContent='Delete';
    eb.style.width='100%';db.style.width='100%';
    eb.style.height='34px';db.style.height='34px';
    eb.style.margin='0';db.style.margin='0';
    eb.style.minWidth='0';db.style.minWidth='0';
    edit.replaceWith(row);row.append(eb,db);del.remove();
  }
  function beginSavedRouteEditI667(){
    if(!state.selected||state.selected.source!=='local')return;
    const entry=locateSavedRouteI667(state.selected.object);
    const api=window.takRouteEditorI654;
    if(!entry||!api||typeof api.startEditingSavedRoute!=='function')return;
    const ok=api.startEditingSavedRoute(entry.feature,entry.file);
    if(ok&&state.panel){state.panel.classList.add('collapsed');state.panel.setAttribute('aria-hidden','true')}
  }

  function appendInfoDeleteAction() {
    if (!state.body || !state.selected) return;
    state.body.querySelectorAll('.tak-context-delete-row-i572,.tak-context-delete-unavailable-i572').forEach(node => node.remove());
    const capability = deleteCapability(state.selected.object, state.selected.source);
    const row = document.createElement('div');
    row.className = 'tak-context-delete-row-i572';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'tak-context-delete-button-i572';
    button.dataset.takI572DeleteCurrent = '1';
    button.textContent = `Delete ${kindOf(state.selected.object).replace(' / Area','')}`;
    if (!capability.supported) {
      button.disabled = true;
      button.title = capability.reason;
      button.setAttribute('aria-describedby','takContextDeleteUnavailableI572');
    }
    row.appendChild(button);
    state.body.appendChild(row);
    if (!capability.supported) {
      const note = document.createElement('div');
      note.id = 'takContextDeleteUnavailableI572';
      note.className = 'tak-context-delete-unavailable-i572';
      note.textContent = capability.reason;
      state.body.appendChild(note);
    }
  }

  function missionNames(object) {
    const names = [];
    const add = value => { const v=text(value); if (v && !names.some(x=>x.toLowerCase()===v.toLowerCase())) names.push(v); };
    try { for (const value of (object && object.mission_memberships) || []) add(value); } catch (_) {}
    try { for (const value of (object && object.mission_names) || []) add(value); } catch (_) {}
    add(object && object.mission_name); add(object && object.mission);
    return names;
  }

  function missionBacked(object) {
    return !!(missionNames(object).length || object && (object.is_mission_object === true || object.association_scope === 'mission' || object.cot_xml_projected_i598 === true));
  }

  function effectiveSource(object, source) {
    if (missionBacked(object)) return 'datasync';
    return source === 'local' ? 'local' : (source || 'datasync');
  }

  function sourceLabel(object, source) {
    const effective = effectiveSource(object, source);
    if (effective === 'local') return 'Local Data';
    const mission = missionNames(object)[0] || '';
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
    state.body.innerHTML = `<div class="tak-context-delete-state-i572"><h3>${esc(error ? 'The object was not deleted' : `Delete ${objectName(object)}?`)}</h3><p>${esc(error ? 'TAK Map kept the object and its sidebar open because OpenTAKServer did not confirm deletion.' : 'Review the source-owned object that will be permanently removed.')}</p><div class="tak-context-delete-summary-i572"><b>Type</b><span>${esc(kindOf(object))}</span><b>Source</b><span>${esc(sourceLabel(object,state.selected.source))}</span>${location ? `<b>Location</b><span>${esc(location)}</span>` : ''}</div>${error ? `<p class="tak-context-delete-error-i572">${esc(error)}</p>` : '<p class="tak-context-delete-warning-i572">This action cannot be undone.</p>'}<div class="tak-context-delete-actions-i572"><button type="button" data-i572-delete-cancel>${error ? 'Back' : 'Cancel'}</button><button type="button" class="danger" data-i572-delete-confirm ${capability.supported ? '' : 'disabled'}>${error ? 'Retry Delete' : 'Delete'}</button></div></div>`;
    openPanel();
    positionPanel();
  }

  function renderDeleting() {
    if (!state.selected || !ensurePanel()) return;
    state.mode = 'deleting';
    setHeader('Deleting', objectName(state.selected.object));
    state.body.innerHTML = `<div class="tak-context-delete-state-i572"><h3><span class="tak-context-delete-spinner-i572" aria-hidden="true"></span>Deleting ${esc(objectName(state.selected.object))}</h3><p>Waiting for OpenTAKServer Mission removal, terminal CoT deletion, and absence confirmation.</p><div class="tak-context-delete-actions-i572"><button type="button" disabled>Deleting…</button></div></div>`;
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
      try { if (typeof window.refreshDataSync === 'function') await window.refreshDataSync(true,'context-sidebar-delete-i572'); } catch (_) {}
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
      button.dataset.takI572DeleteIndex = index;
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
      button.dataset.takI572DeleteCurrent = '1';
    }
  }

  function installDeleteController() {
    if (window.__takMapDeleteControllerI572Installed) return;
    window.__takMapDeleteControllerI572Installed = true;
    const assign = (name, value) => {
      try { window[name] = value; } catch (_) {}
      try { window.__takI572Assign = value; window.eval(`${name}=window.__takI572Assign`); delete window.__takI572Assign; } catch (_) {}
    };
    assign('deleteDataSyncItem', deleteDataSyncByIndex);
    try { const lifecycle = lifecycleApi(); if (lifecycle) lifecycle.deleteDataSyncItem = deleteDataSyncByIndex; } catch (_) {}
    document.addEventListener('click', event => {
      const target = event.target && event.target.closest && event.target.closest('[data-tak-i667-edit-route],[data-tak-i572-delete-index],[data-tak-i572-delete-current],[data-i572-delete-confirm],[data-i572-delete-cancel]');
      if (!target) return;
      try { event.preventDefault(); event.stopPropagation(); event.stopImmediatePropagation(); } catch (_) {}
      if (target.hasAttribute('data-tak-i667-edit-route')) { beginSavedRouteEditI667(); return; }
      if (target.hasAttribute('data-i572-delete-cancel')) { renderInfo(); return; }
      if (target.hasAttribute('data-i572-delete-confirm')) { confirmCurrentDelete(); return; }
      if (target.hasAttribute('data-tak-i572-delete-current')) { renderDeleteConfirmation(''); return; }
      deleteDataSyncByIndex(Number(target.dataset.takI572DeleteIndex), event);
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
    const host = button.closest('.point-popup-location-i572');
    const value = text(host && host.querySelector('.point-popup-location-text-i572') && host.querySelector('.point-popup-location-text-i572').textContent);
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
    const deleteCurrent = event.target && event.target.closest && event.target.closest('[data-tak-i572-delete-current]');
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
    const edit = event.target && event.target.closest && event.target.closest('[data-i556-point-edit],[data-i572-point-edit]');
    if (!edit) return;
    event.preventDefault();
    event.stopPropagation();
    try { event.stopImmediatePropagation(); } catch (_) {}
    const registry = window.TakMapIconRegistryI572 || window.TakMapIconRegistryI556;
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
    if (state.shapeEdit.active) { state.suppressMapClickUntil=Date.now()+360; try { if (event.originalEvent && window.L && window.L.DomEvent) window.L.DomEvent.stop(event.originalEvent); } catch (_) {} reassertActiveShapeDraftI640(); return; }
    state.suppressMapClickUntil = Date.now() + 360;
    try { if (event.originalEvent && window.L && window.L.DomEvent) window.L.DomEvent.stop(event.originalEvent); } catch (_) {}
    showObject(record.object, record.source, layer, true);
  }

  function bindObjectLayer(layer, object, source) {
    if (!layer || !object || typeof layer.on !== 'function') return layer;
    source=effectiveSource(object,source);
    const key = objectKey(object, source);
    const previous = state.layerObjects.get(layer);
    if (previous && previous.key === key) { previous.object = object; previous.source = source; }
    try { if (!layer.__takMapI572InfoHtml) layer.__takMapI572InfoHtml = popupContent(layer); } catch (_) {}
    try { if (typeof layer.unbindPopup === 'function') layer.unbindPopup(); } catch (_) {}
    try { layer.off('mouseover'); layer.off('mouseout'); layer.off('popupopen'); layer.off('popupclose'); layer.off('click'); } catch (_) {}
    try { layer.on('click', layerClickHandler); } catch (error) { state.errors.push(`bind:${error.message || error}`); }
    const record = {object, source:source || 'datasync', key};
    state.layerObjects.set(layer, record);
    state.keyLayers.set(key, layer);
    if (state.shapeEdit.active && key===state.shapeEdit.draftKey) protectActiveShapeLayerI640(layer,object,source);
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
    for (const [object, source0] of rows) {
      const source=effectiveSource(object,source0);
      if (object && object.__layer) bindObjectLayer(object.__layer, object, source);
      if (object && object.__hitLayer) bindObjectLayer(object.__hitLayer, object, source);
      if (state.selected && objectKey(object, source) === state.selected.key) {
        if (state.shapeEdit.active && state.shapeEdit.draftKey===state.selected.key) {
          state.shapeEdit.deferredObject=object;
          state.selected.source=source;
          state.selected.layer=object.__layer||object.__hitLayer||state.selected.layer;
          state.selected.center=shapeCenterI639(state.shapeEdit.draft);
          if(object.__layer)applyDraftToLayerI640(object.__layer);
          if(object.__hitLayer)applyDraftToLayerI640(object.__hitLayer);
        } else {
          state.selected.object = object;
          state.selected.source = source;
          state.selected.layer = object.__layer || object.__hitLayer || state.selected.layer;
          state.selected.center = objectCenter(object, state.selected.layer);
        }
      }
    }
    if (state.selected && state.mode === 'info' && state.panel && !state.panel.classList.contains('collapsed')) renderInfo(false);
  }

  function assignGlobal(name, value) {
    try { window[name] = value; } catch (_) {}
    try { window.__takMapI572Global = value; window.eval(`${name}=window.__takMapI572Global`); delete window.__takMapI572Global; } catch (_) {}
  }

  function wrapRuntime() {
    if (!state.wrapped.addObjectLayer && typeof window.addObjectLayer === 'function') {
      const base = window.addObjectLayer;
      const wrapper = function (group, object, sourceKey) {
        const layer = base.apply(this, arguments);
        setTimeout(() => {
          if (object && object.__layer) bindObjectLayer(object.__layer, object, sourceKey || 'datasync');
          if (object && object.__hitLayer) bindObjectLayer(object.__hitLayer, object, sourceKey || 'datasync');
          if (layer) { bindObjectLayer(layer, object, sourceKey || 'datasync'); protectActiveShapeLayerI640(layer,object,sourceKey||'datasync'); }
        }, 0);
        return layer;
      };
      wrapper.__takMapContextI572 = true;
      state.wrapped.addObjectLayer = base;
      assignGlobal('addObjectLayer', wrapper);
    }
    for (const name of ['drawDataSyncObjects','drawImportedObjects']) {
      if (!state.wrapped[name] && typeof window[name] === 'function') {
        const base = window[name];
        const wrapper = function () { const result = base.apply(this, arguments); try{scanObjects();reassertActiveShapeDraftI640()}catch(_){} setTimeout(()=>{scanObjects();reassertActiveShapeDraftI640()},0); setTimeout(()=>{scanObjects();reassertActiveShapeDraftI640()},80); return result; };
        wrapper.__takMapContextI572 = true;
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
    if (!state.wrapped.renderDataSyncRowsI572 && typeof window.renderDataSyncRows === 'function') {
      const base = window.renderDataSyncRows;
      const wrapper = function () { const result = base.apply(this, arguments); sanitizeDataSyncDeleteButtons(document); return result; };
      wrapper.__takMapContextI572 = true;
      state.wrapped.renderDataSyncRowsI572 = base;
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
    if (!m || m.__takMapContextSidebarI572) return false;
    m.__takMapContextSidebarI572 = true;
    m.on('click', event => {
      if (Date.now() < state.suppressMapClickUntil) return;
      const target = event && event.originalEvent && event.originalEvent.target;
      if (target && state.panel && state.panel.contains(target)) return;
      if(state.shapeEdit.active){reassertActiveShapeDraftI640();return;}
      hide('map');
    });
    m.on('moveend zoomend', () => {
      positionPanel();
      if(state.shapeEdit.active)reassertActiveShapeDraftI640();
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
    showReadOnly,
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
      silverTheme: !!document.getElementById('takMapContextSidebarStyleI572'),
      contextualDelete: true,
      gatewayDataReadOnly: true,
      readOnlyMode: state.mode === 'gateway-data-readonly',
      gatewayTopOverlay: state.gatewayOverlayMounted,
      themedGatewayScrollbar: true,
      adaptiveGatewayWidth: true,
      sharedDynamicWidthI618: !!window.TakMapContextPanelSizingI618, compactShapeWidthI638:true, stableShapeInfoI638:true, localizedGeometryI638:true, missionSourceAttributionI638:true, inPlaceShapeEditI639:true, geometryHandlesI639:true, dynamicSegmentLabelsI639:true, silverShapeButtonsI639:true, centerLabelI639:true, panelWidthHeightRemovedI639:true, shapeEditActiveI639:!!state.shapeEdit.active, shapeEditHandleCountI639:(state.shapeEdit.handles||[]).length, shapeEditLabelCountI639:(state.shapeEdit.labels||[]).length, authoritativeDraftI640:true, refreshProtectedDraftI640:true, dedicatedSaveCancelI640:true, closeEditRemovedI640:true, categoryRowRemovedI640:true, rotationRowRemovedI640:true, normalWeightShapeNameI640:true, verifiedSaveReadbackI641:true, authoritativeMissionSaveI642:true, aggregateDataSyncCommitGateI642:false, ringOrderIndependentI642:true, nativeShapeSaveI643:true, globalNativeShapeReadbackI643:true, missionContentsUidAssociationI643:true, missionCotGetOnlyI643:true, persistentEditUntilExplicitExitI641:true, centerTranslationHandleI641:true, notesLastI641:true, largerSaveCancelTextI641:true, shapeEditActiveI640:!!state.shapeEdit.active, shapeEditDirtyI640:!!state.shapeEdit.dirty, shapeEditRevisionI640:Number(state.shapeEdit.revision||0), shapeEditDraftKeyI640:state.shapeEdit.draftKey||'', shapeEditSaveErrorI640:state.shapeEdit.lastSaveError||'', shapeEditSaveConfirmationI641:state.shapeEdit.lastSaveConfirmation||'', nifcContentWidthI620: true,
      topOverlayAllContextsI618: !!(state.panel && state.panel.classList.contains('tak-context-top-overlay-i618')),
      nativeDeleteDialogs: false,
      sharedDeleteController: true,
      deleteMode: state.mode.startsWith('delete') || state.mode === 'deleting',
      errors: state.errors.slice(),
    }),
  });
  window.TakMapContextSidebarI572 = api;
  window.TakMapDeleteControllerI572 = api;
  window.TakMapContextSidebarI562 = api;

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true});
  else boot();
})(window, document);
