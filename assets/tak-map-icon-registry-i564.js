/* TAK Map i564 icon registry, related-symbol inspector, and reliable point create/edit windows. */
(function (window, document) {
  'use strict';

  const VERSION = 'i564';
  const API = '/api/tak-map/icon-registry';
  const POINT_API = '/api/tak-map/data-sync-point-i556';
  const LOCAL_POINT_API = '/api/tak-map/local-point-i556';
  const ALIAS_URL = '/mil2525/atak-compatibility-aliases-i553.json';
  const AFFILIATIONS = ['friendly', 'hostile', 'neutral', 'unknown'];
  const AFFILIATION_LABEL = {friendly:'Friendly',hostile:'Hostile',neutral:'Neutral',unknown:'Unknown'};
  const AFFILIATION_CODE = {friendly:'f',hostile:'h',neutral:'n',unknown:'u'};
  const SIDC_AFFILIATION = {friendly:'F',hostile:'H',neutral:'N',unknown:'U'};
  const DIMENSION_LABEL = {G:'Ground',A:'Air',S:'Sea Surface',U:'Subsurface',P:'Space',E:'Emergency'};

  const state = {
    booted: false,
    runtimeReady: false,
    ready: false,
    summary: null,
    aliasesReady: false,
    milLoadPromise: null,
    milError: '',
    otsIdentity: {display:'Data Sync: OpenTAKServer', url_hostname:'', server_hostname:''},
    otsIdentityPromise: null,
    cotByName: new Map(),
    activeSet: 'milstd2525c',
    activeGroup: '',
    activeAffiliation: 'friendly',
    activeDomain: 'Ground',
    selected: null,
    pickerTarget: 'point',
    customBySet: new Map(),
    customByPath: new Map(),
    editorPoint: null,
    editorSymbol: null,
    editorOriginal: null,
    editorDirty: false,
    editorSource: '',
    editorLocalId: '',
    baseDataSyncIcon: null,
    baseMilIconHtml: null,
    basePointPopupHtml: null,
    baseAddObjectLayer: null,
    baseDrawDataSyncObjects: null,
    baseDrawImportedObjects: null,
    old: {},
    errors: [],
    normalizedCache: new Map(),
    normalizerObserver: null,
  };
  let createSession = {active:false, id:0, mapCoordinateKey:'', manualLocation:false};

  function coordinateKey(coord) {
    return coord && finite(coord.lat) && finite(coord.lon) ? `${Number(coord.lat).toFixed(7)},${Number(coord.lon).toFixed(7)}` : '';
  }

  function pointStateCoordinate() {
    try {
      const ll = window.v233PointState && window.v233PointState.latlng;
      if (ll && finite(ll.lat) && finite(ll.lng)) return {lat:Number(ll.lat), lon:Number(ll.lng)};
    } catch (_) {}
    return null;
  }

  function resetCreateDraft(options) {
    const preserveReusable = !options || options.preserveReusable !== false;
    const destination = preserveReusable && byId('pointSaveDestinationI556') ? byId('pointSaveDestinationI556').value : 'local';
    const mission = preserveReusable && byId('pointMissionI556') ? byId('pointMissionI556').value : '';
    const affiliation = preserveReusable && byId('pointAffiliationI556') ? byId('pointAffiliationI556').value : 'friendly';
    const name = byId('pointNameInput'); if (name) name.value = '';
    const notes = byId('pointNotesInput'); if (notes) notes.value = '';
    const location = byId('pointLocationI556'); if (location) { location.value = ''; location.classList.remove('invalid'); }
    const error = byId('pointLocationErrorI556'); if (error) error.textContent = '';
    if (byId('pointSaveDestinationI556')) byId('pointSaveDestinationI556').value = destination || 'local';
    if (byId('pointMissionI556') && mission) byId('pointMissionI556').value = mission;
    if (byId('pointAffiliationI556')) byId('pointAffiliationI556').value = affiliation || 'friendly';
    window.v233PointState = window.v233PointState || {};
    window.v233PointState.name = '';
    window.v233PointState.notes = '';
    window.v233PointState.latlng = null;
    createSession = {active:false, id:createSession.id + 1, mapCoordinateKey:'', manualLocation:false};
    setCreateStatus('Ready to save the icon-based point.');
  }


  const byId = id => document.getElementById(id);
  const text = value => String(value == null ? '' : value).trim();
  const esc = value => text(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const finite = value => Number.isFinite(Number(value));
  const titleWords = value => text(value).replace(/[_-]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  const customAssetUrl = path => `${API}/icon?path=${encodeURIComponent(text(path))}`;

  async function apiJson(response) {
    let body = {};
    try { body = await response.json(); } catch (_) { body = {}; }
    if (!response.ok || body.ok === false) {
      const error = new Error(body.error || `HTTP ${response.status}`);
      error.status = response.status;
      error.payload = body;
      throw error;
    }
    return body;
  }

  function affiliationFromSidc(value) {
    return ({F:'friendly',H:'hostile',N:'neutral',U:'unknown'})[text(value).toUpperCase().charAt(1)] || 'friendly';
  }

  function affiliationFromCot(value) {
    const match = text(value).toLowerCase().match(/^a-([fhnu])(?:-|$)/);
    return ({f:'friendly',h:'hostile',n:'neutral',u:'unknown'})[match && match[1]] || 'friendly';
  }

  function milAffiliation(icon) {
    const name = text(icon && icon.name).toLowerCase();
    for (const value of AFFILIATIONS) if (name.startsWith(value + '-')) return value;
    return affiliationFromSidc(icon && icon.sidc);
  }

  function milDomain(icon) {
    const sidc = text(icon && icon.sidc).toUpperCase();
    if (DIMENSION_LABEL[sidc.charAt(2)]) return DIMENSION_LABEL[sidc.charAt(2)];
    const name = text(icon && icon.name).toLowerCase();
    if (name.includes('-air-')) return 'Air';
    if (name.includes('-sea-surface-')) return 'Sea Surface';
    if (name.includes('-subsurface-')) return 'Subsurface';
    if (name.includes('-space-')) return 'Space';
    if (name.includes('-emergency-')) return 'Emergency';
    return 'Ground';
  }

  function milCategory(icon) {
    const name = text(icon && icon.name).toLowerCase().replace(/^(friendly|hostile|neutral|unknown)-/, '');
    const parts = name.split('-').filter(Boolean);
    const domain = parts.shift() || 'ground';
    let family = parts.shift() || 'symbol';
    if (domain === 'sea' && family === 'surface') family = parts.shift() || 'surface';
    const known = [
      'infantry','armor','artillery','air-defense','engineer','reconnaissance','signal','medical','supply',
      'headquarters','transportation','aviation','special-forces','ranger','civil-affairs','psychological-operations',
      'vehicle','radar','sensor','weapon','installation','facility','emergency','aircraft','helicopter','vessel','submarine'
    ];
    const joined = parts.join('-');
    const branch = known.find(value => joined.includes(value)) || parts[0] || family;
    return [domain, family, branch].filter(Boolean).join('-');
  }

  function cotFromSidc(icon) {
    const sidc = text(icon && icon.sidc).toUpperCase();
    if (sidc.length < 4 || sidc.charAt(0) !== 'S') return '';
    const aff = ({F:'f',H:'h',N:'n',U:'u'})[sidc.charAt(1)] || 'u';
    const dim = sidc.charAt(2) || 'G';
    const functionId = sidc.slice(4, 10).replace(/-/g, '').split('').join('-');
    return ['a', aff, dim, functionId].filter(Boolean).join('-');
  }

  function milCotType(icon) {
    const direct = text(icon && icon.cot_type);
    if (direct) return direct;
    const reviewed = state.cotByName.get(text(icon && icon.name).toLowerCase());
    return reviewed || cotFromSidc(icon) || `a-${AFFILIATION_CODE[milAffiliation(icon)] || 'u'}-G`;
  }

  function customCotType(icon) {
    const affiliation = text(icon && icon.affiliation_override) || affiliationFromCot(icon && (icon.cot_type || icon.type2525b));
    const code = AFFILIATION_CODE[affiliation] || 'u';
    const raw = text(icon && (icon.type2525b || icon.cot_type));
    if (/^a-[fhnu]-[A-Za-z](?:-|$)/.test(raw)) {
      const parts = raw.split('-');
      parts[1] = code;
      return parts.join('-');
    }
    return `a-${code}-G`;
  }

  function iconAffiliation(icon) {
    if (!icon) return 'unknown';
    if (icon.affiliation_override) return icon.affiliation_override;
    if (icon.kind === 'custom') return affiliationFromCot(icon.type2525b || icon.cot_type);
    if (icon.kind === 'unregistered') return affiliationFromCot(icon.cot_type);
    return milAffiliation(icon);
  }

  function selectionLabel(icon) {
    if (!icon) return 'No symbol selected';
    if (icon.kind === 'custom') return titleWords(text(icon.filename).replace(/\.[^.]+$/i, '') || text(icon.iconsetpath));
    if (icon.kind === 'unregistered') return 'Unregistered custom icon';
    const name = text(icon.name);
    const readable = name
      .replace(/^(friendly|hostile|neutral|unknown)-/, '')
      .replace(/^(ground|air|sea-surface|subsurface|space|emergency)-/, '')
      .replace(/^(unit|equipment|installation|activity)-/, '');
    return titleWords(readable || icon.label || icon.sidc);
  }

  function selectionImage(icon) {
    if (!icon) return '';
    if (icon.kind === 'custom') return icon.asset_url || customAssetUrl(icon.iconsetpath);
    if (icon.kind === 'unregistered') return '';
    return `/mil2525/svg/${encodeURIComponent(text(icon.name))}.svg`;
  }

  function selectionCot(icon) {
    if (!icon) return '';
    if (icon.kind === 'custom') return customCotType(icon);
    if (icon.kind === 'unregistered') return text(icon.cot_type) || 'Protected source CoT type';
    return milCotType(icon);
  }

  function combatBranch(rest) {
    const joined = rest.join('-');
    const support = ['medical','supply','maintenance','transportation','logistics','finance','personnel','postal','legal','religious','contracting'];
    const combat = ['infantry','armor','artillery','air-defense','engineer','reconnaissance','aviation','special-forces','ranger','anti-armor','breaching'];
    if (support.some(value => joined.includes(value))) return 'Combat Service Support';
    if (combat.some(value => joined.includes(value))) return 'Combat';
    return '';
  }

  function milHierarchy(icon) {
    const parts = text(icon && icon.name).toLowerCase().split('-').filter(Boolean);
    const affiliation = AFFILIATION_LABEL[parts.shift()] || titleWords(parts.shift() || 'Unknown');
    let domain = parts.shift() || 'ground';
    const path = [affiliation];
    if (domain === 'ground') path.push('Ground Track');
    else if (domain === 'air') path.push('Air Track');
    else if (domain === 'sea' && parts[0] === 'surface') { parts.shift(); path.push('Sea Surface'); }
    else if (domain === 'subsurface') path.push('Subsurface');
    else if (domain === 'space') path.push('Space');
    else if (domain === 'emergency') path.push('Emergency');
    else path.push(titleWords(domain));
    if (parts.length) {
      const entity = parts.shift();
      path.push(titleWords(entity));
      if (domain === 'ground' && entity === 'unit') {
        const branch = combatBranch(parts);
        if (branch) path.push(branch);
      }
    }
    const phrases = [
      ['air','defense'],['anti','armor'],['special','forces'],['civil','affairs'],['psychological','operations'],
      ['mechanized','infantry'],['motorized','infantry'],['combat','engineer'],['sea','surface'],['fixed','wing'],['rotary','wing']
    ];
    let remaining = parts.slice();
    while (remaining.length) {
      let used = false;
      for (const phrase of phrases) {
        if (phrase.every((value, index) => remaining[index] === value)) {
          path.push(phrase.map(titleWords).join(' '));
          remaining = remaining.slice(phrase.length);
          used = true;
          break;
        }
      }
      if (!used) path.push(titleWords(remaining.shift()));
    }
    return path.join(' > ');
  }

  function selectionHierarchy(icon) {
    if (!icon) return '';
    if (icon.kind === 'custom') {
      return [icon.iconset_name, icon.group_name, text(icon.filename).replace(/\.[^.]+$/i, '')].filter(Boolean).map(titleWords).join(' > ');
    }
    if (icon.kind === 'unregistered') return text(icon.iconsetpath) || 'Unregistered custom icon';
    return milHierarchy(icon);
  }

  function selectionIdentity(icon) {
    if (!icon) return [];
    const affiliation = AFFILIATION_LABEL[iconAffiliation(icon)] || 'Unknown';
    if (icon.kind === 'custom') {
      const mime = text(icon.mime_type || 'image/png').split('/').pop().toUpperCase();
      const dimensions = icon.width && icon.height ? `${icon.width} × ${icon.height}` : 'Original dimensions preserved';
      return [
        ['Icon Set', text(icon.iconset_name) || 'Custom'],
        ['Icon Set UID', text(icon.iconset_uid) || '—'],
        ['Affiliation', affiliation],
        ['Group', text(icon.group_name) || 'Ungrouped'],
        ['Asset', `${mime} · ${dimensions}`],
      ];
    }
    if (icon.kind === 'unregistered') {
      return [
        ['Icon Set', 'Unregistered Custom Icon'],
        ['Icon Set UID', text(icon.iconsetpath).split('/')[0] || '—'],
        ['Affiliation', affiliation],
        ['Group', 'Source metadata protected'],
        ['Asset', 'Original source asset unavailable'],
      ];
    }
    return [
      ['Icon Set', 'TAK Map Reviewed MIL-STD-2525C'],
      ['SIDC', text(icon.sidc) || '—'],
      ['Affiliation', affiliation],
      ['Dimension', milDomain(icon)],
      ['Asset', `SVG · ${Number(icon.size || 48)} px definition`],
    ];
  }

  function normalizeMil(icon) {
    return icon ? Object.assign({}, icon, {kind:'milstd2525c'}) : null;
  }

  function iconKey(icon) {
    if (!icon) return '';
    if (icon.kind === 'custom') return `${icon.iconsetpath}|${icon.affiliation_override || ''}`;
    if (icon.kind === 'unregistered') return `unregistered|${icon.iconsetpath}`;
    return text(icon.name);
  }

  function switchMilAffiliation(icon, affiliation) {
    const base = text(icon && icon.name).replace(/^(friendly|hostile|neutral|unknown)-/i, '');
    const targetName = `${affiliation}-${base}`;
    const match = (window.v233MilIcons || []).find(row => text(row.name).toLowerCase() === targetName.toLowerCase());
    if (match) return normalizeMil(match);
    const clone = normalizeMil(icon) || {};
    clone.name = targetName;
    const sidc = text(clone.sidc).toUpperCase();
    if (sidc.length >= 2) clone.sidc = sidc.charAt(0) + (SIDC_AFFILIATION[affiliation] || 'U') + sidc.slice(2);
    const cot = milCotType(clone).split('-');
    if (cot.length > 1) cot[1] = AFFILIATION_CODE[affiliation] || 'u';
    clone.cot_type = cot.join('-');
    return clone;
  }

  function switchIconAffiliation(icon, affiliation) {
    if (!icon) return icon;
    if (icon.kind === 'custom') return Object.assign({}, icon, {affiliation_override: affiliation});
    if (icon.kind === 'unregistered') return icon;
    return switchMilAffiliation(icon, affiliation);
  }

  async function loadAliases() {
    if (state.aliasesReady) return;
    try {
      const response = await fetch(ALIAS_URL, {cache:'no-store', credentials:'same-origin'});
      const body = await apiJson(response);
      const byCot = body.by_cot_type || {};
      for (const [cot, record] of Object.entries(byCot)) {
        if (!Array.isArray(record) || !record[0]) continue;
        const name = text(record[0]).toLowerCase();
        const quality = text(record[3]);
        if (!state.cotByName.has(name) || quality.includes('original')) state.cotByName.set(name, cot);
      }
      state.aliasesReady = true;
    } catch (error) {
      state.errors.push(`Alias catalog: ${error.message || error}`);
      state.aliasesReady = true;
    }
  }

  function usableMilIcons(rows) {
    return (Array.isArray(rows) ? rows : []).filter(icon => icon && text(icon.name) && text(icon.sidc) && icon.label !== '?' && !text(icon.name).includes('placeholder'));
  }

  async function ensureMilCatalogLoaded(force) {
    const existing = usableMilIcons(window.v233MilIcons || []);
    if (!force && existing.length) {
      state.milError = '';
      return existing;
    }
    const deferred = usableMilIcons(window.__takMilStdSelectorV381 && window.__takMilStdSelectorV381.icons);
    if (!force && deferred.length) {
      window.v233MilIcons = deferred;
      state.milError = '';
      return deferred;
    }
    if (!force && state.milLoadPromise) return state.milLoadPromise;
    const promise = (async () => {
      let lastError = null;
      try {
        if (typeof window.v381LoadMilIcons === 'function') {
          const loaded = usableMilIcons(await window.v381LoadMilIcons(!!force));
          if (loaded.length) {
            window.v233MilIcons = loaded;
            state.milError = '';
            return loaded;
          }
        }
      } catch (error) { lastError = error; }
      for (const url of ['/mil2525/icons.json', '/assets/mil2525/icons.json']) {
        try {
          const response = await fetch(`${url}${url.includes('?') ? '&' : '?'}v=${encodeURIComponent(VERSION)}&cb=${Date.now()}`, {cache:'no-store', credentials:'same-origin'});
          const body = await apiJson(response);
          const loaded = usableMilIcons(body);
          if (!loaded.length) throw new Error('MIL-STD-2525C catalog was empty');
          window.v233MilIcons = loaded;
          try {
            const ctl = window.__takMilStdSelectorV381 || (window.__takMilStdSelectorV381 = {});
            ctl.icons = loaded;
            ctl.source = url;
            ctl.error = null;
          } catch (_) {}
          state.milError = '';
          return loaded;
        } catch (error) { lastError = error; }
      }
      state.milError = text(lastError && (lastError.message || lastError)) || 'MIL-STD-2525C catalog failed to load';
      throw new Error(state.milError);
    })().finally(() => { state.milLoadPromise = null; });
    state.milLoadPromise = promise;
    return promise;
  }

  async function loadSummary() {
    try {
      const response = await fetch(API, {cache:'no-store', credentials:'same-origin'});
      state.summary = await apiJson(response);
      state.ready = true;
      await loadAliases();
      renderSetRail();
      refreshMissionOptions();
      installAuthoritativeRenderers();
      redrawPointLayers('registry-ready');
      return state.summary;
    } catch (error) {
      state.errors.push(String(error));
      state.summary = {ok:false, sets:[], custom_set_count:0, custom_icon_count:0};
      state.ready = false;
      renderSetRail();
      return state.summary;
    }
  }

  async function loadCustomSet(uid) {
    if (state.customBySet.has(uid)) return state.customBySet.get(uid);
    const promise = fetch(`${API}/icons?set_uid=${encodeURIComponent(uid)}`, {cache:'no-store', credentials:'same-origin'})
      .then(apiJson)
      .then(result => {
        const icons = (result.icons || []).map(icon => Object.assign({}, icon, {kind:'custom'}));
        state.customBySet.set(uid, icons);
        for (const icon of icons) state.customByPath.set(icon.iconsetpath, icon);
        return icons;
      })
      .catch(error => { state.customBySet.delete(uid); throw error; });
    state.customBySet.set(uid, promise);
    return promise;
  }

  async function normalizedUrl(src, canvasSize, footprint) {
    const source = text(src);
    if (!source) return '';
    const key = `${source}|${canvasSize}|${footprint}`;
    if (state.normalizedCache.has(key)) return state.normalizedCache.get(key);
    const promise = (async () => {
      const response = await fetch(source, {cache:'force-cache', credentials:'same-origin'});
      if (!response.ok) throw new Error(`Icon HTTP ${response.status}`);
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      try {
        const image = await new Promise((resolve, reject) => {
          const node = new Image();
          node.onload = () => resolve(node);
          node.onerror = () => reject(new Error('Icon decode failed'));
          node.src = objectUrl;
        });
        const scanSize = 192;
        const scan = document.createElement('canvas');
        scan.width = scan.height = scanSize;
        const context = scan.getContext('2d', {willReadFrequently:true});
        const scale = Math.min(scanSize / Math.max(image.naturalWidth || image.width || 1, 1), scanSize / Math.max(image.naturalHeight || image.height || 1, 1));
        const width = Math.max(1, Math.round((image.naturalWidth || image.width || 1) * scale));
        const height = Math.max(1, Math.round((image.naturalHeight || image.height || 1) * scale));
        context.clearRect(0, 0, scanSize, scanSize);
        context.drawImage(image, Math.round((scanSize-width)/2), Math.round((scanSize-height)/2), width, height);
        const pixels = context.getImageData(0, 0, scanSize, scanSize).data;
        let minX=scanSize, minY=scanSize, maxX=-1, maxY=-1;
        for (let y=0; y<scanSize; y+=1) {
          for (let x=0; x<scanSize; x+=1) {
            if (pixels[(y*scanSize+x)*4+3] > 8) {
              if (x<minX) minX=x; if (x>maxX) maxX=x;
              if (y<minY) minY=y; if (y>maxY) maxY=y;
            }
          }
        }
        if (maxX < minX || maxY < minY) return source;
        const cropW = maxX-minX+1, cropH=maxY-minY+1;
        const target = document.createElement('canvas');
        target.width = target.height = canvasSize;
        const targetContext = target.getContext('2d');
        const targetScale = Math.min(footprint/cropW, footprint/cropH);
        const targetW = Math.max(1, Math.round(cropW*targetScale));
        const targetH = Math.max(1, Math.round(cropH*targetScale));
        targetContext.clearRect(0,0,canvasSize,canvasSize);
        targetContext.drawImage(scan,minX,minY,cropW,cropH,Math.round((canvasSize-targetW)/2),Math.round((canvasSize-targetH)/2),targetW,targetH);
        return target.toDataURL('image/png');
      } finally { URL.revokeObjectURL(objectUrl); }
    })().catch(() => source);
    state.normalizedCache.set(key, promise);
    return promise;
  }

  function normalizeImageElement(image) {
    if (!image || image.dataset.normalizing === '1' || image.dataset.normalized === '1') return;
    const src = image.dataset.iconSrc || image.getAttribute('src') || '';
    if (!src) return;
    image.dataset.normalizing = '1';
    const canvas = Number(image.dataset.canvas || 96);
    const footprint = Number(image.dataset.footprint || 72);
    normalizedUrl(src, canvas, footprint).then(url => {
      if (url) image.src = url;
      image.dataset.normalized = '1';
      image.classList.add('normalized-i556');
    }).finally(() => { delete image.dataset.normalizing; });
  }

  function scheduleNormalization(root) {
    const scope = root || document;
    const images = Array.from(scope.querySelectorAll('img[data-icon-src]'));
    const grid = byId('milGrid');
    const gridWrap = grid && grid.parentElement;
    const gridScope = scope === grid || scope === gridWrap;
    if (!gridScope || !('IntersectionObserver' in window) || !gridWrap) {
      images.slice(0, 24).forEach(normalizeImageElement);
      return;
    }
    if (!state.normalizerObserver || state.normalizerRoot !== gridWrap) {
      if (state.normalizerObserver) state.normalizerObserver.disconnect();
      state.normalizerRoot = gridWrap;
      state.normalizerObserver = new IntersectionObserver(entries => {
        for (const entry of entries) if (entry.isIntersecting) {
          state.normalizerObserver.unobserve(entry.target);
          normalizeImageElement(entry.target);
        }
      }, {root:gridWrap, rootMargin:'240px 0px'});
    }
    images.forEach(image => state.normalizerObserver.observe(image));
  }

  function iconImg(icon, canvas, footprint, className) {
    const src = selectionImage(icon);
    if (!src) return '<span class="unavailable-i556">?</span>';
    return `<img class="${esc(className || '')}" src="${esc(src)}" data-icon-src="${esc(src)}" data-canvas="${Number(canvas || 96)}" data-footprint="${Number(footprint || 72)}" alt="">`;
  }

  function addStyle() {
    if (byId('takMapIconRegistryStyleI556')) return;
    const style = document.createElement('style');
    style.id = 'takMapIconRegistryStyleI556';
    style.textContent = `
      :root{--i556-bg:#071019;--i556-panel:#0d1822;--i556-panel2:#111e29;--i556-panel3:#152430;--i556-line:#35434f;--i556-line2:#53616d;--i556-text:#edf1f4;--i556-muted:#9ea9b3;--i556-silver:#c8cfd5;--i556-silver2:#a8b1ba}
      #milPicker.mil-picker{position:fixed!important;inset:12px!important;width:auto!important;height:auto!important;max-width:1560px!important;max-height:860px!important;margin:auto!important;transform:none!important;display:none!important;grid-template-rows:58px minmax(0,1fr) 58px!important;overflow:hidden!important;border:1px solid #596671!important;border-radius:14px!important;background:linear-gradient(180deg,#111e29,#09131c)!important;color:var(--i556-text)!important;box-shadow:0 28px 88px rgba(0,0,0,.68)!important;z-index:2147483300!important}
      #milPicker.mil-picker.active{display:grid!important}
      #milPicker .registry-head-i556{display:flex;align-items:center;gap:11px;padding:0 15px;border-bottom:1px solid var(--i556-line);background:linear-gradient(180deg,#15232f,#0f1a24)}
      #milPicker .registry-head-icon-i556{width:34px;height:34px;display:grid;place-items:center;border:1px solid #65727d;border-radius:9px;background:#1b2833;color:#e3e7ea;font-weight:900}
      #milPicker .registry-title-i556{font-size:17px;font-weight:850;letter-spacing:.035em}.registry-subtitle-i556{margin-top:1px;color:#909ba5;font-size:9px;text-transform:uppercase;letter-spacing:.08em}
      #milPicker .registry-close-i556{width:36px;height:36px;margin-left:auto;border:1px solid #4d5b67;border-radius:8px;background:#111c25;color:#d7dde1;font-size:21px;cursor:pointer}
      #milPicker .registry-layout-i556{display:grid;grid-template-columns:220px minmax(0,1fr) 248px;height:100%;min-height:0;overflow:hidden}
      #milPicker .set-rail-i556{min-width:0;overflow:auto;border-right:1px solid var(--i556-line);background:#0a151e;padding:10px}
      #milPicker .rail-label-i556,#milPicker .section-label-i556{color:#919da7;font-size:9px;font-weight:850;letter-spacing:.09em;text-transform:uppercase}
      #milPicker .set-list-i556{display:flex;flex-direction:column;gap:5px;margin-top:8px}
      #milPicker .set-button-i556{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:7px;align-items:center;width:100%;min-height:42px;padding:7px 9px;border:1px solid #34434f;border-radius:8px;background:#101c26;color:#cbd2d7;text-align:left;cursor:pointer}
      #milPicker .set-button-i556:hover{border-color:#7c8791;background:#1a2732}.set-button-i556.active{border-color:#e0e4e7!important;background:#c8cfd5!important;color:#111920!important}
      #milPicker .set-name-i556{overflow:hidden;font-size:10px;font-weight:800;text-overflow:ellipsis;white-space:nowrap}.set-count-i556{font-size:8px;opacity:.75}
      #milPicker .registry-main-i556{display:grid;grid-template-rows:auto minmax(0,1fr);min-width:0;min-height:0;background:#0c1720}
      #milPicker .registry-controls-i556{padding:10px;border-bottom:1px solid var(--i556-line);background:#101c26}
      #milPicker .search-row-i556{display:grid;grid-template-columns:minmax(180px,1fr) minmax(150px,220px);gap:8px}
      #milPicker .registry-search-i556,#milPicker .registry-group-select-i556{width:100%;height:38px;border:1px solid #475563;border-radius:9px;outline:none;background:#09131c;color:#edf1f4;padding:0 10px;font-size:11px}
      #milPicker .registry-search-i556:focus,#milPicker .registry-group-select-i556:focus{border-color:#c5ccd2;box-shadow:0 0 0 2px rgba(197,204,210,.12)}
      #milPicker .filter-row-i556{display:flex;align-items:center;gap:5px;margin-top:7px;overflow-x:auto;padding-bottom:1px}
      #milPicker .filter-chip-i556{flex:0 0 auto;min-height:28px;padding:0 9px;border:1px solid #45535f;border-radius:999px;background:#111c25;color:#bdc6cd;font-size:9px;font-weight:800;cursor:pointer}.filter-chip-i556:hover{background:#1c2934}.filter-chip-i556.active{border-color:#e1e5e8;background:#c8cfd5;color:#111920}
      #milPicker .registry-grid-wrap-i556{min-width:0;min-height:0;overflow:auto;padding:9px}
      #milPicker .registry-grid-i556{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:7px;align-content:start}
      #milPicker .icon-card-i556{min-width:0;height:128px;padding:6px 5px;border:1px solid #354450;border-radius:9px;background:linear-gradient(180deg,#14212b,#0d1821);color:#e1e6e9;cursor:pointer;overflow:hidden}.icon-card-i556:hover{border-color:#8e99a2;background:linear-gradient(180deg,#1d2a35,#121e28)}.icon-card-i556.selected{border-color:#e2e6e9;box-shadow:0 0 0 1px rgba(218,224,229,.25);background:#202d38}
      #milPicker .icon-stage-i556{width:96px;height:96px;max-width:100%;margin:0 auto 4px;display:grid;place-items:center;border:1px solid #33414d;border-radius:8px;background:linear-gradient(135deg,rgba(255,255,255,.025) 25%,transparent 25%) 0 0/14px 14px,linear-gradient(315deg,rgba(255,255,255,.025) 25%,transparent 25%) 0 0/14px 14px,#09131c}.icon-stage-i556 img{width:96px;height:96px;object-fit:contain;opacity:.12;transition:opacity .12s ease}.icon-stage-i556 img.normalized-i556{opacity:1}
      #milPicker .icon-card-label-i556{display:block;overflow:hidden;color:#dde3e7;font-size:8px;font-weight:800;line-height:1.15;text-align:center;text-overflow:ellipsis;white-space:nowrap}
      #milPicker .registry-empty-i556{grid-column:1/-1;padding:28px;border:1px dashed #46545f;border-radius:10px;color:#9ca7b0;text-align:center}
      #milPicker .registry-inspector-i556{min-width:0;overflow:auto;border-left:1px solid var(--i556-line);background:#0a151e;padding:10px;scrollbar-width:thin}
      #milPicker .summary-hero-i556{display:grid;grid-template-columns:80px minmax(0,1fr);gap:10px;align-items:start;margin-top:8px;padding:9px;border:1px solid #3d4a56;border-radius:10px;background:linear-gradient(145deg,#172530,#101b24)}
      #milPicker .summary-stage-i556{width:76px;height:76px;display:grid;place-items:center;border:1px solid #33414d;border-radius:8px;background:#09131c}.summary-stage-i556 img{width:76px;height:76px;object-fit:contain;opacity:.12}.summary-stage-i556 img.normalized-i556{opacity:1}
      #milPicker .summary-copy-i556{min-width:0}.summary-name-i556{margin:1px 0 7px;font-size:15px;font-weight:850;line-height:1.08}.hero-field-i556{min-width:0;margin-top:5px}.hero-label-i556{display:block;margin-bottom:2px;color:#909ba5;font-size:8px;font-weight:850;letter-spacing:.08em;text-transform:uppercase}.hero-cot-i556{display:block;overflow:hidden;color:#e3e7ea;font:10px/1.25 Consolas,monospace;text-overflow:ellipsis;white-space:nowrap}.hero-path-i556{display:-webkit-box;overflow:hidden;color:#c1c8ce;font-size:9px;line-height:1.28;overflow-wrap:anywhere;-webkit-box-orient:vertical;-webkit-line-clamp:3}
      #milPicker .inspector-block-i556{margin-top:10px;border:1px solid #364550;border-radius:9px;overflow:hidden;background:#0d1821}.inspector-block-title-i556{display:flex;align-items:center;justify-content:space-between;padding:8px 9px;border-bottom:1px solid #33414d;background:#15212b;color:#cbd1d6;font-size:9px;font-weight:850;letter-spacing:.08em;text-transform:uppercase}.identity-row-i556{display:grid;grid-template-columns:72px minmax(0,1fr);gap:8px;padding:7px 9px;border-bottom:1px solid #263540;font-size:9px}.identity-row-i556:last-child{border-bottom:0}.identity-row-i556 span{color:#929da7}.identity-row-i556 strong{color:#e3e7ea;font-weight:750;overflow-wrap:anywhere}
      #milPicker .related-count-i556{color:#8f9aa4;font-size:8px;font-weight:750;letter-spacing:.04em;text-transform:none}.related-grid-i556{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:5px;padding:7px}.related-card-i556{min-width:0;padding:4px 3px 5px;border:1px solid #3a4854;border-radius:8px;background:linear-gradient(180deg,#14212b,#0d1821);color:#e3e7ea;text-align:center;cursor:pointer}.related-card-i556:hover{border-color:#8e99a2;background:linear-gradient(180deg,#1d2a35,#121e28)}.related-card-i556.active{border-color:#e1e5e8;box-shadow:0 0 0 1px rgba(214,220,225,.2);background:#202d38}.related-stage-i556{width:48px;height:48px;margin:0 auto 4px;display:grid;place-items:center;border:1px solid #33414d;border-radius:7px;background:#09131c}.related-stage-i556 img{width:48px;height:48px;object-fit:contain;opacity:.12}.related-stage-i556 img.normalized-i556{opacity:1}.related-name-i556{display:block;overflow:hidden;color:#e0e5e8;font-size:8px;font-weight:850;line-height:1.1;text-overflow:ellipsis;white-space:nowrap}.related-meta-i556{display:block;margin-top:2px;overflow:hidden;color:#8f9aa4;font-size:7px;line-height:1.1;text-overflow:ellipsis;white-space:nowrap}.related-divider-i556{grid-column:1/-1;height:1px;margin:1px 0;background:#2b3944}
      #milPicker .registry-foot-i556{display:flex;align-items:center;gap:8px;padding:9px 13px;border-top:1px solid var(--i556-line);background:#0b151e}.registry-foot-status-i556{min-width:0;flex:1;color:#9ca7b0;font-size:9px}.registry-button-i556{min-height:38px;padding:0 14px;border:1px solid #566471;border-radius:9px;background:#15212c;color:#edf1f4;font-weight:850;cursor:pointer}.registry-button-i556:hover{background:#202d39}.registry-button-i556.primary{color:#111920;border-color:#e5e8eb;background:linear-gradient(180deg,#e1e5e8,#aeb7c0)}.registry-button-i556:disabled{opacity:.4;cursor:not-allowed}
      .unavailable-i556{display:grid;place-items:center;width:48px;height:48px;border:2px dashed #77838d;border-radius:8px;color:#e2e6e9;font-weight:900}
      .tak-custom-icon-i556{display:flex;align-items:center;justify-content:center;width:38px;height:40px}.tak-custom-icon-i556 img{max-width:38px;max-height:38px;width:auto;height:auto;object-fit:contain;filter:none!important;transform:none!important}.tak-custom-unavailable-i556{display:flex;align-items:center;justify-content:center;width:36px;height:38px;border:2px dashed #a7adb4;border-radius:8px;background:rgba(7,11,15,.88);color:#e8edf0;font:800 13px/1 system-ui,Arial}
      .popup-edit-i556{display:flex;gap:7px;margin-top:10px}.popup-edit-i556 button{width:100%;border:1px solid rgba(210,220,228,.35);border-radius:9px;background:rgba(210,220,228,.08);color:#edf3f6;padding:7px 9px;font-weight:700;cursor:pointer}
      #pointEditPanel.point-window-i556{position:fixed!important;top:82px!important;left:28px!important;right:auto!important;bottom:auto!important;width:min(468px,calc(100vw - 28px))!important;max-height:calc(100vh - 105px)!important;overflow:auto!important;padding:0!important;border:1px solid #586570!important;border-radius:14px!important;background:linear-gradient(180deg,rgba(17,29,40,.985),rgba(8,16,24,.99))!important;box-shadow:0 24px 72px rgba(0,0,0,.58),inset 0 1px rgba(255,255,255,.04)!important;color:#edf1f4!important;z-index:2147483000!important}
      #pointEditPanel.point-window-i556 .point-head-i556,#takMapPointEditorI556 .point-head-i556{min-height:58px;display:flex;align-items:center;gap:11px;padding:0 14px;border-bottom:1px solid #35434f;background:linear-gradient(180deg,#14212c,#0e1821)}.point-head-icon-i556{width:32px;height:32px;display:grid;place-items:center;border:1px solid #66727d;border-radius:8px;background:#1b2833;color:#e4e7ea;font-weight:900}.point-title-i556{font-size:17px;font-weight:850;letter-spacing:.035em}.point-subtitle-i556{margin-top:1px;color:#909ba5;font-size:9px;text-transform:uppercase;letter-spacing:.08em}.point-close-i556{width:35px;height:35px;margin-left:auto;border:1px solid #4c5a66;border-radius:8px;background:#111c25;color:#d6dce1;font-size:21px;cursor:pointer}
      #pointEditPanel .point-body-i556,#takMapPointEditorI556 .point-body-i556{display:flex;flex-direction:column;gap:11px;padding:13px}.point-source-strip-i556{display:grid;grid-template-columns:34px minmax(0,1fr) auto;gap:9px;align-items:center;padding:9px 10px;border:1px solid #3c4a56;border-radius:9px;background:linear-gradient(145deg,#17242f,#101a23)}.point-source-icon-i556{width:32px;height:32px;display:grid;place-items:center;border:1px solid #596673;border-radius:8px;color:#d8dde1;font-weight:900}.point-source-title-i556{font-size:12px;font-weight:800}.point-source-meta-i556{margin-top:2px;overflow:hidden;color:#97a2ac;font:9px/1.3 Consolas,monospace;text-overflow:ellipsis;white-space:nowrap}.point-source-state-i556{display:inline-flex;align-items:center;gap:5px;color:#bac3ca;font-size:8px;font-weight:800;letter-spacing:.04em;text-transform:uppercase}.point-source-state-i556:before{content:'';width:7px;height:7px;border:1px solid #d7dde1;border-radius:50%;background:#9da8b1}
      .point-form-grid-i556{display:grid;grid-template-columns:1fr 1fr;gap:10px}.point-field-i556{min-width:0}.point-field-i556.wide{grid-column:1/-1}.point-field-i556 label,.point-field-label-i556{display:block;margin:0 0 4px;color:#a8b1b9;font-size:9px;font-weight:850;letter-spacing:.07em;text-transform:uppercase}.point-control-i556{box-sizing:border-box;width:100%;min-width:0;height:39px;border:1px solid #475563;border-radius:9px;outline:none;background:#0b151e;color:#edf1f4;padding:0 11px;font-size:12px}.point-control-i556:focus{border-color:#c4cbd1;box-shadow:0 0 0 2px rgba(196,203,209,.12)}textarea.point-control-i556{min-height:76px;height:auto;padding:9px 11px;resize:vertical;line-height:1.35}.point-control-i556.invalid{border-color:#765858;box-shadow:0 0 0 2px rgba(118,88,88,.14)}.point-help-i556{display:flex;justify-content:space-between;gap:10px;margin-top:4px;color:#85919b;font-size:8px}.point-location-error-i556{color:#d5bdbd}
      .point-symbol-card-i556{display:grid;grid-template-columns:90px minmax(0,1fr) auto;gap:11px;align-items:center;padding:9px;border:1px solid #3b4955;border-radius:10px;background:linear-gradient(145deg,#172530,#101b24)}.point-symbol-stage-i556{width:86px;height:86px;display:grid;place-items:center;border:1px solid #33424e;border-radius:8px;background:#09131c}.point-symbol-stage-i556 img{width:86px;height:86px;object-fit:contain;opacity:.12}.point-symbol-stage-i556 img.normalized-i556{opacity:1}.point-symbol-name-i556{font-size:14px;font-weight:850}.point-symbol-cot-i556{margin-top:4px;color:#c5ccd2;font:10px/1.25 Consolas,monospace}.point-symbol-path-i556{display:-webkit-box;margin-top:4px;overflow:hidden;color:#929da7;font-size:9px;line-height:1.3;-webkit-box-orient:vertical;-webkit-line-clamp:2}.point-symbol-button-i556{min-height:37px;padding:0 11px;border:1px solid #626f7a;border-radius:8px;background:#18242e;color:#e2e6e9;font-size:10px;font-weight:850;cursor:pointer}.point-symbol-button-i556:hover{background:#26333e}.point-symbol-button-i556:disabled{opacity:.42;cursor:not-allowed}
      .point-destination-i556{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:10px;border:1px solid #34434f;border-radius:10px;background:#0d1821}.point-destination-i556 .wide{grid-column:1/-1}.point-mission-field-i556[hidden]{display:none!important}.point-status-i556{display:flex;min-height:35px;align-items:center;gap:8px;padding:8px 10px;border:1px solid #52606b;border-radius:8px;background:#151f28;color:#c1c9cf;font-size:9px}.point-status-i556:before{content:'';flex:0 0 auto;width:8px;height:8px;border:1px solid #d7dde1;border-radius:50%;background:#9da8b1}.point-status-i556.error{border-color:#765858;color:#d5bdbd}.point-status-i556.ok{border-color:#5b7167;color:#bcd5c8}.point-actions-i556{min-height:64px;display:flex;align-items:center;gap:9px;padding:11px 14px;border-top:1px solid #35434f;background:#0b151e}.point-action-spacer-i556{flex:1}.point-button-i556{min-height:39px;padding:0 15px;border:1px solid #566471;border-radius:9px;background:#15212c;color:#edf1f4;font-weight:850;cursor:pointer}.point-button-i556:hover{background:#202d39}.point-button-i556.ghost{background:transparent}.point-button-i556.primary{color:#111920;border-color:#e5e8eb;background:linear-gradient(180deg,#e1e5e8,#aeb7c0)}.point-button-i556:disabled{opacity:.4;cursor:not-allowed}
      #takMapPointEditorI556{position:fixed;inset:0;z-index:2147483400;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,.58);padding:18px}#takMapPointEditorI556.active{display:flex}#takMapPointEditorI556 .point-editor-card-i556{width:min(468px,calc(100vw - 28px));max-height:calc(100vh - 36px);overflow:auto;border:1px solid #586570;border-radius:14px;background:linear-gradient(180deg,rgba(17,29,40,.995),rgba(8,16,24,.995));box-shadow:0 26px 74px rgba(0,0,0,.65);color:#edf1f4}.unsaved-badge-i556{display:none;min-height:24px;align-items:center;padding:2px 8px;border:1px solid #717d87;border-radius:999px;background:#202c36;color:#d7dde1;font-size:8px;font-weight:850;letter-spacing:.05em;text-transform:uppercase}.unsaved-badge-i556.visible{display:inline-flex}
      #pointMiniToolbar .tool-color{display:none!important}
      .leaflet-popup-content:has(.point-info-popup-i556){margin:0!important;width:auto!important}.leaflet-popup-content-wrapper:has(.point-info-popup-i556){padding:0!important;overflow:hidden!important;border:1px solid #596671!important;border-radius:14px!important;background:linear-gradient(180deg,#111e29,#09131c)!important;color:#edf1f4!important;box-shadow:0 18px 46px rgba(0,0,0,.58)!important}.leaflet-popup-tip-container:has(+ *){filter:none}.leaflet-popup:has(.point-info-popup-i556) .leaflet-popup-tip{background:#0b151e!important}.leaflet-popup:has(.point-info-popup-i556) .leaflet-popup-close-button{top:8px!important;right:8px!important;width:27px!important;height:27px!important;display:grid!important;place-items:center!important;border:1px solid #53616d!important;border-radius:999px!important;background:#111c25!important;color:#dbe0e4!important;font-size:20px!important;line-height:1!important;z-index:3!important}
      .point-info-popup-i556{width:360px;max-width:min(360px,calc(100vw - 42px));overflow:hidden;background:linear-gradient(180deg,#111e29,#09131c);color:#edf1f4}.point-popup-head-i556{display:grid;grid-template-columns:78px minmax(0,1fr);gap:11px;align-items:center;padding:13px 44px 11px 13px;border-bottom:1px solid #35434f;background:linear-gradient(180deg,#14212c,#0e1821)}.point-popup-stage-i556{width:74px;height:74px;display:grid;place-items:center;border:1px solid #3a4854;border-radius:9px;background:#07121a}.point-popup-stage-i556 img{width:72px;height:72px;object-fit:contain}.point-popup-stage-i556 .point-popup-unavailable-i556{display:grid;place-items:center;width:56px;height:56px;border:2px dashed #7c8791;border-radius:8px;color:#dce1e5;font-weight:900}.point-popup-title-i556{overflow:hidden;font-size:17px;font-weight:900;line-height:1.08;text-overflow:ellipsis;white-space:nowrap}.point-popup-subtitle-i556{margin-top:3px;color:#9da8b1;font-size:9px;font-weight:800;letter-spacing:.06em;text-transform:uppercase}.point-popup-cot-i556{margin-top:6px;color:#d7dde1;font:10px/1.2 Consolas,monospace}.point-popup-path-i556{display:-webkit-box;margin-top:3px;overflow:hidden;color:#aab4bc;font-size:9px;line-height:1.25;-webkit-box-orient:vertical;-webkit-line-clamp:3}.point-popup-body-i556{padding:9px 12px 11px}.point-popup-grid-i556{display:grid;grid-template-columns:82px minmax(0,1fr);border:1px solid #34434f;border-radius:9px;overflow:hidden;background:#0d1821}.point-popup-label-i556,.point-popup-value-i556{padding:7px 9px;border-bottom:1px solid #283741;font-size:9px;line-height:1.3}.point-popup-label-i556{color:#929da7;font-weight:850;letter-spacing:.04em;text-transform:uppercase}.point-popup-value-i556{color:#e0e5e8;overflow-wrap:anywhere}.point-popup-grid-i556>:nth-last-child(-n+2){border-bottom:0}.point-popup-notes-i556{white-space:pre-wrap}.point-popup-actions-i556{display:flex;margin-top:9px}.point-popup-edit-i556{width:100%;min-height:37px;border:1px solid #e2e6e9;border-radius:9px;background:linear-gradient(180deg,#e1e5e8,#aeb7c0);color:#111920;font-weight:900;cursor:pointer}.point-popup-edit-i556:hover{filter:brightness(1.06)}
      @media(max-width:1260px){#milPicker .registry-layout-i556{grid-template-columns:190px minmax(0,1fr) 238px}#milPicker .registry-grid-i556{grid-template-columns:repeat(6,minmax(0,1fr))}}
      @media(max-width:920px){#milPicker .registry-layout-i556{grid-template-columns:160px minmax(0,1fr)}#milPicker .registry-inspector-i556{display:none}#milPicker .registry-grid-i556{grid-template-columns:repeat(5,minmax(0,1fr))}}
      @media(max-width:650px){#milPicker.mil-picker{inset:7px!important}#milPicker .registry-layout-i556{grid-template-columns:118px minmax(0,1fr)}#milPicker .registry-grid-i556{grid-template-columns:repeat(2,minmax(0,1fr))}#milPicker .search-row-i556{grid-template-columns:1fr}#pointEditPanel.point-window-i556{left:14px!important;top:72px!important}.point-form-grid-i556,.point-destination-i556{grid-template-columns:1fr}.point-field-i556.wide,.point-destination-i556 .wide{grid-column:auto}.point-symbol-card-i556{grid-template-columns:74px minmax(0,1fr)}.point-symbol-stage-i556{width:70px;height:70px}.point-symbol-stage-i556 img{width:70px;height:70px}.point-symbol-button-i556{grid-column:1/-1}}
    `;
    document.head.appendChild(style);
  }

  function ensureRegistryModal() {
    const picker = byId('milPicker');
    if (!picker) return false;
    if (picker.dataset.i556Registry === '1') return true;
    picker.dataset.i556Registry = '1';
    picker.innerHTML = `
      <header class="registry-head-i556">
        <span class="registry-head-icon-i556">T</span>
        <div><div class="registry-title-i556">TAK Icon Registry</div><div class="registry-subtitle-i556">Reviewed MIL-STD-2525C and registered ATAK icon sets</div></div>
        <button type="button" class="registry-close-i556" id="registryCloseI556" aria-label="Close">×</button>
      </header>
      <div class="registry-layout-i556">
        <aside class="set-rail-i556"><div class="rail-label-i556">Icon Sets</div><div class="set-list-i556" id="registrySetListI556"></div></aside>
        <main class="registry-main-i556">
          <div class="registry-controls-i556">
            <div class="search-row-i556"><input class="registry-search-i556" id="milSearch" placeholder="Search names, SIDCs, paths, or groups…"><select class="registry-group-select-i556" id="registryGroupI556"><option value="">All groups</option></select></div>
            <div class="filter-row-i556" id="registryFilterRowI556"></div>
          </div>
          <div class="registry-grid-wrap-i556"><div class="registry-grid-i556" id="milGrid"></div></div>
        </main>
        <aside class="registry-inspector-i556" id="registryInspectorI556"></aside>
      </div>
      <footer class="registry-foot-i556"><div class="registry-foot-status-i556" id="registryFootStatusI556">Select a symbol.</div><button type="button" class="registry-button-i556" id="registryClearI556">Clear</button><button type="button" class="registry-button-i556" id="registryCancelI556">Cancel</button><button type="button" class="registry-button-i556 primary" id="registryApplyI556" disabled>Use Selected Symbol</button></footer>`;
    byId('registryCloseI556').addEventListener('click', closePicker);
    byId('registryCancelI556').addEventListener('click', closePicker);
    byId('registryClearI556').addEventListener('click', clearPickerSelection);
    byId('registryApplyI556').addEventListener('click', applyPickerSelection);
    byId('milSearch').addEventListener('input', renderPicker);
    byId('registryGroupI556').addEventListener('change', event => { state.activeGroup = event.target.value || ''; renderPicker(); });
    picker.addEventListener('click', event => { if (event.target === picker) closePicker(); });
    renderSetRail();
    return true;
  }

  function renderSetRail() {
    if (!ensureRegistryModal()) return;
    const node = byId('registrySetListI556');
    if (!node) return;
    const sets = [{uid:'milstd2525c',name:'MIL-STD-2525C',icon_count:(window.v233MilIcons || []).length || 1448}]
      .concat(((state.summary && state.summary.sets) || []).map(set => ({uid:set.uid,name:set.name,icon_count:set.icon_count})));
    node.innerHTML = sets.map(set => `<button type="button" class="set-button-i556 ${state.activeSet === set.uid ? 'active' : ''}" data-set-uid="${esc(set.uid)}"><span class="set-name-i556">${esc(set.name)}</span><span class="set-count-i556">${Number(set.icon_count || 0).toLocaleString()}</span></button>`).join('');
    node.querySelectorAll('[data-set-uid]').forEach(button => button.addEventListener('click', () => {
      state.activeSet = button.dataset.setUid || 'milstd2525c';
      state.activeGroup = '';
      renderSetRail();
      renderPicker();
    }));
  }

  function renderFilters(groups) {
    const select = byId('registryGroupI556');
    if (select) {
      const options = ['<option value="">All groups</option>'].concat((groups || []).map(group => `<option value="${esc(group)}">${esc(titleWords(group))}</option>`));
      select.innerHTML = options.join('');
      select.value = state.activeGroup;
    }
    const row = byId('registryFilterRowI556');
    if (!row) return;
    if (state.activeSet === 'milstd2525c') {
      const affiliation = AFFILIATIONS.map(value => `<button type="button" class="filter-chip-i556 ${state.activeAffiliation === value ? 'active' : ''}" data-affiliation="${value}">${AFFILIATION_LABEL[value]}</button>`).join('');
      const domains = ['Ground','Air','Sea Surface','Subsurface','Space','Emergency'].map(value => `<button type="button" class="filter-chip-i556 ${state.activeDomain === value ? 'active' : ''}" data-domain="${esc(value)}">${esc(value)}</button>`).join('');
      row.innerHTML = affiliation + '<span style="width:5px;flex:0 0 auto"></span>' + domains;
      row.querySelectorAll('[data-affiliation]').forEach(button => button.addEventListener('click', () => { state.activeAffiliation = button.dataset.affiliation; state.activeGroup=''; renderPicker(); }));
      row.querySelectorAll('[data-domain]').forEach(button => button.addEventListener('click', () => { state.activeDomain = button.dataset.domain; state.activeGroup=''; renderPicker(); }));
    } else row.innerHTML = '<span class="registry-subtitle-i556">Registered ATAK custom icon set · exact icon-set UID/group/filename identity preserved</span>';
  }

  function chosenFromPointState() {
    try {
      const icon = window.v233PointState && window.v233PointState.icon;
      if (!icon) return null;
      return icon.kind === 'custom' ? icon : normalizeMil(icon);
    } catch (_) { return null; }
  }

  function setActiveFromSelection(icon) {
    if (icon && icon.kind === 'custom') {
      state.activeSet = icon.iconset_uid;
      state.activeGroup = icon.group_name || '';
    } else {
      state.activeSet = 'milstd2525c';
      state.activeAffiliation = icon ? iconAffiliation(icon) : 'friendly';
      state.activeDomain = icon ? milDomain(icon) : 'Ground';
      state.activeGroup = '';
    }
  }

  function openPicker(target, initial) {
    if (!ensureRegistryModal()) return;
    state.pickerTarget = target || 'point';
    state.selected = initial || (target === 'editor' ? state.editorSymbol : chosenFromPointState()) || null;
    setActiveFromSelection(state.selected);
    renderSetRail();
    const picker = byId('milPicker');
    if (picker) picker.classList.add('active');
    renderPicker();
  }

  function closePicker() {
    const picker = byId('milPicker');
    if (picker) picker.classList.remove('active');
  }

  function cardHtml(icon) {
    const selected = iconKey(icon) === iconKey(state.selected);
    return `<button type="button" class="icon-card-i556 ${selected ? 'selected' : ''}" data-icon-key="${esc(iconKey(icon))}" title="${esc(selectionHierarchy(icon))}"><span class="icon-stage-i556">${iconImg(icon,96,72)}</span><span class="icon-card-label-i556">${esc(selectionLabel(icon))}</span></button>`;
  }

  function bindGridCards(list) {
    const grid = byId('milGrid');
    if (!grid) return;
    grid.querySelectorAll('[data-icon-key]').forEach(button => button.addEventListener('click', () => {
      state.selected = list.find(icon => iconKey(icon) === button.dataset.iconKey) || null;
      renderGridSelection();
      renderInspector();
    }));
    scheduleNormalization(grid);
  }

  function renderGridSelection() {
    const key = iconKey(state.selected);
    document.querySelectorAll('#milGrid [data-icon-key]').forEach(button => button.classList.toggle('selected', button.dataset.iconKey === key));
    const apply = byId('registryApplyI556');
    if (apply) apply.disabled = !state.selected;
    const status = byId('registryFootStatusI556');
    if (status) status.textContent = state.selected ? `${selectionLabel(state.selected)} · ${selectionCot(state.selected)}` : 'Select a symbol.';
  }

  function renderMilPicker() {
    const icons = usableMilIcons(window.v233MilIcons || []).map(normalizeMil);
    if (!icons.length) {
      renderFilters([]);
      const grid = byId('milGrid');
      if (grid) grid.innerHTML = `<div class="registry-empty-i556">${state.milError ? `Could not load MIL-STD-2525C: ${esc(state.milError)} <button type="button" class="registry-button-i556" data-mil-retry-i564="1">Retry</button>` : 'Loading MIL-STD-2525C icon set…'}</div>`;
      const retry = grid && grid.querySelector('[data-mil-retry-i564]');
      if (retry) retry.addEventListener('click', () => { state.milError=''; renderMilPicker(); void ensureMilCatalogLoaded(true).then(() => { renderSetRail(); renderMilPicker(); }).catch(() => renderMilPicker()); });
      const status = byId('registryFootStatusI556');
      if (status) status.textContent = state.milError || 'Loading 1,448 reviewed symbols…';
      renderInspector();
      if (!state.milLoadPromise && !state.milError) void ensureMilCatalogLoaded(false).then(() => { if (state.activeSet === 'milstd2525c') { renderSetRail(); renderMilPicker(); } }).catch(() => { if (state.activeSet === 'milstd2525c') renderMilPicker(); });
      return;
    }
    const query = text(byId('milSearch') && byId('milSearch').value).toLowerCase();
    const groups = Array.from(new Set(icons.filter(icon => milAffiliation(icon) === state.activeAffiliation && milDomain(icon) === state.activeDomain).map(milCategory))).sort((a,b)=>a.localeCompare(b));
    if (state.activeGroup && !groups.includes(state.activeGroup)) state.activeGroup = '';
    renderFilters(groups);
    let list = icons.filter(icon => milAffiliation(icon) === state.activeAffiliation && milDomain(icon) === state.activeDomain && (!state.activeGroup || milCategory(icon) === state.activeGroup));
    if (query) list = list.filter(icon => text([icon.name,icon.label,icon.sidc,milCotType(icon),milHierarchy(icon)].join(' ')).toLowerCase().includes(query));
    list = list.slice(0, 480);
    const grid = byId('milGrid');
    if (grid) grid.innerHTML = list.length ? list.map(cardHtml).join('') : '<div class="registry-empty-i556">No reviewed symbols match this search.</div>';
    bindGridCards(list);
    const status = byId('registryFootStatusI556');
    if (status && !state.selected) status.textContent = `${list.length.toLocaleString()} reviewed symbols shown.`;
    renderInspector();
  }

  async function renderCustomPicker(setUid) {
    const grid = byId('milGrid');
    if (grid) grid.innerHTML = '<div class="registry-empty-i556">Loading icon set…</div>';
    try {
      const icons = await loadCustomSet(setUid);
      if (state.activeSet !== setUid) return;
      const query = text(byId('milSearch') && byId('milSearch').value).toLowerCase();
      const groups = Array.from(new Set(icons.map(icon => icon.group_name || 'Ungrouped'))).sort((a,b)=>a.localeCompare(b));
      if (state.activeGroup && !groups.includes(state.activeGroup)) state.activeGroup = '';
      renderFilters(groups);
      let list = icons.filter(icon => !state.activeGroup || icon.group_name === state.activeGroup);
      if (query) list = list.filter(icon => text([icon.filename,icon.group_name,icon.iconset_name,icon.iconsetpath,icon.type2525b].join(' ')).toLowerCase().includes(query));
      list = list.slice(0, 480);
      if (grid) grid.innerHTML = list.length ? list.map(cardHtml).join('') : '<div class="registry-empty-i556">No registered custom icons match this search.</div>';
      bindGridCards(list);
      const status = byId('registryFootStatusI556');
      if (status && !state.selected) status.textContent = `${list.length.toLocaleString()} registered custom icons shown.`;
      renderInspector();
    } catch (error) {
      if (grid) grid.innerHTML = `<div class="registry-empty-i556">Could not load this icon set: ${esc(error.message || error)}</div>`;
      renderInspector();
    }
  }

  function renderPicker() {
    if (!ensureRegistryModal()) return;
    renderSetRail();
    if (state.activeSet === 'milstd2525c') renderMilPicker();
    else void renderCustomPicker(state.activeSet);
  }

  function relatedCandidates(icon) {
    if (!icon) return [];
    const affiliation = iconAffiliation(icon);
    const variantOrder = ['hostile','neutral','unknown','friendly'].filter(value => value !== affiliation).slice(0,3);
    const variants = variantOrder.map(value => switchIconAffiliation(icon, value));
    let nearby = [];
    if (icon.kind === 'custom') {
      const rows = state.customBySet.get(icon.iconset_uid);
      const list = Array.isArray(rows) ? rows : [];
      nearby = list.filter(row => row.iconsetpath !== icon.iconsetpath && row.group_name === icon.group_name).slice(0,9).map(row => Object.assign({}, row, {affiliation_override: affiliation}));
      if (nearby.length < 9) nearby = nearby.concat(list.filter(row => row.iconsetpath !== icon.iconsetpath && !nearby.some(item => item.iconsetpath === row.iconsetpath)).slice(0,9-nearby.length).map(row => Object.assign({}, row, {affiliation_override: affiliation})));
    } else if (icon.kind !== 'unregistered') {
      const icons = (window.v233MilIcons || []).map(normalizeMil);
      const category = milCategory(icon);
      const sameAff = icons.filter(row => milAffiliation(row) === affiliation && row.name !== icon.name);
      const scored = sameAff.map((row,index) => {
        let score = milCategory(row) === category ? 100 : (milDomain(row) === milDomain(icon) ? 25 : 0);
        const raw = text(row.name).toLowerCase();
        ['infantry','mechanized','motorized','airborne','engineer','reconnaissance','special-forces','medical','headquarters'].forEach((term,rank) => { if (raw.includes(term)) score += 18-rank; });
        return {row,score,index};
      }).sort((a,b)=>b.score-a.score || a.index-b.index);
      nearby = scored.map(item => item.row).filter(row => !variants.some(variant => variant.name === row.name)).slice(0,9);
    }
    return variants.concat(nearby).slice(0,12);
  }

  function renderInspector() {
    const node = byId('registryInspectorI556');
    if (!node) return;
    const icon = state.selected;
    if (!icon) {
      node.innerHTML = '<div class="section-label-i556">Selected Symbol</div><div class="registry-empty-i556" style="margin-top:9px;padding:20px 10px">Select an icon to inspect its identity and related options.</div>';
      renderGridSelection();
      return;
    }
    const identity = selectionIdentity(icon);
    const related = relatedCandidates(icon);
    const variantCount = Math.min(3, related.length);
    node.innerHTML = `
      <div class="section-label-i556">Selected Symbol</div>
      <div class="summary-hero-i556"><div class="summary-stage-i556">${iconImg(icon,128,96)}</div><div class="summary-copy-i556"><div class="summary-name-i556">${esc(selectionLabel(icon))}</div><div class="hero-field-i556"><span class="hero-label-i556">CoT Type</span><code class="hero-cot-i556">${esc(selectionCot(icon))}</code></div><div class="hero-field-i556"><span class="hero-label-i556">Symbol Path</span><div class="hero-path-i556">${esc(selectionHierarchy(icon))}</div></div></div></div>
      <section class="inspector-block-i556"><div class="inspector-block-title-i556"><span>Identity</span></div>${identity.map(row => `<div class="identity-row-i556"><span>${esc(row[0])}</span><strong>${esc(row[1])}</strong></div>`).join('')}</section>
      <section class="inspector-block-i556"><div class="inspector-block-title-i556"><span>Related</span><span class="related-count-i556">${related.length} options</span></div><div class="related-grid-i556">${related.map((item,index) => `${index === variantCount && related.length > variantCount ? '<div class="related-divider-i556"></div>' : ''}<button type="button" class="related-card-i556 ${iconKey(item) === iconKey(icon) ? 'active' : ''}" data-related-index="${index}" title="${esc(selectionHierarchy(item))}"><span class="related-stage-i556">${iconImg(item,96,72)}</span><span class="related-name-i556">${esc(selectionLabel(item))}</span><span class="related-meta-i556">${esc(AFFILIATION_LABEL[iconAffiliation(item)] || milDomain(item))}</span></button>`).join('')}</div></section>`;
    node.querySelectorAll('[data-related-index]').forEach(button => button.addEventListener('click', () => {
      state.selected = related[Number(button.dataset.relatedIndex)] || state.selected;
      setActiveFromSelection(state.selected);
      renderSetRail();
      renderPicker();
    }));
    scheduleNormalization(node);
    renderGridSelection();
  }

  function applyPickerSelection() {
    const icon = state.selected;
    if (!icon) return;
    if (state.pickerTarget === 'editor') {
      if (state.editorPoint && state.editorPoint.symbol_locked) return;
      state.editorSymbol = icon;
      const affiliation = byId('pointEditorAffiliationI556');
      if (affiliation) affiliation.value = iconAffiliation(icon);
      renderEditorSymbol();
      markEditorDirty();
      closePicker();
      return;
    }
    window.v233PointState = window.v233PointState || {};
    window.v233PointState.icon = icon;
    window.v233MilSelected = icon.kind === 'milstd2525c' ? icon : null;
    const affiliation = byId('pointAffiliationI556');
    if (affiliation) affiliation.value = iconAffiliation(icon);
    renderCreateSymbol();
    closePicker();
    openCreatePanel({preserveDraft:true});
  }

  function clearPickerSelection() {
    state.selected = null;
    if (state.pickerTarget === 'point') {
      window.v233PointState = window.v233PointState || {};
      window.v233PointState.icon = null;
      window.v233MilSelected = null;
    }
    renderPicker();
  }

  function missionNames() {
    let rows = [];
    try { rows = (typeof lastDataSync !== 'undefined' && lastDataSync && lastDataSync.missions) || []; } catch (_) { rows = []; }
    const names = [];
    for (const row of rows) {
      const name = text(typeof row === 'string' ? row : (row.name || row.mission_name || row.missionName || row.uid));
      if (name && !names.includes(name)) names.push(name);
    }
    return names.sort((a,b)=>a.localeCompare(b));
  }

  function refreshMissionOptions() {
    const select = byId('pointMissionI556');
    if (!select) return;
    const previous = select.value;
    const names = missionNames();
    select.innerHTML = names.length ? names.map(name => `<option value="${esc(name)}">${esc(name)}</option>`).join('') : '<option value="">No accessible missions</option>';
    select.disabled = !names.length;
    if (names.includes(previous)) select.value = previous;
    updateDestinationVisibility();
  }

  function parseLocation(value) {
    const match = text(value).match(/^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*[, ]\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*$/);
    if (!match) return null;
    const lat = Number(match[1]), lon = Number(match[2]);
    if (!Number.isFinite(lat) || !Number.isFinite(lon) || lat < -90 || lat > 90 || lon < -180 || lon > 180) return null;
    return {lat, lon};
  }

  function formatLocation(lat, lon) {
    if (!finite(lat) || !finite(lon)) return '';
    return `${Number(lat).toFixed(6)}, ${Number(lon).toFixed(6)}`;
  }

  function pointCoordinates() {
    const input = byId('pointLocationI556');
    const parsed = input ? parseLocation(input.value) : null;
    if (parsed) return parsed;
    try {
      const ll = (window.v233PointState && window.v233PointState.latlng) || (typeof lastPointerLatLng !== 'undefined' && lastPointerLatLng) || (typeof map !== 'undefined' && map.getCenter());
      if (ll && finite(ll.lat) && finite(ll.lng)) return {lat:Number(ll.lat), lon:Number(ll.lng)};
    } catch (_) {}
    return null;
  }

  function setPointLatLng(coord) {
    if (!coord) return;
    window.v233PointState = window.v233PointState || {};
    try { window.v233PointState.latlng = window.L && typeof window.L.latLng === 'function' ? window.L.latLng(coord.lat, coord.lon) : {lat:coord.lat,lng:coord.lon}; }
    catch (_) { window.v233PointState.latlng = {lat:coord.lat,lng:coord.lon}; }
  }

  function setCreateStatus(message, kind) {
    const node = byId('pointSaveStatusI556');
    if (!node) return;
    node.textContent = text(message);
    node.classList.toggle('error', kind === 'error');
    node.classList.toggle('ok', kind === 'ok');
  }

  function validateCreateLocation(showMessage) {
    const input = byId('pointLocationI556');
    if (!input) return false;
    const parsed = parseLocation(input.value);
    input.classList.toggle('invalid', !parsed);
    const error = byId('pointLocationErrorI556');
    if (error) error.textContent = !parsed && showMessage ? 'Enter valid latitude and longitude.' : '';
    if (parsed) setPointLatLng(parsed);
    return Boolean(parsed);
  }

  function updateDestinationVisibility() {
    const destination = byId('pointSaveDestinationI556');
    const missionField = byId('pointMissionFieldI556');
    if (!destination || !missionField) return;
    missionField.hidden = destination.value !== 'mission';
    if (destination.value === 'mission' && byId('pointMissionI556') && byId('pointMissionI556').disabled) {
      setCreateStatus('No accessible Data Sync Missions are currently loaded.', 'error');
    } else setCreateStatus('Ready to save the icon-based point.');
  }

  function ensureDefaultPointSymbol() {
    window.v233PointState = window.v233PointState || {};
    if (window.v233PointState.icon) return;
    const icons = window.v233MilIcons || [];
    const preferred = icons.find(icon => icon.name === 'friendly-ground-unit-infantry') || icons.find(icon => /^friendly-ground/i.test(icon.name || '')) || icons[0];
    if (preferred) window.v233PointState.icon = normalizeMil(preferred);
  }

  function ensureCreatePanel() {
    const panel = byId('pointEditPanel');
    if (!panel) return false;
    const required = ['pointCloseI556','pointNameInput','pointLocationI556','pointAffiliationI556','pointSymbolPreviewI556','pointSaveDestinationI556','pointNotesInput','pointSaveI556'];
    const complete = panel.dataset.i556PointWindow === '1' && required.every(id => byId(id));
    if (complete) return true;
    panel.dataset.i556PointWindow = '1';
    panel.dataset.takMapLoadedI564 = '1';
    panel.classList.add('point-window-i556');
    panel.innerHTML = `
      <header class="point-head-i556"><span class="point-head-icon-i556">＋</span><div><div class="point-title-i556">Create Point</div><div class="point-subtitle-i556">Point Tool</div></div><button type="button" class="point-close-i556" id="pointCloseI556" aria-label="Close">×</button></header>
      <div class="point-body-i556">
        <section class="point-source-strip-i556"><span class="point-source-icon-i556">⌖</span><div><div class="point-source-title-i556">Point location selected</div><div class="point-source-meta-i556" id="pointLocationSummaryI556">Click the map or enter coordinates below.</div></div><span class="point-source-state-i556">Ready</span></section>
        <div class="point-form-grid-i556">
          <div class="point-field-i556 wide"><label for="pointNameInput">Point Name</label><input class="point-control-i556" id="pointNameInput" maxlength="120" placeholder="Point name"></div>
          <div class="point-field-i556 wide"><label for="pointLocationI556">Location</label><input class="point-control-i556" id="pointLocationI556" inputmode="decimal" spellcheck="false" placeholder="34.214827, -118.487930"><div class="point-help-i556"><span>Latitude, Longitude</span><span class="point-location-error-i556" id="pointLocationErrorI556"></span></div></div>
          <div class="point-field-i556 wide"><label for="pointAffiliationI556">Affiliation</label><select class="point-control-i556" id="pointAffiliationI556"><option value="friendly">Friendly</option><option value="hostile">Hostile</option><option value="neutral">Neutral</option><option value="unknown">Unknown</option></select></div>
        </div>
        <section class="point-symbol-card-i556"><div class="point-symbol-stage-i556" id="pointSymbolPreviewI556"></div><div><div class="point-symbol-name-i556" id="pointSymbolNameI556">No symbol selected</div><div class="point-symbol-cot-i556" id="pointSymbolCotI556"></div><div class="point-symbol-path-i556" id="pointSymbolPathI556">Choose a registry-managed symbol.</div></div><button type="button" class="point-symbol-button-i556" id="pointChooseSymbolI556">Choose Symbol</button></section>
        <section class="point-destination-i556"><div class="point-field-i556 wide"><label for="pointSaveDestinationI556">Save Destination</label><select class="point-control-i556" id="pointSaveDestinationI556"><option value="local">Local Data</option><option value="mission">Data Sync Mission</option></select></div><div class="point-field-i556 wide point-mission-field-i556" id="pointMissionFieldI556" hidden><label for="pointMissionI556">Mission</label><select class="point-control-i556" id="pointMissionI556"></select></div></section>
        <div class="point-field-i556"><label for="pointNotesInput">Notes / Remarks</label><textarea class="point-control-i556" id="pointNotesInput" placeholder="Description, tasking, or operational remarks"></textarea></div>
        <div class="point-status-i556" id="pointSaveStatusI556">Ready to save the icon-based point.</div>
      </div>
      <footer class="point-actions-i556"><span class="point-action-spacer-i556"></span><button type="button" class="point-button-i556 ghost" id="pointCancelI556">Cancel</button><button type="button" class="point-button-i556 primary" id="pointSaveI556">Save Point</button></footer>`;
    byId('pointCloseI556').addEventListener('click', closeCreatePanel);
    byId('pointCancelI556').addEventListener('click', closeCreatePanel);
    byId('pointSaveI556').addEventListener('click', saveNewPoint);
    byId('pointChooseSymbolI556').addEventListener('click', () => openPicker('point', chosenFromPointState()));
    byId('pointSaveDestinationI556').addEventListener('change', updateDestinationVisibility);
    byId('pointLocationI556').addEventListener('input', () => { createSession.manualLocation = true; validateCreateLocation(false); updateCreateLocationSummary(); });
    byId('pointLocationI556').addEventListener('blur', () => validateCreateLocation(true));
    byId('pointAffiliationI556').addEventListener('change', event => {
      const icon = chosenFromPointState();
      if (icon && icon.kind !== 'unregistered') {
        window.v233PointState.icon = switchIconAffiliation(icon, event.target.value);
        renderCreateSymbol();
      }
    });
    const mini = byId('pointMiniToolbar');
    if (mini) {
      mini.querySelectorAll('.tool-color').forEach(node => node.remove());
      mini.querySelectorAll('button').forEach(button => {
        if (!/icon/i.test(button.textContent || '')) return;
        button.removeAttribute('onclick');
        button.title = 'Choose Symbol';
        if (button.dataset.i564RegistryBound === '1') return;
        button.dataset.i564RegistryBound = '1';
        button.addEventListener('click', event => {
          event.preventDefault();
          event.stopPropagation();
          openPicker('point', chosenFromPointState());
        });
      });
    }
    return true;
  }

  function updateCreateLocationSummary() {
    const node = byId('pointLocationSummaryI556');
    const input = byId('pointLocationI556');
    if (!node || !input) return;
    const parsed = parseLocation(input.value);
    node.textContent = parsed ? formatLocation(parsed.lat, parsed.lon) : 'Enter valid latitude and longitude.';
  }

  function renderCreateSymbol() {
    if (!ensureCreatePanel()) return;
    const icon = chosenFromPointState();
    const preview = byId('pointSymbolPreviewI556');
    if (preview) preview.innerHTML = iconImg(icon,128,96);
    const name = byId('pointSymbolNameI556'); if (name) name.textContent = selectionLabel(icon);
    const cot = byId('pointSymbolCotI556'); if (cot) cot.textContent = selectionCot(icon);
    const path = byId('pointSymbolPathI556'); if (path) path.textContent = selectionHierarchy(icon) || 'Choose a registry-managed symbol.';
    scheduleNormalization(preview);
  }

  function mapViewportRect() {
    const mapNode = byId('map');
    if (!mapNode || typeof mapNode.getBoundingClientRect !== 'function') return null;
    const rect = mapNode.getBoundingClientRect();
    return rect && rect.width > 40 && rect.height > 40 ? rect : null;
  }

  function positionCreatePanel() {
    const panel = byId('pointEditPanel');
    const rect = mapViewportRect();
    if (!panel || !rect || !panel.classList.contains('active')) return;
    const margin = 14;
    const maxWidth = Math.max(280, rect.width - margin * 2);
    const maxHeight = Math.max(260, rect.height - margin * 2);
    panel.style.setProperty('width', `${Math.min(468, maxWidth)}px`, 'important');
    panel.style.setProperty('max-height', `${maxHeight}px`, 'important');
    const measured = panel.getBoundingClientRect();
    let left = rect.left + margin;
    let top = rect.top + margin;
    left = Math.max(rect.left + margin, Math.min(left, rect.right - measured.width - margin));
    top = Math.max(rect.top + margin, Math.min(top, rect.bottom - measured.height - margin));
    panel.style.setProperty('left', `${Math.round(left)}px`, 'important');
    panel.style.setProperty('top', `${Math.round(top)}px`, 'important');
    panel.style.setProperty('right', 'auto', 'important');
    panel.style.setProperty('bottom', 'auto', 'important');
  }

  function watchCreatePanelViewport() {
    if (window.__takMapPointViewportWatchI556) return;
    window.__takMapPointViewportWatchI556 = true;
    const schedule = () => requestAnimationFrame(positionCreatePanel);
    window.addEventListener('resize', schedule, {passive:true});
    window.addEventListener('orientationchange', schedule, {passive:true});
    try {
      const mapNode = byId('map');
      if (mapNode && window.ResizeObserver) new ResizeObserver(schedule).observe(mapNode);
      const sidebar = document.querySelector('.sidebar,#sidebar,.menu-panel');
      if (sidebar && window.MutationObserver) new MutationObserver(schedule).observe(sidebar,{attributes:true,subtree:true,attributeFilter:['class','style']});
    } catch (_) {}
  }

  function openCreatePanel(options) {
    options = options && typeof options === 'object' ? options : {};
    if (!ensureCreatePanel()) return;
    ensureDefaultPointSymbol();
    const panel = byId('pointEditPanel');
    const clicked = pointStateCoordinate();
    const clickedKey = coordinateKey(clicked);
    const starting = !createSession.active;
    if (starting) {
      resetCreateDraft({preserveReusable:true});
      createSession.active = true;
      createSession.id += 1;
    }
    if (panel) panel.classList.add('active');
    const location = byId('pointLocationI556');
    if (!options.preserveDraft && clicked && (starting || clickedKey !== createSession.mapCoordinateKey)) {
      if (location) location.value = formatLocation(clicked.lat, clicked.lon);
      setPointLatLng(clicked);
      createSession.mapCoordinateKey = clickedKey;
      createSession.manualLocation = false;
    } else if (starting && location && !text(location.value)) {
      const coord = pointCoordinates();
      if (coord) { location.value = formatLocation(coord.lat, coord.lon); setPointLatLng(coord); createSession.mapCoordinateKey = coordinateKey(coord); }
    }
    const affiliation = byId('pointAffiliationI556');
    const icon = chosenFromPointState();
    if (affiliation && icon) affiliation.value = iconAffiliation(icon);
    refreshMissionOptions();
    updateDestinationVisibility();
    updateCreateLocationSummary();
    renderCreateSymbol();
    watchCreatePanelViewport();
    requestAnimationFrame(positionCreatePanel);
    setTimeout(positionCreatePanel, 80);
  }

  function closeCreatePanel() {
    const panel = byId('pointEditPanel');
    if (panel) panel.classList.remove('active');
    resetCreateDraft({preserveReusable:true});
  }

  function localFeatureProperties(icon, affiliation, name, notes) {
    const properties = {name, callsign:name, notes, remarks:notes, kind:'point', source:'TAK Map Point Tool i556'};
    if (icon && icon.kind === 'custom') {
      Object.assign(properties, {icon_mode:'custom-registry', iconsetpath:icon.iconsetpath, iconset_path:icon.iconsetpath, iconset_uid:icon.iconset_uid, iconset_name:icon.iconset_name, icon_group:icon.group_name, icon_filename:icon.filename, cot_type:customCotType(Object.assign({}, icon, {affiliation_override:affiliation})), sidc:''});
    } else if (icon) {
      Object.assign(properties, {icon_mode:'milstd2525c', mil2525_name:icon.name || '', mil2525_label:icon.label || '', sidc:icon.sidc || '', cot_type:milCotType(icon)});
    }
    return properties;
  }

  async function uploadLocalPoint(name, feature) {
    const collection = {type:'FeatureCollection', features:[feature]};
    const blob = new Blob([JSON.stringify(collection, null, 2)], {type:'application/geo+json'});
    const safe = text(name || 'TAK Map Object').replace(/[\\/:*?"<>|]+/g,'-').slice(0,80) || 'TAK Map Object';
    const data = new FormData();
    data.append('files', new File([blob], `${safe}.geojson`, {type:'application/geo+json'}));
    const result = await apiJson(await fetch('/api/tak-map/import', {method:'POST', body:data, credentials:'same-origin'}));
    try { if (typeof lastImports !== 'undefined') lastImports = result.imports || lastImports; } catch (_) {}
    try { if (typeof refreshLocalData === 'function') await refreshLocalData(); if (typeof drawImportedObjects === 'function') drawImportedObjects(); } catch (_) {}
    return result;
  }

  function symbolPayload(icon) {
    if (!icon) return {};
    if (icon.kind === 'custom') return {kind:'custom', iconsetpath:icon.iconsetpath, iconset_uid:icon.iconset_uid, group_name:icon.group_name, filename:icon.filename, cot_type:customCotType(icon)};
    if (icon.kind === 'unregistered') return {kind:'unregistered', iconsetpath:icon.iconsetpath};
    return {kind:'milstd2525c', sidc:icon.sidc || '', name:icon.name || '', label:icon.label || '', cot_type:milCotType(icon)};
  }

  async function saveNewPoint() {
    if (!ensureCreatePanel()) return;
    const locationInput = byId('pointLocationI556');
    let coord = parseLocation(locationInput && locationInput.value);
    if (!coord && locationInput && !text(locationInput.value)) {
      coord = pointCoordinates();
      if (coord) locationInput.value = formatLocation(coord.lat, coord.lon);
    }
    if (!coord) { validateCreateLocation(true); setCreateStatus('Enter a valid Location before saving.', 'error'); return; }
    const name = text(byId('pointNameInput').value) || 'Dropped Point';
    const notes = text(byId('pointNotesInput').value);
    const affiliation = text(byId('pointAffiliationI556').value) || 'friendly';
    const destination = text(byId('pointSaveDestinationI556').value) || 'local';
    const mission = text(byId('pointMissionI556').value);
    let icon = chosenFromPointState();
    if (!icon) { setCreateStatus('Select a registry-managed symbol before saving.', 'error'); return; }
    if (icon.kind !== 'unregistered') icon = switchIconAffiliation(icon, affiliation);
    window.v233PointState.icon = icon;
    setPointLatLng(coord);
    const button = byId('pointSaveI556');
    if (button) button.disabled = true;
    setCreateStatus(destination === 'mission' ? 'Publishing to OpenTAKServer Mission and waiting for read-back confirmation…' : 'Saving to Local Data…');
    try {
      if (destination === 'mission') {
        if (!mission) throw new Error('Select an accessible Data Sync Mission.');
        const payload = {mission_name:mission, name, notes, lat:coord.lat, lon:coord.lon, affiliation, symbol:symbolPayload(icon)};
        const result = await apiJson(await fetch(POINT_API, {method:'POST', headers:{'Content-Type':'application/json'}, credentials:'same-origin', cache:'no-store', body:JSON.stringify(payload)}));
        if (!result.redraw_allowed) throw new Error('OpenTAKServer did not confirm the new point.');
        setCreateStatus('Point saved and confirmed by OpenTAKServer.', 'ok');
        if (typeof forceDataSyncSync === 'function') await forceDataSyncSync('i564-new-registry-point');
      } else {
        const feature = {type:'Feature', geometry:{type:'Point', coordinates:[coord.lon, coord.lat]}, properties:localFeatureProperties(icon, affiliation, name, notes)};
        await uploadLocalPoint(name, feature);
        setCreateStatus('Point saved to Local Data.', 'ok');
      }
      setTimeout(() => {
        closeCreatePanel();
        if (typeof setActiveMapTool === 'function') setActiveMapTool('move');
      }, 300);
    } catch (error) {
      setCreateStatus(`Save failed: ${error.message || error}`, 'error');
    } finally { if (button) button.disabled = false; }
  }

  function customPathFromObject(value) {
    const keys = new Set(['data_sync_current_iconset_path_i553','current_iconset_path_i553','mission_cot_raw_iconset_path_i553','iconsetpath','iconset_path','usericon_path','user_icon_path','icon_path']);
    const stack = [value], seen = new Set();
    while (stack.length) {
      const current = stack.pop();
      if (current && typeof current === 'object') {
        if (seen.has(current)) continue;
        seen.add(current);
        if (Array.isArray(current)) { current.forEach(child => stack.push(child)); continue; }
        for (const [key, child] of Object.entries(current)) {
          if (keys.has(String(key).toLowerCase()) && text(child)) return text(child);
          if (child && typeof child === 'object') stack.push(child);
        }
      }
    }
    return '';
  }

  function objectUid(object) { return text(object && (object.event_uid || object.cot_uid || object.uid || object.id)); }
  function objectMission(object) { return text(object && (object.mission_name || object.missionName || object.mission)); }
  function objectIsPoint(object) { return object && finite(object.lat) && finite(object.lon) && !/route|shape|polygon|area/i.test(text(object.geometry || object.kind)); }
  function sourceOwnedPoint(object) { return Boolean(objectIsPoint(object) && objectUid(object) && objectMission(object)); }
  function localPointId(object) {
    const direct = text(object && (object._local_id || object.local_id));
    if (direct) return direct;
    const importId = text(object && (object.import_id || object.importId));
    const rawIndex = object && (object.import_feature_index ?? object.feature_index ?? object.local_index);
    const index = Number(rawIndex);
    return importId && Number.isInteger(index) && index >= 0 ? `${importId}:${index}` : '';
  }
  function localPoint(object) { return Boolean(objectIsPoint(object) && (localPointId(object) || text(object && (object.import_id || object.import_name)))); }
  function dataSyncObjects() { try { return (typeof lastDataSync !== 'undefined' && lastDataSync && lastDataSync.objects) || []; } catch (_) { return []; } }
  function localObjects() { try { return typeof importedFeatures === 'function' ? importedFeatures() : []; } catch (_) { return []; } }

  function objectNotes(object) {
    return text(object && (object.notes || object.remarks || (object.properties && (object.properties.notes || object.properties.remarks || object.properties.description))));
  }

  function parsedDate(value) {
    if (value == null || value === '') return null;
    try {
      let date;
      const numeric = typeof value === 'number' || /^\d+(?:\.\d+)?$/.test(text(value));
      if (numeric) {
        let epoch = Number(value);
        if (!Number.isFinite(epoch)) return null;
        while (epoch > 1e14) epoch /= 1000;
        if (epoch < 1e12) epoch *= 1000;
        date = new Date(epoch);
      } else {
        date = new Date(value);
      }
      return Number.isFinite(date.getTime()) ? date : null;
    } catch (_) { return null; }
  }

  function pad2(value) { return String(value).padStart(2, '0'); }

  function elapsedAge(date) {
    if (!date || !Number.isFinite(date.getTime())) return '';
    let minutes = Math.max(0, Math.floor((Date.now() - date.getTime()) / 60000));
    const days = Math.floor(minutes / 1440);
    minutes -= days * 1440;
    const hours = Math.floor(minutes / 60);
    minutes -= hours * 60;
    const parts = [];
    if (days) parts.push(`${days}${days === 1 ? 'day' : 'days'}`);
    if (hours) parts.push(`${hours}h`);
    if (minutes || !parts.length) parts.push(`${minutes}m`);
    return parts.join(' ');
  }

  function dateAgeText(value) {
    const date = parsedDate(value);
    if (!date) return text(value);
    const stamp = `${pad2(date.getMonth() + 1)}/${pad2(date.getDate())}/${date.getFullYear()} ${pad2(date.getHours())}:${pad2(date.getMinutes())}`;
    const age = elapsedAge(date);
    return age ? `${stamp} ${age}` : stamp;
  }

  function objectAdded(object) {
    let value = object && (object.added || object.created || object.uploaded || object.start || object.time);
    if (value == null || value === '') {
      try { if (typeof window.addedTime === 'function') value = window.addedTime(object); } catch (_) {}
    }
    return dateAgeText(value);
  }

  function objectUpdated(object) {
    const edit = object && object.popup_edit;
    const value = (edit && edit.updated) || (object && (object.updated || object.timestamp || object.event_time || object.time));
    return dateAgeText(value);
  }

  function displayLocation(lat, lon) {
    const la = Number(lat), lo = Number(lon);
    if (!Number.isFinite(la) || !Number.isFinite(lo)) return '';
    const ll = {lat:la, lng:lo};
    try {
      if (typeof window.formatCoordMode === 'function') {
        const formatted = text(window.formatCoordMode(ll));
        if (formatted && !/move pointer/i.test(formatted)) return formatted;
      }
    } catch (_) {}
    return formatLocation(la, lo);
  }

  async function ensureOtsIdentity(force) {
    if (!force && state.otsIdentityPromise) return state.otsIdentityPromise;
    if (!force && state.otsIdentity && state.otsIdentity.loaded) return state.otsIdentity;
    const promise = (async () => {
      try {
        const response = await fetch('/api/tak-map/ots/source-identity', {cache:'no-store', credentials:'same-origin'});
        const body = await apiJson(response);
        const display = text(body && body.display) || 'Data Sync: OpenTAKServer';
        state.otsIdentity = {
          loaded:true,
          display,
          url_hostname:text(body && body.url_hostname),
          server_hostname:text(body && body.server_hostname),
        };
      } catch (error) {
        state.otsIdentity = {loaded:true, display:'Data Sync: OpenTAKServer', url_hostname:'', server_hostname:'', error:text(error && (error.message || error))};
      }
      try {
        const sidebar = window.TakMapContextSidebarI564 || window.TakMapContextSidebarI562;
        if (sidebar && typeof sidebar.refresh === 'function') sidebar.refresh();
      } catch (_) {}
      return state.otsIdentity;
    })().finally(() => { state.otsIdentityPromise = null; });
    state.otsIdentityPromise = promise;
    return promise;
  }

  function sourceDisplay(dataSync, object) {
    if (!dataSync) return text(object && (object.import_name || object.source)) || 'Local Data';
    return text(state.otsIdentity && state.otsIdentity.display) || 'Data Sync: OpenTAKServer';
  }

  function syncState(object, dataSync) {
    const explicit = text(object && (object.sync_state || object.syncState || object.sync_status || object.syncStatus)).toLowerCase();
    if (object && (object.remote_deleted || object.remoteDeleted || object.tombstone)) return {label:'Remote Deleted', key:'remote-deleted'};
    if (object && (object.sync_conflict || object.conflict)) return {label:'Conflict', key:'conflict'};
    if (object && (object.sync_pending || object.pending_sync || object.pending)) return {label:'Pending', key:'pending'};
    if (object && (object.sync_stale || object.stale)) return {label:'Stale', key:'stale'};
    if (/remote.?deleted|deleted.?remote/.test(explicit)) return {label:'Remote Deleted', key:'remote-deleted'};
    if (/conflict/.test(explicit)) return {label:'Conflict', key:'conflict'};
    if (/pending|saving|uploading|syncing/.test(explicit)) return {label:'Pending', key:'pending'};
    if (/stale|expired/.test(explicit)) return {label:'Stale', key:'stale'};
    if (/local/.test(explicit)) return {label:'Local Only', key:'local-only'};
    if (/synced|current|complete|ok/.test(explicit)) return {label:'Synced', key:'synced'};
    return dataSync ? {label:'Synced', key:'synced'} : {label:'Local Only', key:'local-only'};
  }

  function objectSymbol(object) {
    const path = customPathFromObject(object);
    if (path && !/^COT_MAPPING_2525/i.test(path)) {
      const cached = state.customByPath.get(path);
      if (cached && typeof cached.then !== 'function') return Object.assign({}, cached, {kind:'custom', affiliation_override:affiliationFromCot(object && (object.cot_type || object.type))});
      const parts = path.split('/').filter(Boolean);
      const uid = parts.shift() || '';
      const filename = parts.pop() || path;
      const set = state.summary && (state.summary.sets || []).find(row => row.uid === uid);
      const icon = {
        kind: set ? 'custom' : 'unregistered',
        iconsetpath:path,
        iconset_uid:uid,
        iconset_name:(set && set.name) || uid,
        group_name:parts.join('/'),
        filename,
        cot_type:text(object && (object.cot_type || object.type)),
        affiliation_override:affiliationFromCot(object && (object.cot_type || object.type)),
        asset_url:customAssetUrl(path),
      };
      return icon;
    }
    return milFromPoint(object || {});
  }

  function popupImageHtml(object) {
    const path = customPathFromObject(object);
    if (path && !/^COT_MAPPING_2525/i.test(path)) {
      return `<img src="${esc(customAssetUrl(path))}" alt="" onerror="this.outerHTML='<span class=&quot;point-popup-unavailable-i556&quot;>?</span>'">`;
    }
    const icon = objectSymbol(object);
    const src = selectionImage(icon);
    return src ? `<img src="${esc(src)}" alt="">` : '<span class="point-popup-unavailable-i556">?</span>';
  }

  function popupRow(label, value, className) {
    const clean = text(value);
    if (!clean) return '';
    return `<div class="point-popup-label-i556">${esc(label)}</div><div class="point-popup-value-i556 ${esc(className || '')}">${esc(clean)}</div>`;
  }

  function popupLocationRow(value) {
    const clean = text(value);
    if (!clean) return '';
    return `<div class="point-popup-label-i556">Location</div><div class="point-popup-value-i556 point-popup-location-i564"><span class="point-popup-location-text-i564">${esc(clean)}</span><button type="button" class="point-popup-copy-i564" data-point-copy-location="1" title="Copy location" aria-label="Copy location">Copy</button></div>`;
  }

  function popupSyncRow(sync) {
    if (!sync || !sync.label) return '';
    return `<div class="point-popup-label-i556">Sync State</div><div class="point-popup-value-i556"><span class="point-popup-sync-i564 state-${esc(sync.key)}"><span class="point-popup-sync-dot-i564"></span>${esc(sync.label)}</span></div>`;
  }

  function pointInfoPopupHtml(object, sourceKind) {
    const local = sourceKind === 'local' || localPoint(object) || (!objectMission(object) && text(object && (object.import_id || object.import_name)));
    const dataSync = !local;
    const icon = objectSymbol(object);
    const name = text(object && (object.callsign || object.name || object.uid || object.id)) || 'Point';
    const cot = text(object && (object.cot_type || object.type)) || selectionCot(icon);
    const hierarchy = selectionHierarchy(icon) || 'Point symbol';
    const affiliation = AFFILIATION_LABEL[iconAffiliation(icon)] || AFFILIATION_LABEL[affiliationFromCot(cot)] || 'Unknown';
    const location = displayLocation(object && object.lat, object && object.lon);
    const mission = objectMission(object);
    const source = sourceDisplay(dataSync, object);
    const added = objectAdded(object);
    const updated = objectUpdated(object);
    const sync = syncState(object, dataSync);
    const notes = objectNotes(object);
    let editButton = '';
    if (dataSync && sourceOwnedPoint(object)) {
      editButton = `<button type="button" class="point-popup-edit-i556" data-i556-point-edit="1" data-point-source="datasync" data-point-uid="${esc(objectUid(object))}" data-point-mission="${esc(mission)}">Edit Point</button>`;
    } else if (local && localPointId(object)) {
      editButton = `<button type="button" class="point-popup-edit-i556" data-i556-point-edit="1" data-point-source="local" data-point-local-id="${esc(localPointId(object))}">Edit Point</button>`;
    }
    const rows = [
      popupRow('Affiliation', affiliation),
      dataSync ? popupRow('Mission', mission) : '',
      popupRow('Source', source),
      popupLocationRow(location),
      popupRow('Added', added, 'point-popup-time-i564'),
      popupRow('Updated', updated, 'point-popup-time-i564'),
      popupSyncRow(sync),
      popupRow('Notes', notes, 'point-popup-notes-i556'),
    ].join('');
    return `<div class="point-info-popup-i556"><header class="point-popup-head-i556"><div class="point-popup-stage-i556">${popupImageHtml(object)}</div><div><div class="point-popup-title-i556">${esc(name)}</div><div class="point-popup-subtitle-i556">Point · ${dataSync ? 'Data Sync' : 'Local Data'}</div><div class="point-popup-cot-i556">${esc(cot)}</div><div class="point-popup-path-i556">${esc(hierarchy)}</div></div></header><div class="point-popup-body-i556"><div class="point-popup-grid-i556">${rows}</div>${editButton ? `<div class="point-popup-actions-i556">${editButton}</div>` : ''}</div></div>`;
  }

  function setPointLayerPopup(object, sourceKind) {
    if (!objectIsPoint(object)) return;
    const layer = object && object.__layer;
    if (!layer) return;
    try {
      const controller = window.TakMapContextSidebarI564 || window.TakMapContextSidebarI562;
      if (controller && typeof controller.bindObjectLayer === 'function') {
        if (typeof layer.unbindPopup === 'function') layer.unbindPopup();
        controller.bindObjectLayer(layer, object, sourceKind);
        return;
      }
    } catch (_) {}
    const content = pointInfoPopupHtml(object, sourceKind);
    try {
      if (typeof layer.setPopupContent === 'function') layer.setPopupContent(content);
      else if (typeof layer.bindPopup === 'function') layer.bindPopup(content);
      const popup = typeof layer.getPopup === 'function' ? layer.getPopup() : null;
      if (popup && typeof popup.setContent === 'function') popup.setContent(content);
      if (!layer.__takMapPointPopupI556 && typeof layer.on === 'function') {
        layer.__takMapPointPopupI556 = true;
        layer.on('popupopen', () => {
          try {
            const latest = pointInfoPopupHtml(object, sourceKind);
            if (typeof layer.setPopupContent === 'function') layer.setPopupContent(latest);
            const active = typeof layer.getPopup === 'function' ? layer.getPopup() : null;
            if (active && typeof active.setContent === 'function') active.setContent(latest);
          } catch (_) {}
        });
      }
    } catch (error) { state.errors.push(`Popup: ${error.message || error}`); }
  }

  function refreshPointPopups() {
    for (const object of dataSyncObjects()) setPointLayerPopup(object, 'datasync');
    for (const object of localObjects()) setPointLayerPopup(object, 'local');
  }

  function redrawPointLayers(reason) {
    setTimeout(() => {
      try { if (typeof drawDataSyncObjects === 'function') drawDataSyncObjects(dataSyncObjects()); } catch (_) {}
      try { if (typeof drawImportedObjects === 'function') drawImportedObjects(); } catch (_) {}
      setTimeout(refreshPointPopups, 40);
    }, reason === 'registry-ready' ? 20 : 0);
  }

  function ensureEditor() {
    if (byId('takMapPointEditorI556')) return;
    const modal = document.createElement('div');
    modal.id = 'takMapPointEditorI556';
    modal.innerHTML = `
      <section class="point-editor-card-i556" role="dialog" aria-modal="true" aria-labelledby="pointEditorTitleI556">
        <header class="point-head-i556"><span class="point-head-icon-i556">✎</span><div><div class="point-title-i556" id="pointEditorTitleI556">Edit Point</div><div class="point-subtitle-i556" id="pointEditorSubtitleI556">Point</div></div><span class="unsaved-badge-i556" id="pointEditorUnsavedI556">Unsaved Changes</span><button type="button" class="point-close-i556" id="pointEditorCloseI556" aria-label="Close">×</button></header>
        <div class="point-body-i556">
          <section class="point-source-strip-i556"><span class="point-source-icon-i556">⌘</span><div><div class="point-source-title-i556" id="pointEditorSourceTitleI556">Point</div><div class="point-source-meta-i556" id="pointEditorSourceMetaI556"></div></div><span class="point-source-state-i556" id="pointEditorSourceStateI556">Ready</span></section>
          <div class="point-form-grid-i556">
            <div class="point-field-i556 wide"><label for="pointEditorNameI556">Point Name</label><input class="point-control-i556" id="pointEditorNameI556" maxlength="120"></div>
            <div class="point-field-i556 wide"><label for="pointEditorLocationI556">Location</label><input class="point-control-i556" id="pointEditorLocationI556" inputmode="decimal" spellcheck="false"><div class="point-help-i556"><span>Latitude, Longitude</span><span class="point-location-error-i556" id="pointEditorLocationErrorI556"></span></div></div>
            <div class="point-field-i556"><label for="pointEditorAffiliationI556">Affiliation</label><select class="point-control-i556" id="pointEditorAffiliationI556"><option value="friendly">Friendly</option><option value="hostile">Hostile</option><option value="neutral">Neutral</option><option value="unknown">Unknown</option></select></div>
            <div class="point-field-i556"><label for="pointEditorContextI556" id="pointEditorContextLabelI556">Source</label><input class="point-control-i556" id="pointEditorContextI556" readonly></div>
          </div>
          <section class="point-symbol-card-i556"><div class="point-symbol-stage-i556" id="pointEditorSymbolPreviewI556"></div><div><div class="point-symbol-name-i556" id="pointEditorSymbolNameI556"></div><div class="point-symbol-cot-i556" id="pointEditorSymbolCotI556"></div><div class="point-symbol-path-i556" id="pointEditorSymbolPathI556"></div></div><button type="button" class="point-symbol-button-i556" id="pointEditorChangeSymbolI556">Change Symbol</button></section>
          <div class="point-field-i556"><label for="pointEditorNotesI556">Notes / Remarks</label><textarea class="point-control-i556" id="pointEditorNotesI556"></textarea></div>
          <div class="point-status-i556" id="pointEditorStatusI556">Loading point…</div>
        </div>
        <footer class="point-actions-i556"><button type="button" class="point-button-i556 ghost" id="pointEditorResetI556" disabled>Reset Changes</button><span class="point-action-spacer-i556"></span><button type="button" class="point-button-i556 ghost" id="pointEditorCancelI556">Cancel</button><button type="button" class="point-button-i556 primary" id="pointEditorSaveI556" disabled>Save Changes</button></footer>
      </section>`;
    document.body.appendChild(modal);
    byId('pointEditorCloseI556').addEventListener('click', () => closeEditor(false, 'cancel'));
    byId('pointEditorCancelI556').addEventListener('click', () => closeEditor(false, 'cancel'));
    byId('pointEditorResetI556').addEventListener('click', resetEditor);
    byId('pointEditorSaveI556').addEventListener('click', saveEditor);
    byId('pointEditorChangeSymbolI556').addEventListener('click', () => {
      if (state.editorPoint && state.editorPoint.symbol_locked) return;
      openPicker('editor', state.editorSymbol);
    });
    ['pointEditorNameI556','pointEditorLocationI556','pointEditorAffiliationI556','pointEditorNotesI556'].forEach(id => {
      const node = byId(id);
      if (node) {
        node.addEventListener('input', markEditorDirty);
        node.addEventListener('change', () => {
          if (id === 'pointEditorAffiliationI556' && state.editorSymbol && state.editorSymbol.kind !== 'unregistered') state.editorSymbol = switchIconAffiliation(state.editorSymbol, node.value);
          if (id === 'pointEditorAffiliationI556') renderEditorSymbol();
          markEditorDirty();
        });
      }
    });
    byId('pointEditorLocationI556').addEventListener('blur', () => validateEditorLocation(true));
    modal.addEventListener('click', event => { if (event.target === modal) closeEditor(false); });
  }

  function setEditorStatus(message, kind) {
    const node = byId('pointEditorStatusI556');
    if (!node) return;
    node.textContent = text(message);
    node.classList.toggle('error', kind === 'error');
    node.classList.toggle('ok', kind === 'ok');
  }

  function validateEditorLocation(showMessage) {
    const input = byId('pointEditorLocationI556');
    const parsed = input && parseLocation(input.value);
    if (input) input.classList.toggle('invalid', !parsed);
    const error = byId('pointEditorLocationErrorI556');
    if (error) error.textContent = !parsed && showMessage ? 'Enter valid latitude and longitude.' : '';
    return Boolean(parsed);
  }

  function editorSnapshot() {
    return {
      name:text(byId('pointEditorNameI556') && byId('pointEditorNameI556').value),
      location:text(byId('pointEditorLocationI556') && byId('pointEditorLocationI556').value),
      affiliation:text(byId('pointEditorAffiliationI556') && byId('pointEditorAffiliationI556').value),
      notes:text(byId('pointEditorNotesI556') && byId('pointEditorNotesI556').value),
      symbolKey:iconKey(state.editorSymbol),
    };
  }

  function markEditorDirty() {
    if (!state.editorOriginal) return;
    const current = editorSnapshot();
    state.editorDirty = JSON.stringify(current) !== JSON.stringify(state.editorOriginal);
    const valid = validateEditorLocation(false);
    const badge = byId('pointEditorUnsavedI556'); if (badge) badge.classList.toggle('visible', state.editorDirty);
    const reset = byId('pointEditorResetI556'); if (reset) reset.disabled = !state.editorDirty;
    const save = byId('pointEditorSaveI556'); if (save) save.disabled = !state.editorDirty || !valid;
    if (state.editorDirty) {
      setEditorStatus(state.editorSource === 'datasync' ? 'Unsaved changes. Save uses concurrent-edit protection and OpenTAKServer Mission read-back confirmation.' : 'Unsaved changes. Save will update the Local Data point and redraw the map.');
    } else if (state.editorPoint) {
      const locked = state.editorPoint.symbol_locked ? ' The unregistered custom icon is protected and its exact source metadata will be preserved.' : '';
      setEditorStatus(state.editorSource === 'datasync' ? `Ready. Changes are written to the source-owned Mission point and redrawn only after confirmation.${locked}` : `Ready. Changes are stored in Local Data.${locked}`);
    }
  }

  function resetEditor() {
    if (!state.editorOriginal || !state.editorPoint) return;
    byId('pointEditorNameI556').value = state.editorOriginal.name;
    byId('pointEditorLocationI556').value = state.editorOriginal.location;
    byId('pointEditorAffiliationI556').value = state.editorOriginal.affiliation;
    byId('pointEditorNotesI556').value = state.editorOriginal.notes;
    state.editorSymbol = state.editorOriginal.symbol;
    renderEditorSymbol();
    markEditorDirty();
    setEditorStatus('Unsaved changes were reset.');
  }

  function closeEditor(force, reason) {
    const previous = state.editorPoint;
    const previousSource = state.editorSource;
    const modal = byId('takMapPointEditorI556');
    if (modal) modal.classList.remove('active');
    state.editorPoint = null;
    state.editorSymbol = null;
    state.editorOriginal = null;
    state.editorDirty = false;
    state.editorSource = '';
    state.editorLocalId = '';
    try {
      const controller = window.TakMapContextSidebarI564 || window.TakMapContextSidebarI562;
      if (controller && typeof controller.onPointEditorClosed === 'function') controller.onPointEditorClosed(reason || (force ? 'complete' : 'cancel'), previous, previousSource);
    } catch (_) {}
  }

  function milFromPoint(point) {
    const sidc = text(point && (point.sidc || (point.properties && point.properties.sidc))).toUpperCase();
    const name = text(point && (point.mil2525_name || (point.properties && point.properties.mil2525_name)));
    const list = window.v233MilIcons || [];
    let match = name ? list.find(icon => text(icon.name).toLowerCase() === name.toLowerCase()) : null;
    if (!match) match = list.find(icon => text(icon.sidc).toUpperCase() === sidc);
    if (!match && sidc) match = list.find(icon => text(icon.sidc).toUpperCase().replace(/-/g,'') === sidc.replace(/-/g,''));
    return match ? normalizeMil(match) : (sidc ? {kind:'milstd2525c',sidc,name,label:'Current MIL-STD-2525C symbol',cot_type:text(point && (point.cot_type || point.type))} : null);
  }

  function renderEditorSymbol() {
    const icon = state.editorSymbol;
    const preview = byId('pointEditorSymbolPreviewI556'); if (preview) preview.innerHTML = iconImg(icon,128,96);
    const name = byId('pointEditorSymbolNameI556'); if (name) name.textContent = selectionLabel(icon);
    const cot = byId('pointEditorSymbolCotI556'); if (cot) cot.textContent = selectionCot(icon);
    const path = byId('pointEditorSymbolPathI556'); if (path) path.textContent = selectionHierarchy(icon);
    const change = byId('pointEditorChangeSymbolI556');
    if (change) { change.disabled = Boolean(state.editorPoint && state.editorPoint.symbol_locked); change.textContent = change.disabled ? 'Unregistered Icon Locked' : 'Change Symbol'; }
    scheduleNormalization(preview);
  }

  async function openEditor(reference, mission, sourceKind) {
    ensureEditor();
    const source = sourceKind === 'local' ? 'local' : 'datasync';
    state.editorSource = source;
    state.editorLocalId = source === 'local' ? text(reference) : '';
    const modal = byId('takMapPointEditorI556'); if (modal) modal.classList.add('active');
    try {
      const controller = window.TakMapContextSidebarI564 || window.TakMapContextSidebarI562;
      if (controller && typeof controller.onPointEditorOpening === 'function') controller.onPointEditorOpening(source, reference, mission || '');
    } catch (_) {}
    byId('pointEditorSubtitleI556').textContent = source === 'local' ? 'Local Data' : 'Data Sync Mission';
    byId('pointEditorContextLabelI556').textContent = source === 'local' ? 'Source' : 'Mission';
    byId('pointEditorSourceStateI556').textContent = source === 'local' ? 'Local' : 'Synced';
    setEditorStatus(source === 'local' ? 'Loading Local Data point…' : 'Loading current Mission point…');
    try {
      const endpoint = source === 'local' ? `${LOCAL_POINT_API}?local_id=${encodeURIComponent(reference)}` : `${POINT_API}?uid=${encodeURIComponent(reference)}&mission=${encodeURIComponent(mission || '')}`;
      const result = await apiJson(await fetch(endpoint, {cache:'no-store', credentials:'same-origin'}));
      const point = result.point;
      state.editorPoint = point;
      if (source === 'datasync' && !point.source_owned) throw new Error('This point does not have a safe source-owned Mission identity.');
      if (point.registry_icon) state.editorSymbol = Object.assign({}, point.registry_icon, {kind:'custom',affiliation_override:affiliationFromCot(point.cot_type)});
      else if (point.custom_icon) state.editorSymbol = {kind:'unregistered',iconsetpath:point.iconsetpath,cot_type:point.cot_type};
      else state.editorSymbol = milFromPoint(point);
      byId('pointEditorNameI556').value = point.name || '';
      byId('pointEditorLocationI556').value = formatLocation(point.lat, point.lon);
      byId('pointEditorNotesI556').value = point.notes || '';
      byId('pointEditorContextI556').value = source === 'local' ? (point.source || 'Local Data') : (point.mission_name || '');
      byId('pointEditorAffiliationI556').value = iconAffiliation(state.editorSymbol) || affiliationFromCot(point.cot_type);
      byId('pointEditorSourceTitleI556').textContent = source === 'local' ? (point.source || 'Local Data Point') : `${point.mission_name || 'Data Sync'} Mission`;
      byId('pointEditorSourceMetaI556').textContent = source === 'local' ? `Local ID: ${point.local_id || reference}` : `UID: ${point.uid || ''} · source-owned`;
      renderEditorSymbol();
      state.editorOriginal = Object.assign(editorSnapshot(), {symbol:state.editorSymbol});
      state.editorDirty = false;
      markEditorDirty();
    } catch (error) {
      setEditorStatus(`Could not open point: ${error.message || error}`, 'error');
      const save = byId('pointEditorSaveI556'); if (save) save.disabled = true;
    }
  }

  async function saveEditor() {
    const point = state.editorPoint;
    if (!point || !state.editorDirty) return;
    const coord = parseLocation(byId('pointEditorLocationI556').value);
    if (!coord) { validateEditorLocation(true); setEditorStatus('Enter a valid Location before saving.', 'error'); return; }
    const button = byId('pointEditorSaveI556'); if (button) button.disabled = true;
    const reset = byId('pointEditorResetI556'); if (reset) reset.disabled = true;
    const dataSync = state.editorSource === 'datasync';
    setEditorStatus(dataSync ? 'Saving through OpenTAKServer and confirming Mission read-back…' : 'Saving Local Data point…');
    try {
      const affiliation = text(byId('pointEditorAffiliationI556').value);
      let icon = state.editorSymbol;
      if (icon && icon.kind !== 'unregistered') icon = switchIconAffiliation(icon, affiliation);
      state.editorSymbol = icon;
      const payload = {expected_fingerprint:point.fingerprint,name:text(byId('pointEditorNameI556').value),lat:coord.lat,lon:coord.lon,notes:text(byId('pointEditorNotesI556').value),affiliation,symbol:symbolPayload(icon)};
      let result;
      if (dataSync) {
        Object.assign(payload,{uid:point.uid,mission_name:point.mission_name});
        result = await apiJson(await fetch(POINT_API, {method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',cache:'no-store',body:JSON.stringify(payload)}));
        if (!result.redraw_allowed) throw new Error('OpenTAKServer did not confirm the update.');
        if (typeof forceDataSyncSync === 'function') await forceDataSyncSync('i556-registry-point-edit');
      } else {
        payload.local_id = point.local_id || state.editorLocalId;
        result = await apiJson(await fetch(LOCAL_POINT_API, {method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',cache:'no-store',body:JSON.stringify(payload)}));
        try { if (typeof refreshImports === 'function') await refreshImports(); else { if (typeof refreshLocalData === 'function') await refreshLocalData(); if (typeof drawImportedObjects === 'function') drawImportedObjects(); } } catch (_) {}
      }
      state.editorPoint = result.point || point;
      state.editorOriginal = Object.assign(editorSnapshot(), {symbol:state.editorSymbol});
      state.editorDirty = false;
      markEditorDirty();
      setEditorStatus(dataSync ? 'Saved and confirmed by OpenTAKServer. The map may now redraw.' : 'Local Data point saved and redrawn.', 'ok');
      redrawPointLayers('editor-save');
      try {
        const controller = window.TakMapContextSidebarI564 || window.TakMapContextSidebarI562;
        if (controller && typeof controller.onPointSaved === 'function') controller.onPointSaved(result.point || state.editorPoint, dataSync ? 'datasync' : 'local');
      } catch (_) {}
      setTimeout(() => closeEditor(true, 'save'), 450);
    } catch (error) {
      if (error.status === 409 && error.payload && error.payload.concurrent_edit) setEditorStatus('This point changed after the editor opened. Close and reopen it to load the current version; nothing was overwritten.', 'error');
      else setEditorStatus(`Save failed: ${error.message || error}`, 'error');
      if (button) button.disabled = false;
      if (reset) reset.disabled = false;
    }
  }

  function handlePopupPointEdit(event) {
    try {
      const button = event.target && event.target.closest && event.target.closest('[data-i556-point-edit]');
      if (!button) return;
      event.preventDefault();
      event.stopPropagation();
      const source = text(button.getAttribute('data-point-source')) || 'datasync';
      if (source === 'local') {
        const localId = text(button.getAttribute('data-point-local-id'));
        if (localId) void openEditor(localId, '', 'local');
      } else {
        const uid = text(button.getAttribute('data-point-uid'));
        const mission = text(button.getAttribute('data-point-mission'));
        if (uid) void openEditor(uid, mission, 'datasync');
      }
    } catch (error) { state.errors.push(String(error)); }
  }

  function customIconHtml(object) {
    const path = customPathFromObject(object);
    if (!path || /^COT_MAPPING_2525/i.test(path)) return null;
    return `<div class="tak-icon-wrap tak-custom-icon-i556"><img src="${esc(customAssetUrl(path))}" alt="${esc(text(object && (object.callsign || object.name || path)))}" onerror="this.parentElement.innerHTML='<span class=&quot;tak-custom-unavailable-i556&quot;>?</span>'"></div>`;
  }

  function authoritativeMilIconHtml(object) {
    const custom = customIconHtml(object);
    if (custom) return custom;
    const base = state.baseMilIconHtml;
    return typeof base === 'function' ? base(object) : '';
  }
  authoritativeMilIconHtml.__takMapI556 = true;

  function authoritativeDataSyncIcon(object) {
    const path = customPathFromObject(object);
    if (path && !/^COT_MAPPING_2525/i.test(path) && window.L && typeof window.L.divIcon === 'function') {
      return window.L.divIcon({className:'',html:customIconHtml(object),iconSize:[40,40],iconAnchor:[20,20],popupAnchor:[0,-18]});
    }
    const base = state.baseDataSyncIcon;
    if (typeof base === 'function') return base(object);
    return window.L && typeof window.L.divIcon === 'function' ? window.L.divIcon({className:'',html:authoritativeMilIconHtml(object),iconSize:[36,40],iconAnchor:[18,22]}) : null;
  }
  authoritativeDataSyncIcon.__takMapI556 = true;

  function installAuthoritativeRenderers() {
    try {
      const currentMil = window.mil2525IconHtml;
      if (typeof currentMil === 'function' && currentMil !== authoritativeMilIconHtml && !currentMil.__takMapI556) state.baseMilIconHtml = currentMil;
      window.mil2525IconHtml = authoritativeMilIconHtml;
      try { mil2525IconHtml = authoritativeMilIconHtml; } catch (_) {}
    } catch (_) {}
    try {
      const currentIcon = window.dataSyncIcon;
      if (typeof currentIcon === 'function' && currentIcon !== authoritativeDataSyncIcon && !currentIcon.__takMapI556) state.baseDataSyncIcon = currentIcon;
      window.dataSyncIcon = authoritativeDataSyncIcon;
      try { dataSyncIcon = authoritativeDataSyncIcon; } catch (_) {}
    } catch (_) {}
  }

  function installPointPopupWrappers() {
    try {
      const currentPopup = window.pointPopupHtml;
      if (typeof currentPopup === 'function' && !currentPopup.__takMapI556) state.basePointPopupHtml = currentPopup;
      const popupWrapper = function (object, category) {
        if (objectIsPoint(object)) return pointInfoPopupHtml(object, localPoint(object) ? 'local' : 'datasync');
        return typeof state.basePointPopupHtml === 'function' ? state.basePointPopupHtml(object, category) : '';
      };
      popupWrapper.__takMapI556 = true;
      window.pointPopupHtml = popupWrapper;
      try { pointPopupHtml = popupWrapper; } catch (_) {}
    } catch (_) {}

    try {
      const currentAdd = window.addObjectLayer;
      if (typeof currentAdd === 'function' && !currentAdd.__takMapI556) {
        state.baseAddObjectLayer = currentAdd;
        const wrapper = function (group, object, sourceKey) {
          const layer = currentAdd.apply(this, arguments);
          if (objectIsPoint(object)) setPointLayerPopup(object, sourceKey === 'imported' ? 'local' : 'datasync');
          return layer;
        };
        wrapper.__takMapI556 = true;
        window.addObjectLayer = wrapper;
        try { addObjectLayer = wrapper; } catch (_) {}
      }
    } catch (_) {}

    try {
      const currentDraw = window.drawDataSyncObjects;
      if (typeof currentDraw === 'function' && !currentDraw.__takMapI556) {
        state.baseDrawDataSyncObjects = currentDraw;
        const wrapper = function () { const result = currentDraw.apply(this, arguments); setTimeout(refreshPointPopups, 0); return result; };
        wrapper.__takMapI556 = true;
        window.drawDataSyncObjects = wrapper;
        try { drawDataSyncObjects = wrapper; } catch (_) {}
      }
    } catch (_) {}

    try {
      const currentDraw = window.drawImportedObjects;
      if (typeof currentDraw === 'function' && !currentDraw.__takMapI556) {
        state.baseDrawImportedObjects = currentDraw;
        const wrapper = function () { const result = currentDraw.apply(this, arguments); setTimeout(refreshPointPopups, 0); return result; };
        wrapper.__takMapI556 = true;
        window.drawImportedObjects = wrapper;
        try { drawImportedObjects = wrapper; } catch (_) {}
      }
    } catch (_) {}

    const sidebarEditor = async function (index, event) {
      try {
        if (event && event.stopPropagation) event.stopPropagation();
        const object = dataSyncObjects()[Number(index)];
        if (sourceOwnedPoint(object)) return openEditor(objectUid(object), objectMission(object), 'datasync');
      } catch (_) {}
      return state.old.openDataSyncItemEdit && state.old.openDataSyncItemEdit !== sidebarEditor ? state.old.openDataSyncItemEdit.apply(this, arguments) : undefined;
    };
    sidebarEditor.__takMapI556 = true;
    window.openDataSyncItemEdit = sidebarEditor;
    try { openDataSyncItemEdit = sidebarEditor; } catch (_) {}
  }

  function patchRuntime() {
    if (state.booted) return;
    if (!byId('milPicker') || !window.v233PointState || typeof window.renderMilPicker !== 'function') return;
    state.booted = true;
    window.__takMapCurrentIconRegistry = VERSION;
    if (!document.__takMapI564RegistryToolbarDelegated) {
      document.__takMapI564RegistryToolbarDelegated = true;
      document.addEventListener('click', event => {
        const button = event.target && event.target.closest && event.target.closest('#pointMiniToolbar button');
        if (!button || !/icon/i.test(button.textContent || '')) return;
        event.preventDefault();
        event.stopPropagation();
        if (event.stopImmediatePropagation) event.stopImmediatePropagation();
        openPicker('point', chosenFromPointState());
      }, true);
    }
    addStyle();
    ensureRegistryModal();
    ensureCreatePanel();
    ensureEditor();
    state.old.renderPicker = window.renderMilPicker;
    state.old.openPicker = window.openMilPicker;
    state.old.closePicker = window.closeMilPicker;
    state.old.applyPicker = window.applyMilSelection;
    state.old.clearPicker = window.clearMilSelection;
    state.old.savePoint = window.v233SavePoint;
    state.old.openPointPanel = window.v233OpenPointPanel;
    state.old.milIconHtml = window.mil2525IconHtml;
    state.old.pointPopupHtml = window.pointPopupHtml;
    state.old.openDataSyncItemEdit = window.openDataSyncItemEdit;
    state.baseMilIconHtml = window.mil2525IconHtml;
    state.baseDataSyncIcon = window.dataSyncIcon;
    state.basePointPopupHtml = window.pointPopupHtml;

    window.renderMilPicker = renderPicker;
    window.openMilPicker = () => openPicker('point', chosenFromPointState());
    window.closeMilPicker = closePicker;
    window.applyMilSelection = applyPickerSelection;
    window.clearMilSelection = clearPickerSelection;
    window.v233SavePoint = saveNewPoint;
    window.v233OpenPointPanel = openCreatePanel;
    window.openDataSyncPointEditI556 = (uid, mission) => openEditor(uid, mission, 'datasync');
    window.openLocalPointEditI556 = localId => openEditor(localId, '', 'local');
    window.openDataSyncPointEditI564 = window.openDataSyncPointEditI556;
    window.openLocalPointEditI564 = window.openLocalPointEditI556;
    document.addEventListener('click', handlePopupPointEdit, true);
    installAuthoritativeRenderers();
    installPointPopupWrappers();
    // Assigning window.renderMilPicker back into the local renderMilPicker binding
    // makes renderPicker call itself recursively. Window properties above are the
    // authoritative globals; do not alias them back into local function bindings.
    document.querySelectorAll('.iteration-chip,.iteration-marker').forEach(node => node.textContent = 'i564');
    const cleanPointToolbar = () => {
      const mini = byId('pointMiniToolbar');
      if (!mini) return;
      mini.querySelectorAll('.tool-color').forEach(node => node.remove());
      mini.querySelectorAll('button').forEach(button => {
        if (!/icon/i.test(button.textContent || '')) return;
        button.removeAttribute('onclick');
        button.title = 'Choose Symbol';
        if (button.dataset.i564RegistryBound === '1') return;
        button.dataset.i564RegistryBound = '1';
        button.addEventListener('click', event => {
          event.preventDefault();
          event.stopPropagation();
          openPicker('point', chosenFromPointState());
        });
      });
    };
    const reassert = () => {
      installAuthoritativeRenderers();
      installPointPopupWrappers();
      cleanPointToolbar();
      refreshPointPopups();
      positionCreatePanel();
    };
    reassert();
    [120,300,700,1200,2500,5200,8000].forEach(ms => setTimeout(reassert, ms));
    setInterval(reassert, 12000);
    watchCreatePanelViewport();
    void ensureOtsIdentity(false);
    void loadSummary().then(() => { renderSetRail(); renderCreateSymbol(); reassert(); redrawPointLayers('registry-ready'); });
    const publicApiI564 = Object.freeze({
      version:VERSION,
      summary:()=>state.summary,
      selected:()=>state.selected,
      open:openPicker,
      openPointEditor:(source,reference,mission)=>openEditor(reference,mission,source),
      closePointEditor:(reason)=>closeEditor(true, reason || 'external'),
      pointInfoHtml:(object,sourceKind)=>pointInfoPopupHtml(object,sourceKind),
      isPoint:objectIsPoint,
      isLocalPoint:localPoint,
      pointUid:objectUid,
      pointMission:objectMission,
      pointLocalId:localPointId,
      pointCenter:object=>objectIsPoint(object)?[Number(object.lat),Number(object.lon)]:null,
      ensureCreatePanel,
      refreshPopups:refreshPointPopups,
      redraw:redrawPointLayers,
      diagnostics:()=>({ready:state.ready,activeSet:state.activeSet,milIconsLoaded:usableMilIcons(window.v233MilIcons||[]).length,milCatalogLoading:!!state.milLoadPromise,milCatalogError:state.milError,otsIdentity:Object.assign({},state.otsIdentity||{}),customSetsCached:Array.from(state.customBySet.keys()),normalizedAssets:state.normalizedCache.size,editorSource:state.editorSource,customRendererAuthoritative:window.dataSyncIcon===authoritativeDataSyncIcon,popupRendererAuthoritative:!!(window.pointPopupHtml&&window.pointPopupHtml.__takMapI556),createPanelReady:!!(byId('pointSaveI556')&&byId('pointLocationI556')),errors:state.errors.slice()})
    });
    window.TakMapIconRegistryI564 = publicApiI564;
    window.TakMapIconRegistryI562 = publicApiI564;

    window.TakMapIconRegistryI556 = publicApiI564;
  }

  function scheduleBoot() {
    if (!state.runtimeReady && document.documentElement.dataset.takMapRuntime !== 'ready') return;
    state.runtimeReady = true;
    let attempts = 0;
    const tryBoot = () => { attempts += 1; patchRuntime(); if (!state.booted && attempts < 80) setTimeout(tryBoot, 250); };
    tryBoot();
  }

  function markRuntimeReady() { state.runtimeReady = true; scheduleBoot(); }
  window.addEventListener('takmap:runtime-ready-i553', markRuntimeReady, {once:true});
  let readinessChecks = 0;
  const awaitRuntime = () => {
    readinessChecks += 1;
    if (document.documentElement.dataset.takMapRuntime === 'ready') return markRuntimeReady();
    if (readinessChecks < 120) setTimeout(awaitRuntime,250);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => setTimeout(awaitRuntime,50), {once:true});
  else setTimeout(awaitRuntime,50);
})(window, document);
