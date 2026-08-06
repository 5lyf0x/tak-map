/* TAK Map i572 canonical Local Data synchronization. Leaflet object popups are replaced by the contextual sidebar. */
(function (window, document) {
  'use strict';

  const VERSION = 'i572';
  const HIGHLIGHT_MS = 8000;
  const state563 = {
    installed: false,
    canonicalRefresh: null,
    refreshPromise: null,
    highlightId: '',
    highlightUntil: 0,
    originalFetch: null,
    popupObserver: null,
    errors: [],
  };

  const text = value => String(value == null ? '' : value).trim();
  const esc = value => text(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

  function addStyle() {
    if (document.getElementById('takMapPopupLocalDataStyleI572')) return;
    const style = document.createElement('style');
    style.id = 'takMapPopupLocalDataStyleI572';
    style.textContent = `
      .local-data-row.local-highlight-i572{border-color:#dce2e6!important;background:linear-gradient(90deg,rgba(210,218,224,.17),rgba(210,218,224,.045))!important;box-shadow:inset 3px 0 0 #d7dde1!important}
      .local-data-row.local-highlight-i572 b{color:#f2f5f7!important}
      .local-data-list.local-data-complete-i572{contain:content}
      .local-list-complete-note-i572{padding:5px 8px 7px;color:#8f9aa4;font-size:9px;text-align:right}
    `;
    document.head.appendChild(style);
  }

  function mapInstance() {
    try { if (typeof map !== 'undefined' && map) return map; } catch (_) {}
    return window.map || null;
  }

  function mapElement() {
    const mapObject = mapInstance();
    try {
      if (mapObject && typeof mapObject.getContainer === 'function') return mapObject.getContainer();
    } catch (_) {}
    return document.getElementById('map') || document.querySelector('.leaflet-container');
  }

  function popupLimit() {
    const element = mapElement();
    const rect = element && element.getBoundingClientRect ? element.getBoundingClientRect() : {width:window.innerWidth,height:window.innerHeight};
    return {
      width: Math.max(280, Math.floor(Number(rect.width || window.innerWidth) - 34)),
      height: Math.max(220, Math.floor(Number(rect.height || window.innerHeight) - 34)),
    };
  }

  function sizePopup(popup) {
    if (!popup) return;
    const limit = popupLimit();
    try {
      popup.options = popup.options || {};
      popup.options.maxHeight = null;
      popup.options.maxWidth = limit.width;
      popup.options.minWidth = Math.min(Number(popup.options.minWidth || 50), limit.width);
      popup.options.autoPan = true;
      popup.options.keepInView = true;
      popup.options.autoPanPaddingTopLeft = [17, 17];
      popup.options.autoPanPaddingBottomRight = [17, 17];
    } catch (_) {}

    const container = popup._container;
    const wrapper = container && container.querySelector ? container.querySelector('.leaflet-popup-content-wrapper') : null;
    const content = popup._contentNode || (container && container.querySelector ? container.querySelector('.leaflet-popup-content') : null);
    try {
      if (container) {
        container.style.maxWidth = `${limit.width}px`;
        container.style.setProperty('--tak-map-popup-max-width-i572', `${limit.width - 8}px`);
      }
      if (wrapper) {
        wrapper.style.maxHeight = 'none';
        wrapper.style.overflow = 'visible';
      }
      if (content) {
        content.classList.remove('leaflet-popup-scrolled');
        content.style.maxHeight = 'none';
        content.style.height = 'auto';
        content.style.overflow = 'visible';
        content.style.overflowX = 'visible';
        content.style.overflowY = 'visible';
      }
      if (typeof popup.update === 'function') popup.update();
    } catch (error) {
      state563.errors.push(`popup-size:${error.message || error}`);
    }

    requestAnimationFrame(() => {
      try {
        const refreshed = popup._contentNode || content;
        if (refreshed) {
          refreshed.classList.remove('leaflet-popup-scrolled');
          refreshed.style.maxHeight = 'none';
          refreshed.style.overflow = 'visible';
        }
        if (typeof popup.update === 'function') popup.update();
        if (typeof popup._adjustPan === 'function') popup._adjustPan();
      } catch (error) {
        state563.errors.push(`popup-pan:${error.message || error}`);
      }
    });
  }

  function resizeOpenPopup() {
    const mapObject = mapInstance();
    try {
      const popup = mapObject && mapObject._popup;
      if (popup && popup._map) sizePopup(popup);
    } catch (_) {}
  }

  function installPopupSizing() {
    const mapObject = mapInstance();
    if (!mapObject || mapObject.__takMapPopupSizingI572) return false;
    mapObject.__takMapPopupSizingI572 = true;
    try {
      mapObject.on('popupopen', event => sizePopup(event && event.popup));
      mapObject.on('resize moveend zoomend', resizeOpenPopup);
    } catch (error) {
      state563.errors.push(`popup-events:${error.message || error}`);
    }
    window.addEventListener('resize', resizeOpenPopup, {passive:true});
    window.addEventListener('orientationchange', () => setTimeout(resizeOpenPopup, 80), {passive:true});
    return true;
  }

  function mutationObserver() {
    if (state563.popupObserver || !document.body) return;
    state563.popupObserver = new MutationObserver(records => {
      let found = false;
      for (const record of records) {
        for (const node of record.addedNodes || []) {
          if (!(node instanceof Element)) continue;
          if (node.matches('.leaflet-popup,.leaflet-popup-content,.leaflet-popup-scrolled') || node.querySelector('.leaflet-popup,.leaflet-popup-scrolled')) {
            found = true;
            break;
          }
        }
        if (found) break;
      }
      if (found) requestAnimationFrame(resizeOpenPopup);
    });
    state563.popupObserver.observe(document.body, {subtree:true, childList:true});
  }

  function itemTimestamp(item) {
    const feature = item && item.feature || {};
    const props = feature.properties && typeof feature.properties === 'object' ? feature.properties : {};
    const values = [
      feature.updated, props.updated, feature.modified, props.modified,
      feature.created, props.created, feature.uploaded, props.uploaded,
    ];
    for (const value of values) {
      const parsed = Date.parse(text(value));
      if (Number.isFinite(parsed)) return parsed;
    }
    return 0;
  }

  function orderedLocalItems(items) {
    const list = Array.isArray(items) ? items.slice() : [];
    const highlight = state563.highlightUntil > Date.now() ? state563.highlightId : '';
    return list.sort((left, right) => {
      const leftHighlight = text(left && left.id) === highlight ? 1 : 0;
      const rightHighlight = text(right && right.id) === highlight ? 1 : 0;
      if (leftHighlight !== rightHighlight) return rightHighlight - leftHighlight;
      const timeDelta = itemTimestamp(right) - itemTimestamp(left);
      if (timeDelta) return timeDelta;
      return text(left && left.name).localeCompare(text(right && right.name), undefined, {numeric:true,sensitivity:'base'});
    });
  }

  function renderLocalSectionI572(kind, title, items) {
    let collapsed = false;
    try { collapsed = !!state.localCollapsed[kind]; } catch (_) {}
    const ordered = orderedLocalItems(items);
    const highlight = state563.highlightUntil > Date.now() ? state563.highlightId : '';
    let html = `<div class="local-section ${collapsed ? 'collapsed' : ''}"><div class="subgroup-title local-section-title" onclick="toggleLocalSection('${esc(kind)}')"><span class="subgroup-label"><span class="toggle">${collapsed ? '›' : '⌄'}</span>${esc(title)}</span><span class="chip">${ordered.length}</span><button class="layer-button unselect-local-btn" onclick="unselectLocalSection('${esc(kind)}',event)">Unselect All</button></div><div class="local-data-list local-data-complete-i572">`;
    if (ordered.length) {
      html += ordered.map(item => {
        const id = text(item && item.id);
        let checked = '';
        try { checked = state.local[kind] && state.local[kind][id] ? 'checked' : ''; } catch (_) {}
        const visibility = item && item.shown === false ? 'hidden' : 'shown';
        const isPoint = kind === 'points';
        const feature = item && item.feature || {};
        const lat = item && item.lat != null ? item.lat : feature.lat;
        const lon = item && item.lon != null ? item.lon : feature.lon;
        let coords = '';
        try { if (isPoint && lat != null && lon != null && typeof formatCoords === 'function') coords = formatCoords(lat, lon); } catch (_) {}
        const meta = coords || `${text(item && item.source) || 'Local Data'} · ${visibility}`;
        const highlightClass = id && id === highlight ? ' local-highlight-i572' : '';
        return `<div class="local-data-row ${checked ? 'selected-local' : ''} ${visibility === 'hidden' ? 'hidden-local' : ''}${highlightClass}" data-local-id="${esc(id)}"><label class="local-data-main"><input type="checkbox" ${checked} onchange="toggleLocalItem('${esc(kind)}','${esc(id)}',this.checked)"><span><b>${esc(item && item.name)}</b><small>${esc(meta)}</small></span></label><button class="layer-button local-goto-btn" onclick="centerLocalItem('${esc(kind)}','${esc(id)}',event)">Go To</button></div>`;
      }).join('');
      html += `<div class="local-list-complete-note-i572">All ${ordered.length} ${esc(title.toLowerCase())} shown</div>`;
    } else {
      html += `<div class="muted" style="padding:8px">No local ${esc(title.toLowerCase())} yet.</div>`;
    }
    let actions = '';
    try { if (typeof renderLocalActions === 'function') actions = renderLocalActions(kind, ordered); } catch (_) {}
    html += `</div>${actions}</div>`;
    return html;
  }

  function assignGlobal(name, value) {
    try { window[name] = value; } catch (_) {}
    try {
      window.__takMapI572GlobalValue = value;
      window.eval(`${name}=window.__takMapI572GlobalValue`);
      delete window.__takMapI572GlobalValue;
    } catch (_) {}
  }

  function setLastImports(imports) {
    const safe = Array.isArray(imports) ? imports : [];
    try { window.lastImports = safe; } catch (_) {}
    try {
      window.__takMapCanonicalImportsI572 = safe;
      window.eval('lastImports=window.__takMapCanonicalImportsI572');
    } catch (error) {
      state563.errors.push(`last-imports:${error.message || error}`);
    } finally {
      try { delete window.__takMapCanonicalImportsI572; } catch (_) {}
    }
  }

  function highlightFromPayload(payload) {
    if (!payload || typeof payload !== 'object') return '';
    const point = payload.point && typeof payload.point === 'object' ? payload.point : {};
    if (text(point.local_id)) return text(point.local_id);
    const imports = Array.isArray(payload.imports) ? payload.imports : [];
    if (!imports.length) return '';
    const latest = imports.slice().sort((left, right) => {
      const l = Date.parse(text(left && (left.uploaded || left.updated || left.created))) || 0;
      const r = Date.parse(text(right && (right.uploaded || right.updated || right.created))) || 0;
      return r - l;
    })[0] || imports[imports.length - 1];
    const features = Array.isArray(latest && latest.features) ? latest.features : [];
    if (!features.length) return '';
    const index = features.length - 1;
    return `${text(latest.id || latest.name)}:${index}`;
  }

  async function canonicalRefresh(options) {
    const opts = options || {};
    if (state563.refreshPromise && !opts.force) return state563.refreshPromise;
    const fetchImpl = state563.originalFetch || window.fetch.bind(window);
    state563.refreshPromise = (async () => {
      const response = await fetchImpl('/api/tak-map/imported', {cache:'no-store', credentials:'same-origin'});
      let body = {};
      try { body = await response.json(); } catch (_) { body = {}; }
      if (!response.ok || body.ok === false) throw new Error(body.error || `HTTP ${response.status}`);
      const imports = Array.isArray(body.imports) ? body.imports : [];
      if (text(opts.highlightId)) {
        state563.highlightId = text(opts.highlightId);
        state563.highlightUntil = Date.now() + HIGHLIGHT_MS;
      }
      setLastImports(imports);
      try { if (typeof renderImportRows === 'function') renderImportRows(); } catch (_) {}
      try { if (typeof renderLocalDataRows === 'function') renderLocalDataRows(); } catch (_) {}
      try { if (typeof drawImportedObjects === 'function') drawImportedObjects(); } catch (_) {}
      requestAnimationFrame(() => {
        try {
          const row = state563.highlightId && document.querySelector(`.local-data-row[data-local-id="${CSS.escape(state563.highlightId)}"]`);
          if (row) row.scrollIntoView({block:'nearest',behavior:'smooth'});
        } catch (_) {}
      });
      return Object.assign({}, body, {imports, version:VERSION});
    })().finally(() => { state563.refreshPromise = null; });
    return state563.refreshPromise;
  }

  function mutationRequest(url, method) {
    const path = (() => { try { return new URL(url, window.location.href).pathname; } catch (_) { return text(url).split('?')[0]; } })();
    if (String(method || 'GET').toUpperCase() === 'GET') return false;
    return path === '/api/tak-map/import' ||
      path === '/api/tak-map/import-clear' ||
      /\/api\/tak-map\/local-point-i\d+$/.test(path) ||
      /\/api\/tak-map\/(?:import|local-data)[^/]*(?:delete|remove|clear)/.test(path);
  }

  function installFetchRefresh() {
    if (window.fetch && window.fetch.__takMapI572) return;
    const previous = window.fetch.bind(window);
    state563.originalFetch = previous;
    const wrapped = async function (input, init) {
      const url = text(typeof input === 'string' ? input : input && input.url);
      const method = text(init && init.method || (input && input.method) || 'GET').toUpperCase();
      const response = await previous(input, init);
      if (response.ok && mutationRequest(url, method)) {
        let highlightId = '';
        try {
          const payload = await response.clone().json();
          highlightId = highlightFromPayload(payload);
        } catch (_) {}
        setTimeout(() => canonicalRefresh({highlightId, force:true}).catch(error => state563.errors.push(`post-mutation:${error.message || error}`)), 0);
      }
      return response;
    };
    wrapped.__takMapI572 = true;
    wrapped.__takMapI572Previous = previous;
    window.fetch = wrapped;
  }

  function installLocalDataPatch() {
    assignGlobal('renderLocalSection', renderLocalSectionI572);
    assignGlobal('refreshImports', canonicalRefresh);
    assignGlobal('refreshLocalData', canonicalRefresh);
    try { if (typeof renderLocalDataRows === 'function') renderLocalDataRows(); } catch (_) {}
  }

  function boot() {
    addStyle();
    installFetchRefresh();
    installLocalDataPatch();
    [120, 450, 1100, 2600, 5400].forEach(delay => setTimeout(() => {
      installLocalDataPatch();
    }, delay));
    state563.installed = true;
  }

  window.TakMapPopupLocalDataI572 = Object.freeze({
    version: VERSION,
    canonicalRefresh,
    renderLocalSection: renderLocalSectionI572,
    sizePopup: () => {},
    resizeOpenPopup: () => {},
    audit: () => ({
      version: VERSION,
      installed: state563.installed,
      leafletPopupSizingDisabled: true,
      completeLocalList: typeof window.renderLocalSection === 'function',
      fetchRefreshInstalled: !!(window.fetch && window.fetch.__takMapI572),
      highlightId: state563.highlightId,
      errors: state563.errors.slice(),
    }),
  });

  window.TakMapPopupLocalDataI562 = window.TakMapPopupLocalDataI572;

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true});
  else boot();
})(window, document);
