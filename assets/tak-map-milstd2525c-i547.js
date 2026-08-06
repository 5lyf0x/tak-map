/* TAK Map i547 MIL-STD-2525C resolver with Data Sync deletion tombstones. */
(function (w, d) {
  'use strict';

  const VERSION = 'i547';
  const AFFILIATION_TO_CODE = Object.freeze({ f: 'F', h: 'H', n: 'N', u: 'U' });
  const DIMENSION_TO_CODE = Object.freeze({ g: 'G', a: 'A', s: 'S', u: 'U', p: 'P', e: 'E' });
  const catalogState = {
    loaded: false,
    loading: null,
    icons: [],
    byName: new Map(),
    bySidc: new Map(),
    aliasesBySidc: new Map(),
    byCore: new Map(),
    fileBySidc: new Map(),
    error: ''
  };
  const baseFunctions = Object.create(null);
  const exactMissionPointUids = new Set();
  const deletedMissionPointUids = new Map();
  let missionRefreshTimer = 0;

  function text(value) {
    try { return String(value == null ? '' : value).trim(); } catch (_) { return ''; }
  }

  function attr(value) {
    return text(value).replace(/[&<>"']/g, function (ch) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch];
    });
  }

  function cleanName(value) {
    let raw = text(value).split('/').pop().split('\\').pop().replace(/\.svg$/i, '');
    return raw.replace(/[^A-Za-z0-9._-]/g, '');
  }

  function normalizeSidc(value) {
    let raw = text(value).toUpperCase().replace(/\*/g, '-').replace(/[^A-Z0-9-]/g, '');
    if (raw.length < 4 || raw[0] !== 'S') return '';
    return (raw + '---------------').slice(0, 15);
  }

  function sidcCore(value) {
    const sidc = normalizeSidc(value);
    return sidc ? sidc.slice(0, 4) + sidc.slice(4, 10) : '';
  }

  function significantFunction(value) {
    const sidc = normalizeSidc(value);
    return sidc ? sidc.slice(4, 10).replace(/-+$/g, '') : '';
  }

  function cotTypeToSidc(value) {
    const raw = text(value);
    const parts = raw.toLowerCase().split(/-+/).filter(Boolean);
    if (parts.length < 3 || parts[0] !== 'a') return '';
    const affiliation = AFFILIATION_TO_CODE[parts[1]];
    const dimension = DIMENSION_TO_CODE[parts[2]];
    if (!affiliation || !dimension) return '';
    const functionId = parts.slice(3).join('').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
    return ('S' + affiliation + dimension + 'P' + functionId + '---------------').slice(0, 15);
  }

  function propsOf(object) {
    return object && typeof object.properties === 'object' && object.properties ? object.properties : {};
  }

  function nestedObjects(object) {
    const out = [];
    const seen = new Set();
    const stack = [{ value: object, depth: 0 }];
    while (stack.length && out.length < 96) {
      const item = stack.pop();
      const value = item && item.value;
      const depth = item && item.depth || 0;
      if (!value || typeof value !== 'object' || Array.isArray(value) || seen.has(value)) continue;
      seen.add(value);
      out.push(value);
      if (depth >= 4) continue;
      for (const nested of Object.values(value)) {
        if (nested && typeof nested === 'object' && !Array.isArray(nested)) {
          stack.push({ value: nested, depth: depth + 1 });
        }
      }
    }
    return out;
  }

  function objectValues(object, keys) {
    const out = [];
    for (const source of nestedObjects(object)) {
      for (const key of keys) {
        const value = source[key];
        if (value != null && text(value)) out.push(value);
      }
    }
    return out;
  }

  function fileExists(file) {
    const name = cleanName(file);
    if (!name) return false;
    try {
      if (typeof MIL2525_ICON_FILES !== 'undefined' && MIL2525_ICON_FILES && MIL2525_ICON_FILES.has(name + '.svg')) return true;
    } catch (_) {}
    return catalogState.byName.has(name.toLowerCase());
  }

  function rememberIcon(icon) {
    const name = cleanName(icon && icon.name);
    const sidc = normalizeSidc(icon && icon.sidc);
    if (!name || !sidc) return;
    const row = Object.assign({}, icon, { name, sidc });
    catalogState.icons.push(row);
    catalogState.byName.set(name.toLowerCase(), row);
    if (!catalogState.bySidc.has(sidc)) catalogState.bySidc.set(sidc, row);
    const aliases = catalogState.aliasesBySidc.get(sidc) || [];
    aliases.push(name);
    catalogState.aliasesBySidc.set(sidc, aliases);
    const core = sidcCore(sidc);
    const coreRows = catalogState.byCore.get(core) || [];
    coreRows.push(row);
    catalogState.byCore.set(core, coreRows);
  }

  function resetCatalog(raw) {
    catalogState.icons = [];
    catalogState.byName.clear();
    catalogState.bySidc.clear();
    catalogState.aliasesBySidc.clear();
    catalogState.byCore.clear();
    catalogState.fileBySidc.clear();
    for (const row of Array.isArray(raw) ? raw : []) rememberIcon(row);
    catalogState.loaded = catalogState.icons.length > 0;
    return catalogState.icons;
  }

  function embeddedFileForSidc(sidc) {
    try {
      if (typeof MIL2525_ICON_BY_SIDC !== 'undefined' && MIL2525_ICON_BY_SIDC && MIL2525_ICON_BY_SIDC[sidc]) {
        const name = cleanName(MIL2525_ICON_BY_SIDC[sidc]);
        if (fileExists(name)) return name + '.svg';
      }
    } catch (_) {}
    return '';
  }

  function canonicalFileForSidc(value) {
    const sidc = normalizeSidc(value);
    if (!sidc) return '';
    if (catalogState.fileBySidc.has(sidc)) return catalogState.fileBySidc.get(sidc);

    const remember = function (file) {
      const resolved = file || '';
      catalogState.fileBySidc.set(sidc, resolved);
      return resolved;
    };

    const exact = catalogState.bySidc.get(sidc);
    if (exact && fileExists(exact.name)) return remember(exact.name + '.svg');
    const embeddedExact = embeddedFileForSidc(sidc);
    if (embeddedExact) return remember(embeddedExact);

    // Some 2525C families require a modifier while CoT only carries the
    // affiliation, battle dimension and six-character function hierarchy.
    // A same-core match is safe; prefer the catalog's canonical first alias.
    const sameCore = catalogState.byCore.get(sidcCore(sidc)) || [];
    const distinctCoreSidcs = new Set(sameCore.map(function (row) { return normalizeSidc(row.sidc); }).filter(Boolean));
    if (distinctCoreSidcs.size === 1 && sameCore.length && fileExists(sameCore[0].name)) return remember(sameCore[0].name + '.svg');

    // Controlled parent fallback. A requested child may use an existing parent,
    // but a generic parent must never be mapped to an arbitrary child.
    const requestedFunction = significantFunction(sidc);
    let best = '';
    let bestLength = -1;
    const consider = function (candidateSidc, fileName) {
      const candidate = normalizeSidc(candidateSidc);
      const file = cleanName(fileName);
      if (!candidate || !file || !fileExists(file)) return;
      if (candidate.slice(0, 4) !== sidc.slice(0, 4)) return;
      const candidateFunction = significantFunction(candidate);
      if (!candidateFunction || !requestedFunction.startsWith(candidateFunction)) return;
      // Equal-length function codes with different SIDC modifiers are siblings,
      // not parent/child fallbacks. Choosing one would display a wrong symbol.
      if (candidateFunction.length >= requestedFunction.length) return;
      if (candidateFunction.length > bestLength) {
        best = file + '.svg';
        bestLength = candidateFunction.length;
      }
    };
    for (const [candidateSidc, icon] of catalogState.bySidc.entries()) consider(candidateSidc, icon.name);
    try {
      if (typeof MIL2525_ICON_BY_SIDC !== 'undefined' && MIL2525_ICON_BY_SIDC) {
        for (const candidateSidc of Object.keys(MIL2525_ICON_BY_SIDC)) consider(candidateSidc, MIL2525_ICON_BY_SIDC[candidateSidc]);
      }
    } catch (_) {}
    return remember(best);
  }

  function xmlStrings(object) {
    const out = [];
    for (const source of nestedObjects(object)) {
      for (const value of Object.values(source)) {
        if (typeof value === 'string' && value.includes('<')) out.push(value);
      }
    }
    return out.slice(0, 16);
  }

  function metadataFromXml(object) {
    const result = { name: '', sidc: '', cotType: '', iconsetPath: '' };
    for (const xml of xmlStrings(object)) {
      let match = xml.match(/<takmap_point\b[^>]*\bmil2525Name=["']([^"']+)["']/i);
      if (match && !result.name) result.name = match[1];
      match = xml.match(/<takmap_point\b[^>]*\bsidc=["']([^"']+)["']/i);
      if (match && !result.sidc) result.sidc = match[1];
      match = xml.match(/<event\b[^>]*\btype=["']([^"']+)["']/i);
      if (match && !result.cotType) result.cotType = match[1];
      match = xml.match(/<usericon\b[^>]*\biconsetpath=["']([^"']+)["']/i);
      if (match && !result.iconsetPath) result.iconsetPath = match[1];
    }
    return result;
  }

  function iconsetCandidates(value) {
    const raw = text(value);
    const names = [];
    const sidcs = [];
    const cotTypes = [];
    if (!raw) return { names, sidcs, cotTypes };
    for (const token of raw.split(/[\\/|;,\s]+/).filter(Boolean)) {
      const name = cleanName(token);
      if (name) names.push(name);
      const sidc = normalizeSidc(token);
      if (sidc) sidcs.push(sidc);
      if (/^a-[fhnu]-[gasupe](?:-|$)/i.test(token)) cotTypes.push(token);
    }
    const sidcMatches = raw.toUpperCase().match(/S[FHNU][GASUPE][A-Z0-9-]{12}/g) || [];
    sidcs.push.apply(sidcs, sidcMatches);
    const cotMatches = raw.match(/a-[fhnu]-[gasupe](?:-[a-z0-9]+){0,6}/ig) || [];
    cotTypes.push.apply(cotTypes, cotMatches);
    return { names, sidcs, cotTypes };
  }

  function resolveByName(value, source) {
    const requestedName = cleanName(value);
    if (!requestedName || !fileExists(requestedName)) return null;
    const icon = catalogState.byName.get(requestedName.toLowerCase()) || {};
    const name = cleanName(icon.name || requestedName);
    return {
      ok: true,
      exact: true,
      source,
      name,
      file: name + '.svg',
      sidc: normalizeSidc(icon.sidc),
      label: text(icon.label)
    };
  }

  function resolveBySidc(value, source) {
    const sidc = normalizeSidc(value);
    if (!sidc) return null;
    const file = canonicalFileForSidc(sidc);
    if (!file) return null;
    const name = cleanName(file);
    const icon = catalogState.byName.get(name.toLowerCase()) || {};
    const coreRows = catalogState.byCore.get(sidcCore(sidc)) || [];
    const distinctCoreSidcs = new Set(coreRows.map(function (row) { return normalizeSidc(row.sidc); }).filter(Boolean));
    return {
      ok: true,
      exact: !!catalogState.bySidc.get(sidc) || distinctCoreSidcs.size === 1 || !!embeddedFileForSidc(sidc),
      source,
      name,
      file,
      // Preserve the source SIDC even when a less-specific catalog parent is
      // used as the visual fallback. Never rewrite source identity to the fallback.
      sidc,
      catalogSidc: normalizeSidc(icon.sidc),
      inputSidc: sidc,
      label: text(icon.label)
    };
  }

  function resolveSymbol(object) {
    const obj = object && typeof object === 'object' ? object : {};
    const xml = metadataFromXml(obj);

    // A standard SIDC is authoritative when present. This avoids a stale local
    // filename overriding current symbol identity from ATAK or another TAK app.
    const sidcValues = objectValues(obj, [
      'sidc', 'SIDC', 'sidc2525', 'sidc_2525c', 'mil2525_sidc', 'milstd2525_sidc',
      'symbol_id', 'symbolId', 'symbolID', 'symbol_code', 'symbolCode'
    ]);
    if (xml.sidc) sidcValues.push(xml.sidc);
    for (const value of sidcValues) {
      const resolved = resolveBySidc(value, 'sidc');
      if (resolved) return resolved;
    }

    const nameValues = objectValues(obj, [
      'mil2525_name', 'milstd2525_name', 'mil2525_file', 'mil2525_svg',
      'symbol_name', 'symbolName', 'icon_name', 'iconName'
    ]);
    if (xml.name) nameValues.push(xml.name);
    for (const value of nameValues) {
      const resolved = resolveByName(value, 'exact-name');
      if (resolved) return resolved;
    }

    const iconsetValues = objectValues(obj, [
      'iconsetPath', 'iconsetpath', 'iconset_path', '@iconsetpath', '@iconsetPath',
      'usericon_path', 'user_icon_path', 'icon_path', 'iconPath', 'icon'
    ]);
    if (xml.iconsetPath) iconsetValues.push(xml.iconsetPath);
    for (const value of iconsetValues) {
      const candidates = iconsetCandidates(value);
      for (const sidc of candidates.sidcs) {
        const resolved = resolveBySidc(sidc, 'iconset-sidc');
        if (resolved) return resolved;
      }
      for (const name of candidates.names) {
        const resolved = resolveByName(name, 'iconset-name');
        if (resolved) return resolved;
      }
      for (const cotType of candidates.cotTypes) {
        const resolved = resolveBySidc(cotTypeToSidc(cotType), 'iconset-cot-type');
        if (resolved) return resolved;
      }
    }

    const typeValues = objectValues(obj, ['atak_cot_type', 'cot_type', 'event_type', 'eventType', 'type']);
    if (xml.cotType) typeValues.push(xml.cotType);
    for (const value of typeValues) {
      const directSidc = normalizeSidc(value);
      if (directSidc) {
        const direct = resolveBySidc(directSidc, 'type-sidc');
        if (direct) return direct;
      }
      const resolved = resolveBySidc(cotTypeToSidc(value), 'cot-type');
      if (resolved) return resolved;
    }

    return { ok: false, exact: false, source: 'none', name: '', file: '', sidc: '', label: '' };
  }

  function promote(object) {
    if (!object || typeof object !== 'object') return object;
    const props = propsOf(object);
    const keys = [
      'mil2525_name', 'milstd2525_name', 'mil2525_label', 'mil2525_file', 'mil2525_svg',
      'sidc', 'SIDC', 'mil2525_sidc', 'cot_type', 'atak_cot_type', 'event_type',
      'iconsetPath', 'iconsetpath', 'symbol_code', 'symbolCode'
    ];
    for (const key of keys) {
      if ((object[key] == null || object[key] === '') && props[key] != null && props[key] !== '') object[key] = props[key];
    }
    const resolved = resolveSymbol(object);
    if (resolved.ok) {
      object.sidc = resolved.sidc || object.sidc || '';
      object.SIDC = resolved.sidc || object.SIDC || '';
      object.mil2525_name = resolved.name;
      object.mil2525_file = resolved.file;
      object.mil2525_label = object.mil2525_label || resolved.label;
      object.symbol_resolution_i538 = {
        version: VERSION,
        source: resolved.source,
        exact: resolved.exact,
        input_sidc: resolved.inputSidc || '',
        catalog_sidc: resolved.catalogSidc || resolved.sidc || ''
      };
    }
    return object;
  }

  function affiliationSlug(object) {
    const resolved = resolveSymbol(object);
    const sidc = resolved.sidc || normalizeSidc(object && (object.sidc || object.SIDC));
    const code = sidc && sidc[1];
    if (code === 'H') return 'hostile';
    if (code === 'N') return 'neutral';
    if (code === 'U') return 'unknown';
    return 'friendly';
  }

  function imageError(img) {
    try {
      img.onerror = null;
      const host = img.closest('.tak-icon-wrap');
      if (!host) return;
      const object = { sidc: img.dataset.sidc || '', type: img.dataset.cotType || '' };
      if (typeof w.milShape === 'function') host.innerHTML = w.milShape(affiliationSlug(object), '', '');
    } catch (_) {}
  }

  function iconHtml(object) {
    const promoted = promote(Object.assign({}, object || {}));
    const resolved = resolveSymbol(promoted);
    if (!resolved.ok || !resolved.file) {
      if (typeof w.milShape === 'function') return '<div class="tak-icon-wrap">' + w.milShape(affiliationSlug(promoted), '', '') + '</div>';
      return '';
    }
    const alt = attr(promoted.callsign || promoted.name || promoted.uid || resolved.label || resolved.name);
    const src = '/mil2525/svg/' + encodeURIComponent(resolved.name) + '.svg';
    return '<div class="tak-icon-wrap"><img class="tak-mil2525-img" src="' + src + '" alt="' + alt + '" data-sidc="' + attr(resolved.sidc) + '" data-cot-type="' + attr(promoted.cot_type || promoted.type) + '" onerror="TakMapMilStd2525CI538.onImageError(this)"></div>';
  }

  async function loadCatalog(force) {
    if (!force && catalogState.loaded) return catalogState.icons;
    if (!force && catalogState.loading) return catalogState.loading;
    catalogState.loading = (async function () {
      try {
        const response = await w.fetch('/mil2525/icons.json?i538=' + Date.now(), { cache: 'no-store', credentials: 'same-origin' });
        if (!response.ok) throw new Error('HTTP ' + response.status);
        resetCatalog(await response.json());
        if (!catalogState.loaded) throw new Error('MIL-STD-2525C catalog was empty.');
        catalogState.error = '';
        try {
          w.dispatchEvent(new CustomEvent('takmap:milstd-catalog-ready', { detail: { version: VERSION, count: catalogState.icons.length } }));
        } catch (_) {}
        return catalogState.icons;
      } catch (error) {
        catalogState.error = text(error && error.message || error);
        return catalogState.icons;
      } finally {
        catalogState.loading = null;
      }
    })();
    return catalogState.loading;
  }


  function uidOf(object) {
    for (const source of nestedObjects(object)) {
      for (const key of ['uid', 'cot_uid', 'event_uid', 'id']) {
        const uid = text(source[key]);
        if (uid) return uid.toLowerCase();
      }
    }
    for (const xml of xmlStrings(object)) {
      const match = xml.match(/<event\b[^>]*\buid=["']([^"']+)["']/i);
      if (match) return text(match[1]).toLowerCase();
    }
    return '';
  }

  function pointLike(object) {
    if (!object || typeof object !== 'object') return false;
    const geometry = object.geometry;
    if (geometry && typeof geometry === 'object' && text(geometry.type).toLowerCase() === 'point') return true;
    if (text(geometry).toLowerCase() === 'point') return true;
    const lat = Number(object.lat != null ? object.lat : object.latitude);
    const lon = Number(object.lon != null ? object.lon : object.lng != null ? object.lng : object.longitude);
    return Number.isFinite(lat) && Number.isFinite(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180;
  }

  function eventTimeMs(object) {
    const candidates = [];
    for (const source of nestedObjects(object)) {
      for (const key of ['updated', 'timestamp', 'time', 'start', 'event_time', 'eventTime', 'stale']) {
        if (source[key] != null && text(source[key])) candidates.push(source[key]);
      }
    }
    for (const value of candidates) {
      if (typeof value === 'number' && Number.isFinite(value)) return value > 1e12 ? value : value * 1000;
      const parsed = Date.parse(text(value));
      if (Number.isFinite(parsed)) return parsed;
    }
    return 0;
  }

  function learnDeletedMissionUids(payload) {
    const block = payload && payload.data_sync_deleted_uid_tombstones_i547;
    const rows = block && Array.isArray(block.tombstones) ? block.tombstones : [];
    const advertised = new Set();
    for (const row of rows) {
      const uid = text(row && row.uid).toLowerCase();
      if (!uid) continue;
      advertised.add(uid);
      const cutoffMs = Number(row && row.cutoff_epoch || 0) * 1000;
      deletedMissionPointUids.set(uid, {
        cutoffMs: Number.isFinite(cutoffMs) && cutoffMs > 0 ? cutoffMs : Date.now(),
        observedAtMs: Number(row && row.observed_at_epoch || 0) * 1000 || Date.now()
      });
    }
    for (const uid of Array.from(deletedMissionPointUids.keys())) {
      if (exactMissionPointUids.has(uid)) deletedMissionPointUids.delete(uid);
      else if (rows.length && !advertised.has(uid)) deletedMissionPointUids.delete(uid);
    }
    return deletedMissionPointUids;
  }

  function liveUidSuppressed(row) {
    const uid = uidOf(row);
    if (!uid) return false;
    if (exactMissionPointUids.has(uid)) return true;
    const tombstone = deletedMissionPointUids.get(uid);
    if (!tombstone) return false;
    const eventMs = eventTimeMs(row);
    if (eventMs && eventMs > Number(tombstone.cutoffMs || 0) + 1000) {
      deletedMissionPointUids.delete(uid);
      return false;
    }
    return true;
  }

  function learnMissionPointUids(payload) {
    const next = new Set();
    for (const row of payload && Array.isArray(payload.objects) ? payload.objects : []) {
      if (!pointLike(row)) continue;
      const uid = uidOf(row);
      if (uid) next.add(uid);
    }
    let changed = next.size !== exactMissionPointUids.size;
    if (!changed) for (const uid of next) if (!exactMissionPointUids.has(uid)) { changed = true; break; }
    exactMissionPointUids.clear();
    for (const uid of next) exactMissionPointUids.add(uid);
    learnDeletedMissionUids(payload);
    if (changed || deletedMissionPointUids.size) {
      clearTimeout(missionRefreshTimer);
      missionRefreshTimer = setTimeout(function () {
        try { if (typeof w.refreshCot === 'function') w.refreshCot(); } catch (_) {}
        try { if (typeof w.fetchEudsForDropdown === 'function') w.fetchEudsForDropdown(); } catch (_) {}
      }, 40);
    }
    return exactMissionPointUids;
  }

  function filterLivePayload(payload) {
    if (!payload || typeof payload !== 'object' || (!exactMissionPointUids.size && !deletedMissionPointUids.size)) return payload;
    for (const key of ['markers', 'euds']) {
      if (!Array.isArray(payload[key])) continue;
      payload[key] = payload[key].filter(function (row) {
        return !liveUidSuppressed(row);
      });
    }
    return payload;
  }

  function cloneJsonResponse(response, payload) {
    try {
      const headers = new Headers(response.headers || undefined);
      headers.set('content-type', 'application/json; charset=utf-8');
      headers.set('x-tak-map-mission-uid-ownership', VERSION);
      return new Response(JSON.stringify(payload), {
        status: response.status,
        statusText: response.statusText,
        headers
      });
    } catch (_) {
      return response;
    }
  }

  function patchFetch() {
    const current = w.fetch;
    if (typeof current !== 'function' || current.__takMapI538) return;
    const wrapper = function (input, init) {
      const url = text(input && input.url || input);
      const promise = current.apply(this, arguments);
      if (!/\/api\/tak-map\/(data-sync|cot|euds)(?:[/?]|$)/.test(url)) return promise;
      return Promise.resolve(promise).then(async function (response) {
        try {
          if (!response || !response.ok || typeof response.clone !== 'function') return response;
          const payload = await response.clone().json();
          if (/\/api\/tak-map\/data-sync(?:[/?]|$)/.test(url)) {
            learnMissionPointUids(payload);
            return response;
          }
          filterLivePayload(payload);
          return cloneJsonResponse(response, payload);
        } catch (_) {
          return response;
        }
      });
    };
    wrapper.__takMapI538 = true;
    wrapper.__takMapI538Base = current;
    w.fetch = wrapper;
  }

  function generatedWrapper(object) {
    const resolved = resolveSymbol(promote(object || {}));
    if (resolved.ok) return resolved.file;
    const fallback = baseFunctions.generatedMil2525File;
    return typeof fallback === 'function' ? fallback.call(this, object) : '';
  }
  generatedWrapper.__takMapI538 = true;

  function explicitSidcWrapper(object) {
    return resolveSymbol(object).sidc || '';
  }
  explicitSidcWrapper.__takMapI538 = true;

  function wrapCollectionFunction(name, promoteItems) {
    const current = w[name];
    if (typeof current !== 'function' || current.__takMapI538) return;
    const wrapper = function () {
      try { promoteItems(arguments); } catch (_) {}
      return current.apply(this, arguments);
    };
    wrapper.__takMapI538 = true;
    w[name] = wrapper;
  }

  function patchGlobals() {
    patchFetch();
    w.cotTypeToSidc = cotTypeToSidc;
    w.sidcFileFromSidc = canonicalFileForSidc;
    w.explicitSidc = explicitSidcWrapper;
    if (w.generatedMil2525File !== generatedWrapper) {
      if (typeof w.generatedMil2525File === 'function' && !w.generatedMil2525File.__takMapI538) baseFunctions.generatedMil2525File = w.generatedMil2525File;
      w.generatedMil2525File = generatedWrapper;
    }
    w.mil2525IconHtml = iconHtml;

    wrapCollectionFunction('addObjectLayer', function (args) { promote(args[1]); });
    wrapCollectionFunction('drawDataSyncObjects', function (args) { for (const item of args[0] || []) promote(item); });
    wrapCollectionFunction('importedFeatures', function () {});
  }

  function tunePickerImages() {
    try {
      d.querySelectorAll('#milGrid img,#milPreview img').forEach(function (img) {
        img.loading = 'lazy';
        img.decoding = 'async';
        img.setAttribute('fetchpriority', 'low');
      });
    } catch (_) {}
  }

  function audit() {
    let nameFailures = 0;
    let sidcFailures = 0;
    let duplicateSidcs = 0;
    for (const icon of catalogState.icons) {
      if (!fileExists(icon.name)) nameFailures++;
      if (!canonicalFileForSidc(icon.sidc)) sidcFailures++;
    }
    for (const aliases of catalogState.aliasesBySidc.values()) if (aliases.length > 1) duplicateSidcs++;
    const brokenVisibleImages = Array.from(d.querySelectorAll('.tak-mil2525-img,#milGrid img')).filter(function (img) {
      return img.complete && img.naturalWidth === 0;
    }).length;
    const airDefense = resolveSymbol({ type: 'a-f-G-U-C-D' });
    const emergency = resolveSymbol({ type: 'a-f-E-P' });
    const installation = resolveSymbol({ type: 'a-f-G-I' });
    const genericUnit = resolveSymbol({ type: 'a-f-G-U' });
    return {
      version: VERSION,
      catalogLoaded: catalogState.loaded,
      catalogCount: catalogState.icons.length,
      nameFailures,
      sidcFailures,
      duplicateSidcs,
      brokenVisibleImages,
      catalogError: catalogState.error,
      airDefenseFile: airDefense.file || '',
      emergencyFile: emergency.file || '',
      installationFile: installation.file || '',
      genericUnitFile: genericUnit.file || '',
      emergencyDimensionSupported: cotTypeToSidc('a-f-E-P') === 'SFEPP----------',
      controlledParentFallback: true,
      arbitraryChildFallbackDisabled: true,
      exactMissionPointUidCount: exactMissionPointUids.size,
      deletedMissionPointUidCount: deletedMissionPointUids.size,
      exactMissionUidOwnership: true,
      deletionTombstones: true,
      fetchFilterPatched: !!(w.fetch && w.fetch.__takMapI538)
    };
  }

  function boot() {
    patchGlobals();
    try { if (w.__takMapLastDataSyncJsonI547) learnMissionPointUids(w.__takMapLastDataSyncJsonI547); } catch (_) {}
    loadCatalog(false);
    tunePickerImages();
    [250, 900, 2200, 5000].forEach(function (ms) { setTimeout(patchGlobals, ms); });
    [700, 2500].forEach(function (ms) { setTimeout(tunePickerImages, ms); });
    d.addEventListener('click', function (event) {
      try {
        if (event.target && event.target.closest && event.target.closest('#milPicker,[onclick*="openMilPicker"],#milPreview')) {
          setTimeout(tunePickerImages, 0);
        }
      } catch (_) {}
    }, true);
  }

  const exportedApi = Object.freeze({
    version: VERSION,
    normalizeSidc,
    cotTypeToSidc,
    resolveSymbol,
    promote,
    fileForSidc: canonicalFileForSidc,
    onImageError: imageError,
    loadCatalog,
    audit,
    learnMissionPointUids,
    learnDeletedMissionUids,
    filterLivePayload,
    missionPointUids: function () { return Array.from(exactMissionPointUids); },
    deletedMissionPointUids: function () { return Array.from(deletedMissionPointUids.keys()); },
    _resetCatalogForTest: resetCatalog
  });
  w.TakMapMilStd2525CI547 = exportedApi;
  w.TakMapMilStd2525CI538 = exportedApi;

  if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})(window, document);
