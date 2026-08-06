/* TAK Map i536: NRT satellite imagery with per-user Copernicus Sentinel-2. */
(function (w, d) {
  'use strict';

  const VERSION = 'i536';
  const NRT_ID = 'nrt_satellite_imagery';
  const STORE_KEY = 'takMapNrtSatelliteI535';
  const LEGACY_STORE_KEY = 'takMapNrtSatelliteI525';
  const LEGACY_STORE_KEY_2 = 'takMapNrtSatelliteI524';
  const TRANSPARENT_TILE = 'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=';
  const LANDSAT_SERVICE = 'https://landsat2.arcgis.com/arcgis/rest/services/Landsat8_Views/ImageServer';
  const LANDSAT_QUERY = LANDSAT_SERVICE + '/query';
  const LANDSAT_EXPORT = LANDSAT_SERVICE + '/exportImage';
  const NASA_ATTRIBUTION = 'NASA EOSDIS GIBS';
  const SENTINEL_ATTRIBUTION = 'Copernicus Sentinel-2 imagery processed by Sentinel Hub';
  const SENTINEL_PRODUCTS = Object.freeze({
    true_color: Object.freeze({label:'True Color',group:'Visual Composites',description:'Natural-color surface reflectance using red, green, and blue bands.'}),
    false_color: Object.freeze({label:'False Color · Vegetation',group:'Visual Composites',description:'Near-infrared composite that makes healthy vegetation appear bright red.'}),
    swir: Object.freeze({label:'SWIR Composite',group:'Visual Composites',description:'Short-wave infrared composite useful for moisture, burn scars, and geology.'}),
    ndvi: Object.freeze({label:'NDVI',group:'Vegetation',description:'Normalized Difference Vegetation Index for vegetation vigor and coverage.'}),
    ndre: Object.freeze({label:'NDRE',group:'Vegetation',description:'Red-edge vegetation index useful for chlorophyll and crop stress.'}),
    ndmi: Object.freeze({label:'NDMI / NDII',group:'Water / Moisture',description:'Vegetation and canopy moisture using near-infrared and SWIR.'}),
    ndwi: Object.freeze({label:'NDWI',group:'Water / Moisture',description:'Highlights open water using green and near-infrared bands.'}),
    mndwi: Object.freeze({label:'MNDWI',group:'Water / Moisture',description:'Modified water index that suppresses built-up land more strongly.'}),
    nbr: Object.freeze({label:'NBR / Burn Scar',group:'Fire / Burn',description:'Normalized Burn Ratio for burned-area and burn-severity assessment.'}),
    ndsi: Object.freeze({label:'NDSI',group:'Snow / Ice',description:'Normalized Difference Snow Index for snow and ice discrimination.'}),
    ndbi: Object.freeze({label:'NDBI',group:'Urban / Soil',description:'Normalized Difference Built-up Index for urban and developed surfaces.'}),
    bare_soil: Object.freeze({label:'Bare Soil',group:'Urban / Soil',description:'Bare Soil Index highlighting exposed soil and sparse vegetation.'}),
    scl: Object.freeze({label:'Scene Classification',group:'Quality / Masking',description:'Sentinel-2 Level-2A scene classes including vegetation, water, cloud, and snow.'}),
    cloud_mask: Object.freeze({label:'Cloud Mask',group:'Quality / Masking',description:'Categorical cloud, cirrus, and cloud-shadow mask from scene classification.'}),
    cloud_probability: Object.freeze({label:'Cloud Probability',group:'Quality / Masking',description:'Cloud probability from 0 to 100 percent.'}),
  });

  const SOURCES = Object.freeze({
    sentinel2_cdse: Object.freeze({
      id: 'sentinel2_cdse',
      label: 'Copernicus Sentinel-2 L2A',
      kind: 'sentinel',
      attribution: SENTINEL_ATTRIBUTION,
      maxNativeZoom: 14,
      supportsCloud: true,
      supportsRendering: true,
      supportsDateSearch: true,
      requiresPerUserCredentials: true,
    }),
    landsat_esri: Object.freeze({
      id: 'landsat_esri',
      label: 'Landsat 8 · Esri',
      kind: 'landsat',
      attribution: 'Landsat imagery: USGS/NASA; image service by Esri',
      maxNativeZoom: 13,
      supportsCloud: true,
      supportsRendering: true,
      supportsDateSearch: true,
    }),
    viirs_noaa21: Object.freeze({
      id: 'viirs_noaa21',
      label: 'NASA VIIRS · NOAA-21 True Color',
      kind: 'gibs',
      layer: 'VIIRS_NOAA21_CorrectedReflectance_TrueColor',
      attribution: NASA_ATTRIBUTION,
      maxNativeZoom: 9,
      supportsCloud: false,
      supportsRendering: false,
      supportsDateSearch: false,
    }),
    viirs_noaa20: Object.freeze({
      id: 'viirs_noaa20',
      label: 'NASA VIIRS · NOAA-20 True Color',
      kind: 'gibs',
      layer: 'VIIRS_NOAA20_CorrectedReflectance_TrueColor',
      attribution: NASA_ATTRIBUTION,
      maxNativeZoom: 9,
      supportsCloud: false,
      supportsRendering: false,
      supportsDateSearch: false,
    }),
    viirs_snpp: Object.freeze({
      id: 'viirs_snpp',
      label: 'NASA VIIRS · Suomi NPP True Color',
      kind: 'gibs',
      layer: 'VIIRS_SNPP_CorrectedReflectance_TrueColor',
      attribution: NASA_ATTRIBUTION,
      maxNativeZoom: 9,
      supportsCloud: false,
      supportsRendering: false,
      supportsDateSearch: false,
    }),
  });

  let originalSetBasemap = null;
  let originalRenderBasemaps = null;
  let wrapped = false;
  let nrtMode = false;
  let lastConventionalId = '';
  let leftLayer = null;
  let rightLayer = null;
  let activeComparison = false;
  let overlay = null;
  let dragging = false;
  let dragWasEnabled = false;
  let tileErrors = 0;
  let mapEventsBound = false;
  let landsatSceneGroups = [];
  let sentinelSceneGroups = [];
  let sentinelStatusCache = null;
  let dividerPercent = 50;
  let labelResizeObserver = null;
  let labelMutationObserver = null;
  let labelPositionFrame = 0;

  const by = (id) => d.getElementById(id);
  const clamp = (n, a, b) => Math.max(a, Math.min(b, Number(n)));
  const isoDay = (value) => new Date(value).toISOString().slice(0, 10);

  function defaultDates() {
    const newer = new Date();
    newer.setUTCDate(newer.getUTCDate() - 1);
    const older = new Date(newer.getTime() - 7 * 86400000);
    return { older: isoDay(older), newer: isoDay(newer) };
  }

  function defaults() {
    const dates = defaultDates();
    return {
      source: 'landsat_esri',
      opacity: 100,
      slider: 50,
      landsat: {
        days: 365,
        maxcc: 50,
        rendering: 'Natural Color with DRA',
        leftDate: '',
        rightDate: '',
      },
      gibs: {
        older: dates.older,
        newer: dates.newer,
      },
      sentinel: {
        days: 180,
        maxcc: 35,
        product: 'true_color',
        leftDate: '',
        rightDate: '',
      },
    };
  }

  function readSettings() {
    const base = defaults();
    try {
      const raw = localStorage.getItem(STORE_KEY) || localStorage.getItem(LEGACY_STORE_KEY) || localStorage.getItem(LEGACY_STORE_KEY_2) || '{}';
      const saved = JSON.parse(raw);
      const settings = {
        source: SOURCES[saved.source] ? saved.source : base.source,
        opacity: clamp(saved.opacity == null ? base.opacity : saved.opacity, 10, 100),
        slider: clamp(saved.slider == null ? base.slider : saved.slider, 2, 98),
        landsat: Object.assign({}, base.landsat, saved.landsat || {}),
        gibs: Object.assign({}, base.gibs, saved.gibs || {}),
        sentinel: Object.assign({}, base.sentinel, saved.sentinel || {}),
      };
      if (!localStorage.getItem(STORE_KEY) && raw !== '{}') saveSettings(settings);
      return settings;
    } catch (_) {
      return base;
    }
  }

  function saveSettings(settings) {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(settings));
    } catch (_) {}
  }

  function currentSettings() {
    const prior = readSettings();
    return {
      source: String(by('nrtSatSourceI525')?.value || prior.source),
      opacity: clamp(by('nrtSatOpacityI525')?.value || prior.opacity, 10, 100),
      slider: clamp(dividerPercent == null ? prior.slider : dividerPercent, 2, 98),
      landsat: {
        days: Number(by('nrtSatLandsatDaysI525')?.value || prior.landsat.days || 365),
        maxcc: Number(by('nrtSatLandsatCloudI525')?.value || prior.landsat.maxcc || 50),
        rendering: String(by('nrtSatLandsatRenderingI525')?.value || prior.landsat.rendering || 'Natural Color with DRA'),
        leftDate: String(by('nrtSatLandsatLeftI525')?.value || prior.landsat.leftDate || ''),
        rightDate: String(by('nrtSatLandsatRightI525')?.value || prior.landsat.rightDate || ''),
      },
      gibs: {
        older: String(by('nrtSatGibsOlderI525')?.value || prior.gibs.older || ''),
        newer: String(by('nrtSatGibsNewerI525')?.value || prior.gibs.newer || ''),
      },
      sentinel: {
        days: Number(by('nrtSatSentinelDaysI535')?.value || prior.sentinel.days || 180),
        maxcc: Number(by('nrtSatSentinelCloudI535')?.value || prior.sentinel.maxcc || 35),
        product: String(by('nrtSatSentinelProductI535')?.value || prior.sentinel.product || 'true_color'),
        leftDate: String(by('nrtSatSentinelLeftI535')?.value || prior.sentinel.leftDate || ''),
        rightDate: String(by('nrtSatSentinelRightI535')?.value || prior.sentinel.rightDate || ''),
      },
    };
  }

  function sourceDef() {
    return SOURCES[currentSettings().source] || SOURCES.landsat_esri;
  }

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    }[c]));
  }

  function sentinelProductOptions(current) {
    const groups = {};
    Object.entries(SENTINEL_PRODUCTS).forEach(([id, product]) => {
      (groups[product.group] = groups[product.group] || []).push([id, product]);
    });
    return Object.entries(groups).map(([group, rows]) => '<optgroup label="'+esc(group)+'">'+rows.map(([id,p]) => '<option value="'+esc(id)+'"'+(id===current?' selected':'')+'>'+esc(p.label)+'</option>').join('')+'</optgroup>').join('');
  }

  function sentinelProduct() {
    const id = currentSettings().sentinel.product;
    return SENTINEL_PRODUCTS[id] || SENTINEL_PRODUCTS.true_color;
  }

  async function sentinelStatus(force) {
    if (sentinelStatusCache && !force) return sentinelStatusCache;
    try {
      const response = await fetch('/api/tak-map/account/sentinel-hub', {cache:'no-store', credentials:'same-origin'});
      const payload = await response.json().catch(() => ({ok:false,error:'HTTP '+response.status}));
      sentinelStatusCache = payload;
      return payload;
    } catch (error) {
      sentinelStatusCache = {ok:false, configured:false, error:String(error && error.message || error)};
      return sentinelStatusCache;
    }
  }

  function setStatus(message, kind) {
    const el = by('nrtSatStatusI525');
    if (!el) return;
    el.textContent = String(message || '');
    el.className = 'muted tak-nrt-status-i525 ' + String(kind || '');
  }

  function encode(params) {
    const query = new URLSearchParams();
    Object.keys(params).forEach((key) => query.set(key, String(params[key])));
    return query.toString();
  }

  function mapObject() {
    try {
      return (typeof map !== 'undefined' && map) || w.map || null;
    } catch (_) {
      return w.map || null;
    }
  }

  function configObject() {
    try {
      return (typeof config !== 'undefined' && config) || w.config || {};
    } catch (_) {
      return w.config || {};
    }
  }

  function activeBasemapId() {
    try {
      return String((typeof activeBasemap !== 'undefined' && activeBasemap) || w.activeBasemap || '');
    } catch (_) {
      return String(w.activeBasemap || '');
    }
  }

  function conventionalLabel(id) {
    const row = (configObject().basemaps || []).find((item) => String(item.id) === String(id));
    return row ? String(row.label || row.id || id) : String(id || 'current basemap');
  }

  function chooseFallbackId() {
    const cfg = configObject();
    const rows = cfg.basemaps || [];
    const candidates = [
      lastConventionalId,
      activeBasemapId(),
      cfg.last_basemap,
      cfg.default_basemap,
      'esri_imagery',
      'usgs_imagery_only',
      rows[0] && rows[0].id,
    ];
    for (const candidate of candidates) {
      const id = String(candidate || '');
      if (id && id !== NRT_ID && rows.some((row) => String(row.id) === id)) return id;
    }
    return '';
  }

  function ensureNrtOption() {
    const select = by('basemapSelect');
    if (!select) return false;
    let option = Array.from(select.options || []).find((item) => item.value === NRT_ID);
    if (!option) {
      let group = Array.from(select.querySelectorAll('optgroup')).find((item) => item.label === 'Imagery');
      if (!group) {
        group = d.createElement('optgroup');
        group.label = 'Imagery';
        select.appendChild(group);
      }
      option = d.createElement('option');
      option.value = NRT_ID;
      option.textContent = 'NRT Satellite Imagery';
      group.appendChild(option);
    }
    if (!nrtMode && select.value && select.value !== NRT_ID) lastConventionalId = select.value;
    if (nrtMode) select.value = NRT_ID;
    return true;
  }

  function installStyle() {
    if (by('takMapNrtSatelliteStyleI525')) return;
    const style = d.createElement('style');
    style.id = 'takMapNrtSatelliteStyleI525';
    style.textContent = `
#nrtSatellitePanelI525[hidden]{display:none!important}
#nrtSatellitePanelI525{border-color:rgba(118,181,210,.42)}
#nrtSatellitePanelI525 h2{display:block;margin-bottom:7px}
.tak-nrt-source-i525{display:flex;flex-direction:column;gap:4px;margin-top:8px;color:var(--muted);font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;font-weight:850}
.tak-nrt-source-i525 select,.tak-nrt-grid-i525 select,.tak-nrt-scenes-i525 select,.tak-nrt-grid-i525 input[type=date]{background:#091018;border:1px solid #334553;border-radius:9px;color:var(--text);padding:7px 8px;min-width:0;width:100%;font-size:.76rem;text-transform:none;letter-spacing:0;box-sizing:border-box}
.tak-nrt-grid-i525{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:7px;margin-top:8px}
.tak-nrt-grid-i525 label,.tak-nrt-scenes-i525 label{display:flex;flex-direction:column;gap:4px;color:var(--muted);font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;font-weight:850;min-width:0}
.tak-nrt-scenes-i525{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:7px;margin-top:8px}
.tak-nrt-scenes-i525 label:first-child{color:#d9cda0}.tak-nrt-scenes-i525 label:last-child{color:#b8d9f0}
.tak-nrt-actions-i525{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-top:8px}
.tak-nrt-opacity-label-i525{display:block;margin-top:9px;color:var(--muted);font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;font-weight:850}
#nrtSatOpacityI525.tak-tactical-rail-v442{-webkit-appearance:none;appearance:none;width:100%;height:22px;margin:0;background:transparent;cursor:pointer;outline:none}
#nrtSatOpacityI525.tak-tactical-rail-v442::-webkit-slider-runnable-track{height:12px;border:1px solid #3a4b58;background:linear-gradient(90deg,var(--accent) 0 var(--tak-relief-pct),transparent var(--tak-relief-pct) 100%),repeating-linear-gradient(90deg,rgba(255,255,255,.10) 0 1px,transparent 1px 18px),linear-gradient(180deg,#263540,#111820);clip-path:polygon(6px 0,calc(100% - 6px) 0,100% 6px,100% calc(100% - 6px),calc(100% - 6px) 100%,6px 100%,0 calc(100% - 6px),0 6px);box-shadow:inset 0 1px 2px rgba(255,255,255,.08),inset 0 -2px 3px rgba(0,0,0,.60)}
#nrtSatOpacityI525.tak-tactical-rail-v442::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:16px;height:22px;margin-top:-6px;border:1px solid #ffb083;background:linear-gradient(180deg,#ff9256,#c64718);clip-path:polygon(4px 0,12px 0,16px 4px,16px 18px,12px 22px,4px 22px,0 18px,0 4px);box-shadow:0 0 0 2px rgba(4,8,12,.85),0 0 13px rgba(255,111,46,.45)}
#nrtSatOpacityI525.tak-tactical-rail-v442::-moz-range-track{height:12px;border:1px solid #3a4b58;background:repeating-linear-gradient(90deg,rgba(255,255,255,.10) 0 1px,transparent 1px 18px),linear-gradient(180deg,#263540,#111820)}
#nrtSatOpacityI525.tak-tactical-rail-v442::-moz-range-progress{height:12px;background:var(--accent)}
#nrtSatOpacityI525.tak-tactical-rail-v442::-moz-range-thumb{width:16px;height:22px;border:1px solid #ffb083;border-radius:3px;background:#df581f;box-shadow:0 0 0 2px rgba(4,8,12,.85),0 0 13px rgba(255,111,46,.45)}
.tak-nrt-status-i525{margin-top:7px;line-height:1.35}.tak-nrt-status-i525.ok{color:#71d9a7}.tak-nrt-status-i525.bad{color:#ff857e}.tak-nrt-status-i525.warn{color:#ffcc66}
.tak-nrt-source-note-i525{margin-top:7px;line-height:1.35}
.tak-nrt-product-note-i535{margin-top:7px;padding:7px 8px;border:1px solid rgba(118,181,210,.22);border-radius:8px;background:rgba(118,181,210,.055);line-height:1.35;color:#a9bbc5;font-size:.7rem}
.tak-nrt-compare-overlay-i525{position:absolute;inset:0;z-index:640;pointer-events:none;overflow:hidden}
.tak-nrt-compare-line-i525{position:absolute;top:0;bottom:0;width:8px;margin-left:-4px;border-left:1px solid rgba(255,255,255,.72);border-right:1px solid rgba(0,0,0,.82);background:linear-gradient(90deg,#172027 0%,#7e8a91 24%,#eef2f4 46%,#8a969d 68%,#1a232a 100%);box-shadow:0 0 0 1px rgba(0,0,0,.58),inset 1px 0 0 rgba(255,255,255,.28),inset -2px 0 2px rgba(0,0,0,.55),0 0 14px rgba(0,0,0,.62);pointer-events:none}
.tak-nrt-compare-line-i525:before{content:"";position:absolute;top:0;bottom:0;left:2px;width:1px;background:rgba(255,255,255,.58)}
.tak-nrt-compare-knob-i525{position:absolute;top:50%;left:50%;width:62px;height:48px;transform:translate(-50%,-50%);border:1px solid rgba(228,235,239,.88);border-radius:13px;background:linear-gradient(180deg,#b9c2c7 0%,#737f86 42%,#4a555c 58%,#232c32 100%);box-shadow:inset 0 2px 1px rgba(255,255,255,.48),inset 0 -4px 5px rgba(0,0,0,.48),0 0 0 2px rgba(5,9,12,.86),0 8px 24px rgba(0,0,0,.58);pointer-events:auto;cursor:ew-resize;touch-action:none;user-select:none}
.tak-nrt-compare-knob-i525:before{content:"";position:absolute;inset:5px 7px;border:1px solid rgba(20,28,34,.70);border-radius:9px;background:linear-gradient(180deg,#8f9aa0,#4f5a61);box-shadow:inset 0 1px 1px rgba(255,255,255,.30),inset 0 -2px 3px rgba(0,0,0,.40)}
.tak-nrt-compare-grip-i525{position:absolute;z-index:1;inset:10px 16px;display:flex;flex-direction:column;justify-content:center;gap:4px}
.tak-nrt-compare-grip-i525 i{display:block;height:3px;border-radius:3px;background:linear-gradient(180deg,#d9dfe2,#606b72);box-shadow:0 1px 0 rgba(0,0,0,.65),inset 0 1px 0 rgba(255,255,255,.45)}
.tak-nrt-compare-label-i525{position:absolute;top:24px;max-width:42%;padding:7px 9px;border:1px solid rgba(255,255,255,.38);border-radius:9px;background:rgba(8,17,25,.88);box-shadow:0 7px 20px rgba(0,0,0,.42);color:#f8f4dc;font-size:.7rem;font-weight:900;line-height:1.25;text-shadow:0 1px 2px #000;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;box-sizing:border-box}
.tak-nrt-compare-label-i525.left{left:55px;border-color:rgba(203,190,122,.72)}.tak-nrt-compare-label-i525.right{right:12px;border-color:rgba(126,193,232,.72);text-align:right}
@media(max-width:760px){.tak-relief-slider-row-v442{grid-template-columns:minmax(0,1fr) 48px}}
@media(max-width:520px){.tak-nrt-grid-i525,.tak-nrt-scenes-i525{grid-template-columns:1fr}.tak-nrt-compare-label-i525{max-width:38%;font-size:.62rem}.tak-nrt-compare-label-i525.left{left:48px}}
`;
    d.head.appendChild(style);
  }

  function panelHtml() {
    const options = Object.values(SOURCES).map((source) => `<option value="${esc(source.id)}">${esc(source.label)}</option>`).join('');
    return `<h2>NRT SATELLITE IMAGERY</h2>
<div class="muted">The previously selected basemap remains underneath while imagery loads and through any missing tiles.</div>
<label class="tak-nrt-source-i525">NRT Sat Imagery<select id="nrtSatSourceI525">${options}</select></label>
<div id="nrtSatLandsatControlsI525">
  <div class="tak-nrt-grid-i525">
    <label>Search lookback<select id="nrtSatLandsatDaysI525"><option value="90">90 days</option><option value="180">180 days</option><option value="365">1 year</option><option value="730">2 years</option><option value="1825">5 years</option></select></label>
    <label>Max scene cloud<select id="nrtSatLandsatCloudI525"><option value="10">10%</option><option value="20">20%</option><option value="35">35%</option><option value="50">50%</option><option value="75">75%</option><option value="100">100%</option></select></label>
    <label>Rendering<select id="nrtSatLandsatRenderingI525"><option value="Natural Color with DRA">Natural color</option><option value="Color Infrared with DRA">Color infrared</option><option value="Short-wave Infrared with DRA">Short-wave infrared</option><option value="NDVI Colorized">NDVI</option></select></label>
  </div>
  <div class="tak-nrt-actions-i525"><button id="nrtSatFindDatesI525" class="layer-button" type="button">Find Dates</button></div>
  <div class="tak-nrt-scenes-i525">
    <label>Older · left<select id="nrtSatLandsatLeftI525"><option value="">Find dates first</option></select></label>
    <label>Newer · right<select id="nrtSatLandsatRightI525"><option value="">Find dates first</option></select></label>
  </div>
</div>
<div id="nrtSatSentinelControlsI535" hidden>
  <div class="tak-nrt-grid-i525">
    <label>Search lookback<select id="nrtSatSentinelDaysI535"><option value="30">30 days</option><option value="90">90 days</option><option value="180">180 days</option><option value="365">1 year</option><option value="730">2 years</option></select></label>
    <label>Max scene cloud<select id="nrtSatSentinelCloudI535"><option value="5">5%</option><option value="10">10%</option><option value="20">20%</option><option value="35">35%</option><option value="50">50%</option><option value="75">75%</option><option value="100">100%</option></select></label>
    <label style="grid-column:1/-1">Layer / product<select id="nrtSatSentinelProductI535">${sentinelProductOptions('true_color')}</select></label>
  </div>
  <div id="nrtSatSentinelProductNoteI535" class="tak-nrt-product-note-i535"></div>
  <div class="tak-nrt-actions-i525"><button id="nrtSatSentinelFindDatesI535" class="layer-button" type="button">Find Dates</button></div>
  <div class="tak-nrt-scenes-i525">
    <label>Older · left<select id="nrtSatSentinelLeftI535"><option value="">Find dates first</option></select></label>
    <label>Newer · right<select id="nrtSatSentinelRightI535"><option value="">Find dates first</option></select></label>
  </div>
  <div class="muted tak-nrt-source-note-i525">Uses the signed-in user’s Sentinel Hub OAuth client. Configure it from the account menu.</div>
</div>
<div id="nrtSatGibsControlsI525" hidden>
  <div class="tak-nrt-grid-i525">
    <label>Older · left<input id="nrtSatGibsOlderI525" type="date"></label>
    <label>Newer · right<input id="nrtSatGibsNewerI525" type="date"></label>
  </div>
  <div class="muted tak-nrt-source-note-i525">NASA GIBS is a daily global mosaic. Cloud filtering and per-scene discovery are not available for this source.</div>
  <div class="tak-nrt-actions-i525"><button id="nrtSatLatestDatesI525" class="layer-button" type="button">Use Recent Dates</button></div>
</div>
<label class="tak-nrt-opacity-label-i525" for="nrtSatOpacityI525">Layer opacity</label>
<div class="tak-relief-slider-row-v442">
  <input id="nrtSatOpacityI525" class="tak-tactical-rail-v442" type="range" min="10" max="100" step="1" value="100">
  <span id="nrtSatOpacityValueI525" class="tak-relief-value-v442" aria-live="polite">100%</span>
</div>
<div class="tak-nrt-actions-i525"><button id="nrtSatSwapI525" class="layer-button" type="button">Swap Sides</button><button id="nrtSatStartI525" class="layer-button" type="button">Start Comparison</button><button id="nrtSatHideI525" class="layer-button" type="button">Hide Imagery</button></div>
<div id="nrtSatStatusI525" class="muted tak-nrt-status-i525">Select a source and two dates. The conventional basemap remains visible until imagery is loaded.</div>`;
  }

  function ensurePanel() {
    if (by('nrtSatellitePanelI525')) return true;
    const basePanel = by('basemapSelect')?.closest('.panel');
    if (!basePanel) return false;
    const panel = d.createElement('div');
    panel.className = 'panel';
    panel.id = 'nrtSatellitePanelI525';
    panel.hidden = true;
    panel.innerHTML = panelHtml();
    basePanel.insertAdjacentElement('afterend', panel);

    const saved = readSettings();
    by('nrtSatSourceI525').value = saved.source;
    by('nrtSatOpacityI525').value = String(saved.opacity);
    dividerPercent = saved.slider;
    by('nrtSatLandsatDaysI525').value = String(saved.landsat.days || 365);
    by('nrtSatLandsatCloudI525').value = String(saved.landsat.maxcc == null ? 50 : saved.landsat.maxcc);
    by('nrtSatLandsatRenderingI525').value = saved.landsat.rendering || 'Natural Color with DRA';
    by('nrtSatGibsOlderI525').value = saved.gibs.older || defaultDates().older;
    by('nrtSatGibsNewerI525').value = saved.gibs.newer || defaultDates().newer;
    by('nrtSatSentinelDaysI535').value = String(saved.sentinel.days || 180);
    by('nrtSatSentinelCloudI535').value = String(saved.sentinel.maxcc == null ? 35 : saved.sentinel.maxcc);
    by('nrtSatSentinelProductI535').innerHTML = sentinelProductOptions(saved.sentinel.product || 'true_color');
    by('nrtSatSentinelProductI535').value = SENTINEL_PRODUCTS[saved.sentinel.product] ? saved.sentinel.product : 'true_color';

    by('nrtSatSourceI525').addEventListener('change', onSourceChange);
    by('nrtSatFindDatesI525').addEventListener('click', findLandsatDates);
    by('nrtSatSentinelFindDatesI535').addEventListener('click', findSentinelDates);
    by('nrtSatLatestDatesI525').addEventListener('click', setRecentGibsDates);
    by('nrtSatSwapI525').addEventListener('click', swapSides);
    by('nrtSatStartI525').addEventListener('click', startComparison);
    by('nrtSatHideI525').addEventListener('click', () => {
      removeImagery();
      setStatus('Satellite imagery hidden. The fallback basemap remains active.', '');
    });
    by('nrtSatOpacityI525').addEventListener('input', applyOpacity);
    by('nrtSatOpacityI525').addEventListener('change', applyOpacity);
    [
      'nrtSatLandsatDaysI525', 'nrtSatLandsatCloudI525', 'nrtSatLandsatRenderingI525',
      'nrtSatLandsatLeftI525', 'nrtSatLandsatRightI525',
      'nrtSatGibsOlderI525', 'nrtSatGibsNewerI525',
      'nrtSatSentinelDaysI535', 'nrtSatSentinelCloudI535', 'nrtSatSentinelProductI535',
      'nrtSatSentinelLeftI535', 'nrtSatSentinelRightI535',
    ].forEach((id) => by(id)?.addEventListener('change', () => {
      saveSettings(currentSettings());
      updateSentinelProductNote();
      updateOverlayLabels();
    }));

    updateSourceControls();
    updateSentinelProductNote();
    applyOpacity();
    applySlider(saved.slider, false);
    return true;
  }

  function updateSourceControls() {
    const source = sourceDef();
    const landsat = by('nrtSatLandsatControlsI525');
    const gibs = by('nrtSatGibsControlsI525');
    const sentinel = by('nrtSatSentinelControlsI535');
    if (landsat) landsat.hidden = source.kind !== 'landsat';
    if (gibs) gibs.hidden = source.kind !== 'gibs';
    if (sentinel) sentinel.hidden = source.kind !== 'sentinel';
    updateSentinelProductNote();
    saveSettings(currentSettings());
  }

  async function onSourceChange() {
    removeImagery();
    updateSourceControls();
    const source = sourceDef();
    if (source.kind === 'landsat') {
      setStatus('Pan and zoom to the area of interest, then press Find Dates.', '');
    } else if (source.kind === 'sentinel') {
      const status = await sentinelStatus(true);
      if (!status.configured) setStatus('Sentinel Hub is not configured for this user. Open the account menu and select Configure Sentinel Hub.', 'bad');
      else if (!status.verified) setStatus('Sentinel Hub credentials are saved but not verified. Test the connection from the account menu.', 'warn');
      else setStatus('Choose a product, then find Sentinel-2 acquisition dates for the current map view.', '');
    } else {
      setStatus('Choose two daily ' + source.label + ' dates, then start the comparison.', '');
    }
  }

  function enterNrtMode() {
    ensurePanel();
    const fallback = chooseFallbackId();
    if (fallback) lastConventionalId = fallback;
    const mapRef = mapObject();
    try {
      if (mapRef && !activeBasemapId() && fallback && originalSetBasemap) originalSetBasemap(fallback, { skipSave: true });
    } catch (_) {}
    nrtMode = true;
    ensureNrtOption();
    const panel = by('nrtSatellitePanelI525');
    if (panel) panel.hidden = false;
    const select = by('basemapSelect');
    if (select) select.value = NRT_ID;
    setStatus('Using ' + conventionalLabel(lastConventionalId || fallback) + ' underneath. Choose a source and load two dates.', '');
  }

  function exitNrtMode() {
    if (!nrtMode && by('nrtSatellitePanelI525')?.hidden) return;
    nrtMode = false;
    removeImagery();
    const panel = by('nrtSatellitePanelI525');
    if (panel) panel.hidden = true;
  }

  function wrapBasemapFunctions() {
    if (wrapped) return true;
    if (typeof w.setBasemap !== 'function' || typeof w.renderBasemaps !== 'function') return false;
    originalSetBasemap = w.setBasemap;
    originalRenderBasemaps = w.renderBasemaps;

    const setWrapper = function (id, options) {
      const value = String(id || '');
      if (value === NRT_ID) {
        enterNrtMode();
        return;
      }
      if (value) lastConventionalId = value;
      exitNrtMode();
      return originalSetBasemap.apply(this, arguments);
    };

    const renderWrapper = function () {
      const result = originalRenderBasemaps.apply(this, arguments);
      ensureNrtOption();
      return result;
    };

    w.setBasemap = setWrapper;
    w.renderBasemaps = renderWrapper;
    try { setBasemap = setWrapper; } catch (_) {}
    try { renderBasemaps = renderWrapper; } catch (_) {}
    wrapped = true;
    ensureNrtOption();
    return true;
  }

  function ensurePanes() {
    const mapRef = mapObject();
    if (!mapRef) return;
    [['takNrtLeftPaneI525', '230'], ['takNrtRightPaneI525', '231']].forEach(([name, z]) => {
      let pane = mapRef.getPane(name);
      if (!pane) pane = mapRef.createPane(name);
      pane.style.zIndex = z;
      pane.style.pointerEvents = 'none';
    });
  }

  function clearClip() {
    const mapRef = mapObject();
    if (!mapRef) return;
    ['takNrtLeftPaneI525', 'takNrtRightPaneI525'].forEach((name) => {
      const pane = mapRef.getPane(name);
      if (pane) {
        pane.style.clip = '';
        pane.style.clipPath = '';
      }
    });
  }

  function removeOverlay() {
    try { if (labelResizeObserver) labelResizeObserver.disconnect(); } catch (_) {}
    try { if (labelMutationObserver) labelMutationObserver.disconnect(); } catch (_) {}
    labelResizeObserver = null;
    labelMutationObserver = null;
    if (labelPositionFrame) {
      try { w.cancelAnimationFrame(labelPositionFrame); } catch (_) {}
      labelPositionFrame = 0;
    }
    if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay);
    overlay = null;
    dragging = false;
  }

  function removeImagery() {
    const mapRef = mapObject();
    try { if (leftLayer && mapRef) mapRef.removeLayer(leftLayer); } catch (_) {}
    try { if (rightLayer && mapRef) mapRef.removeLayer(rightLayer); } catch (_) {}
    leftLayer = null;
    rightLayer = null;
    activeComparison = false;
    tileErrors = 0;
    clearClip();
    removeOverlay();
    const button = by('nrtSatStartI525');
    if (button) button.textContent = 'Start Comparison';
  }

  function projectedTileBounds(grid, coords) {
    const mapRef = mapObject();
    const bounds = grid._tileCoordsToBounds(coords);
    const crs = mapRef.options.crs;
    const northWest = crs.project(bounds.getNorthWest());
    const southEast = crs.project(bounds.getSouthEast());
    return [northWest.x, southEast.y, southEast.x, northWest.y];
  }

  function makeLandsatLayer(group, paneName, settings) {
    const renderingRule = { rasterFunction: settings.landsat.rendering };
    const mosaicRule = {
      mosaicMethod: 'esriMosaicLockRaster',
      lockRasterIds: group.ids.slice(0, 20),
      mosaicOperation: 'MT_FIRST',
    };
    const Grid = L.GridLayer.extend({
      createTile: function (coords, done) {
        const tile = d.createElement('img');
        tile.alt = '';
        tile.setAttribute('role', 'presentation');
        tile.decoding = 'async';
        let completed = false;
        const finish = (error) => {
          if (completed) return;
          completed = true;
          done(error || null, tile);
        };
        tile.onload = () => finish(null);
        tile.onerror = () => {
          tileErrors += 1;
          tile.onerror = null;
          tile.onload = () => finish(null);
          tile.src = TRANSPARENT_TILE;
        };
        const size = this.getTileSize();
        const bbox = projectedTileBounds(this, coords);
        tile.src = LANDSAT_EXPORT + '?' + encode({
          f: 'image',
          bbox: bbox.join(','),
          bboxSR: 3857,
          imageSR: 3857,
          size: size.x + ',' + size.y,
          format: 'jpgpng',
          compressionQuality: 85,
          interpolation: 'RSP_BilinearInterpolation',
          mosaicRule: JSON.stringify(mosaicRule),
          renderingRule: JSON.stringify(renderingRule),
          validateExtent: false,
        });
        return tile;
      },
      getAttribution: function () {
        return SOURCES.landsat_esri.attribution;
      },
    });
    return new Grid({
      pane: paneName,
      opacity: settings.opacity / 100,
      minZoom: 3,
      maxNativeZoom: SOURCES.landsat_esri.maxNativeZoom,
      maxZoom: 19,
      tileSize: 256,
      updateWhenIdle: true,
      updateWhenZooming: false,
      keepBuffer: 1,
      noWrap: false,
    });
  }

  function makeGibsLayer(date, paneName, settings, source) {
    const url = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/' + encodeURIComponent(source.layer) +
      '/default/' + encodeURIComponent(date) + '/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg';
    return L.tileLayer(url, {
      pane: paneName,
      opacity: settings.opacity / 100,
      minZoom: 1,
      maxNativeZoom: source.maxNativeZoom,
      maxZoom: 19,
      tileSize: 256,
      updateWhenIdle: true,
      updateWhenZooming: false,
      keepBuffer: 1,
      noWrap: false,
      errorTileUrl: TRANSPARENT_TILE,
      attribution: source.attribution,
    });
  }

  function makeSentinelLayer(date, paneName, settings) {
    const product = SENTINEL_PRODUCTS[settings.sentinel.product] ? settings.sentinel.product : 'true_color';
    const query = encode({date:date, product:product, maxcc:clamp(settings.sentinel.maxcc,0,100), v:'i536'});
    return L.tileLayer('/api/tak-map/sentinel-hub/tile/{z}/{x}/{y}.png?' + query, {
      pane: paneName,
      opacity: settings.opacity / 100,
      minZoom: 1,
      maxNativeZoom: SOURCES.sentinel2_cdse.maxNativeZoom,
      maxZoom: 19,
      tileSize: 256,
      updateWhenIdle: true,
      updateWhenZooming: false,
      keepBuffer: 1,
      noWrap: false,
      errorTileUrl: TRANSPARENT_TILE,
      attribution: SENTINEL_ATTRIBUTION,
    });
  }

  function updateSentinelProductNote() {
    const note = by('nrtSatSentinelProductNoteI535');
    if (!note) return;
    const product = sentinelProduct();
    note.textContent = product.label + ' · ' + product.description;
  }

  function sentinelGroup(key) {
    return sentinelSceneGroups.find((group) => group.key === key) || null;
  }

  function sentinelSceneLabel(group) {
    if (!group) return 'No date selected';
    const cloud = Number.isFinite(Number(group.cloud_cover)) ? Math.round(Number(group.cloud_cover)) + '% cloud · ' : '';
    return group.date + ' · ' + cloud + String(group.scene_count || 1) + ' scene' + (Number(group.scene_count || 1) === 1 ? '' : 's');
  }

  function sentinelSceneShort(group) {
    if (!group) return 'No date selected';
    const cloud = Number.isFinite(Number(group.cloud_cover)) ? ' · ' + Math.round(Number(group.cloud_cover)) + '% cloud' : '';
    return group.date + cloud + ' · ' + sentinelProduct().label;
  }

  function dateText(ms) {
    try {
      return new Intl.DateTimeFormat(undefined, { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' }).format(new Date(ms));
    } catch (_) {
      return isoDay(ms);
    }
  }

  function landsatSceneLabel(group) {
    const clouds = group.clouds.filter(Number.isFinite);
    const cloud = clouds.length ? Math.round(Math.min.apply(null, clouds)) : null;
    const sensor = Array.from(group.sensors).join('/') || 'Landsat';
    return dateText(group.ms) + (cloud !== null ? ' · ' + cloud + '% cloud' : '') + ' · ' + sensor + ' · ' + group.ids.length + ' scene' + (group.ids.length === 1 ? '' : 's');
  }

  function landsatSceneShort(group) {
    if (!group) return 'No date selected';
    const clouds = group.clouds.filter(Number.isFinite);
    const cloud = clouds.length ? Math.round(Math.min.apply(null, clouds)) : null;
    return dateText(group.ms) + (cloud !== null ? ' · ' + cloud + '% cloud' : '');
  }

  function landsatGroup(key) {
    return landsatSceneGroups.find((group) => group.key === key) || null;
  }

  function labelPair() {
    const settings = currentSettings();
    const source = SOURCES[settings.source] || SOURCES.landsat_esri;
    if (source.kind === 'sentinel') {
      const leftGroup = sentinelGroup(settings.sentinel.leftDate);
      const rightGroup = sentinelGroup(settings.sentinel.rightDate);
      const leftRole = leftGroup && rightGroup && leftGroup.ms > rightGroup.ms ? 'NEWER' : 'OLDER';
      const rightRole = leftRole === 'OLDER' ? 'NEWER' : 'OLDER';
      return {
        left: leftRole + ' · ' + sentinelSceneShort(leftGroup),
        right: rightRole + ' · ' + sentinelSceneShort(rightGroup),
      };
    }
    if (source.kind === 'landsat') {
      const leftGroup = landsatGroup(settings.landsat.leftDate);
      const rightGroup = landsatGroup(settings.landsat.rightDate);
      const leftRole = leftGroup && rightGroup && leftGroup.ms > rightGroup.ms ? 'NEWER' : 'OLDER';
      const rightRole = leftRole === 'OLDER' ? 'NEWER' : 'OLDER';
      return {
        left: leftRole + ' · ' + landsatSceneShort(leftGroup),
        right: rightRole + ' · ' + landsatSceneShort(rightGroup),
      };
    }
    const leftRole = settings.gibs.older > settings.gibs.newer ? 'NEWER' : 'OLDER';
    const rightRole = leftRole === 'OLDER' ? 'NEWER' : 'OLDER';
    return {
      left: leftRole + ' · ' + settings.gibs.older + ' · ' + source.label,
      right: rightRole + ' · ' + settings.gibs.newer + ' · ' + source.label,
    };
  }

  function visibleRect(element) {
    if (!element || !element.getBoundingClientRect) return null;
    try {
      const css = w.getComputedStyle ? w.getComputedStyle(element) : null;
      if (css && (css.display === 'none' || css.visibility === 'hidden' || Number(css.opacity) === 0)) return null;
      const rect = element.getBoundingClientRect();
      if (!rect || rect.width < 2 || rect.height < 2) return null;
      return rect;
    } catch (_) {
      return null;
    }
  }

  function rightToolbarInset(mapRect) {
    const seen = new Set();
    const candidates = [
      by('floatingToolbarDock'),
      by('floatingMapToolbar'),
      ...Array.from(d.querySelectorAll('.floating-toolbar-dock,.floating-map-toolbar,.map-mini-toolbar.active,.leaflet-control-container .leaflet-right')),
    ].filter((item) => item && !seen.has(item) && seen.add(item));
    let toolbarLeft = null;
    candidates.forEach((element) => {
      const rect = visibleRect(element);
      if (!rect) return;
      if (rect.right <= mapRect.left || rect.left >= mapRect.right) return;
      if (rect.left < mapRect.left + mapRect.width * 0.5) return;
      toolbarLeft = toolbarLeft == null ? rect.left : Math.min(toolbarLeft, rect.left);
    });
    return toolbarLeft == null ? 12 : Math.max(12, Math.ceil(mapRect.right - toolbarLeft + 12));
  }

  function positionOverlayLabels() {
    if (!overlay) return;
    const mapRef = mapObject();
    const mapNode = mapRef && mapRef.getContainer ? mapRef.getContainer() : null;
    if (!mapNode) return;
    const mapRect = mapNode.getBoundingClientRect();
    if (!mapRect || mapRect.width < 1) return;
    const left = overlay.querySelector('.tak-nrt-compare-label-i525.left');
    const right = overlay.querySelector('.tak-nrt-compare-label-i525.right');
    const leftInset = mapRect.width <= 520 ? 48 : 55;
    const rightInset = rightToolbarInset(mapRect);
    const dividerX = mapRect.width * clamp(dividerPercent, 2, 98) / 100;
    if (left) {
      left.style.top = '24px';
      left.style.left = leftInset + 'px';
      left.style.maxWidth = Math.max(56, Math.min(mapRect.width * 0.42, dividerX - leftInset - 14)) + 'px';
    }
    if (right) {
      right.style.top = '24px';
      right.style.left = 'auto';
      right.style.right = rightInset + 'px';
      right.style.maxWidth = Math.max(56, Math.min(mapRect.width * 0.42, mapRect.width - rightInset - dividerX - 14)) + 'px';
    }
  }

  function scheduleOverlayLabelPosition() {
    if (labelPositionFrame) return;
    labelPositionFrame = w.requestAnimationFrame(() => {
      labelPositionFrame = 0;
      positionOverlayLabels();
    });
  }

  function bindOverlayPositionObservers() {
    const mapRef = mapObject();
    const mapNode = mapRef && mapRef.getContainer ? mapRef.getContainer() : null;
    const toolbar = by('floatingToolbarDock') || d.querySelector('.floating-toolbar-dock');
    try {
      if (w.ResizeObserver) {
        labelResizeObserver = new ResizeObserver(scheduleOverlayLabelPosition);
        if (mapNode) labelResizeObserver.observe(mapNode);
        if (toolbar) labelResizeObserver.observe(toolbar);
        const side = by('sidebar') || d.querySelector('.sidebar');
        if (side) labelResizeObserver.observe(side);
      }
    } catch (_) {}
    try {
      if (w.MutationObserver && toolbar) {
        labelMutationObserver = new MutationObserver(scheduleOverlayLabelPosition);
        labelMutationObserver.observe(toolbar, { attributes: true, childList: true, subtree: true, attributeFilter: ['class', 'style', 'hidden'] });
      }
    } catch (_) {}
  }

  function updateOverlayLabels() {
    if (!overlay) return;
    const pair = labelPair();
    const left = overlay.querySelector('.tak-nrt-compare-label-i525.left');
    const right = overlay.querySelector('.tak-nrt-compare-label-i525.right');
    if (left) { left.textContent = pair.left; left.title = pair.left; }
    if (right) { right.textContent = pair.right; right.title = pair.right; }
    scheduleOverlayLabelPosition();
  }

  function pointerPercent(event) {
    const mapRef = mapObject();
    if (!overlay || !mapRef) return 50;
    const rect = mapRef.getContainer().getBoundingClientRect();
    return clamp((event.clientX - rect.left) / Math.max(1, rect.width) * 100, 2, 98);
  }

  function applySlider(value, persist) {
    const percentage = clamp(value == null ? dividerPercent : value, 2, 98);
    dividerPercent = percentage;
    if (overlay) {
      const line = overlay.querySelector('.tak-nrt-compare-line-i525');
      if (line) line.style.left = percentage + '%';
    }
    const mapRef = mapObject();
    if (activeComparison && mapRef) {
      const x = mapRef.containerPointToLayerPoint([mapRef.getSize().x * percentage / 100, 0]).x;
      const leftPane = mapRef.getPane('takNrtLeftPaneI525');
      const rightPane = mapRef.getPane('takNrtRightPaneI525');
      if (leftPane) leftPane.style.clip = 'rect(-999999px,' + x + 'px,999999px,-999999px)';
      if (rightPane) rightPane.style.clip = 'rect(-999999px,999999px,999999px,' + x + 'px)';
    }
    scheduleOverlayLabelPosition();
    if (persist) {
      const settings = currentSettings();
      settings.slider = percentage;
      saveSettings(settings);
    }
  }

  function finishDrag(event) {
    if (!dragging) return;
    dragging = false;
    try {
      if (event && event.pointerId !== undefined) overlay.querySelector('.tak-nrt-compare-knob-i525').releasePointerCapture(event.pointerId);
    } catch (_) {}
    const mapRef = mapObject();
    try {
      if (dragWasEnabled && mapRef.dragging && !mapRef.dragging.enabled()) mapRef.dragging.enable();
    } catch (_) {}
    applySlider(dividerPercent, true);
  }

  function ensureOverlay() {
    removeOverlay();
    const mapRef = mapObject();
    if (!mapRef) return;
    overlay = d.createElement('div');
    overlay.className = 'tak-nrt-compare-overlay-i525';
    overlay.innerHTML = '<div class="tak-nrt-compare-label-i525 left"></div><div class="tak-nrt-compare-label-i525 right"></div><div class="tak-nrt-compare-line-i525"><div class="tak-nrt-compare-knob-i525" title="Drag to compare dates" aria-label="Drag satellite imagery comparison divider"><span class="tak-nrt-compare-grip-i525" aria-hidden="true"><i></i><i></i><i></i><i></i></span></div></div>';
    mapRef.getContainer().appendChild(overlay);
    try {
      L.DomEvent.disableClickPropagation(overlay);
      L.DomEvent.disableScrollPropagation(overlay);
    } catch (_) {}
    const knob = overlay.querySelector('.tak-nrt-compare-knob-i525');
    knob.addEventListener('pointerdown', (event) => {
      event.preventDefault();
      event.stopPropagation();
      dragging = true;
      try { knob.setPointerCapture(event.pointerId); } catch (_) {}
      try {
        dragWasEnabled = !!(mapRef.dragging && mapRef.dragging.enabled());
        if (dragWasEnabled) mapRef.dragging.disable();
      } catch (_) { dragWasEnabled = false; }
    });
    knob.addEventListener('pointermove', (event) => {
      if (!dragging) return;
      event.preventDefault();
      applySlider(pointerPercent(event), false);
    });
    knob.addEventListener('pointerup', finishDrag);
    knob.addEventListener('pointercancel', finishDrag);
    bindOverlayPositionObservers();
    updateOverlayLabels();
    applySlider(dividerPercent, false);
  }

  function bindMapEvents() {
    const mapRef = mapObject();
    if (mapEventsBound || !mapRef) return;
    mapEventsBound = true;
    mapRef.on('zoom move resize', () => {
      if (activeComparison) applySlider(dividerPercent, false);
    });
    w.addEventListener('resize', scheduleOverlayLabelPosition, { passive: true });
    mapRef.on('moveend', () => {
      if (!activeComparison) return;
      if (sourceDef().kind === 'landsat') {
        setStatus('Comparison remains locked to the selected Landsat dates. Press Find Dates after panning to search the new view.', 'warn');
      }
    });
  }

  function applyOpacity() {
    const settings = currentSettings();
    const output = by('nrtSatOpacityValueI525');
    if (output) output.textContent = Math.round(settings.opacity) + '%';
    const input = by('nrtSatOpacityI525');
    if (input) input.style.setProperty('--tak-relief-pct', Math.round(settings.opacity) + '%');
    saveSettings(settings);
    try {
      if (leftLayer) leftLayer.setOpacity(settings.opacity / 100);
      if (rightLayer) rightLayer.setOpacity(settings.opacity / 100);
    } catch (_) {}
  }

  function attachLayerStatus(layer, side) {
    if (!layer) return;
    layer.on('tileerror', () => { tileErrors += 1; });
    layer.on('loading', () => setStatus('Loading both satellite dates over the fallback basemap…', 'warn'));
    if (side === 'right') {
      layer.on('load', () => {
        if (tileErrors) {
          setStatus('Comparison loaded with ' + tileErrors + ' missing tile' + (tileErrors === 1 ? '' : 's') + '. The fallback basemap remains visible in those areas.', 'warn');
        } else {
          setStatus('Date comparison loaded. Drag the divider across the map.', 'ok');
        }
      });
    }
  }

  function startComparison() {
    const mapRef = mapObject();
    if (!mapRef || typeof L === 'undefined') {
      setStatus('TAK Map is not ready yet. Try again in a moment.', 'warn');
      return;
    }
    const settings = currentSettings();
    const source = SOURCES[settings.source] || SOURCES.landsat_esri;
    let left;
    let right;
    if (source.kind === 'sentinel') {
      const older = sentinelGroup(settings.sentinel.leftDate);
      const newer = sentinelGroup(settings.sentinel.rightDate);
      if (!older || !newer) {
        setStatus('Press Find Dates, then choose an older and a newer Sentinel-2 acquisition.', 'bad');
        return;
      }
      if (older.key === newer.key) {
        setStatus('Choose two different Sentinel-2 acquisition dates.', 'bad');
        return;
      }
      left = makeSentinelLayer(older.date, 'takNrtLeftPaneI525', settings);
      right = makeSentinelLayer(newer.date, 'takNrtRightPaneI525', settings);
    } else if (source.kind === 'landsat') {
      const older = landsatGroup(settings.landsat.leftDate);
      const newer = landsatGroup(settings.landsat.rightDate);
      if (!older || !newer) {
        setStatus('Press Find Dates, then choose an older and a newer Landsat acquisition.', 'bad');
        return;
      }
      if (older.key === newer.key) {
        setStatus('Choose two different Landsat acquisition dates.', 'bad');
        return;
      }
      left = makeLandsatLayer(older, 'takNrtLeftPaneI525', settings);
      right = makeLandsatLayer(newer, 'takNrtRightPaneI525', settings);
    } else {
      const older = settings.gibs.older;
      const newer = settings.gibs.newer;
      if (!/^\d{4}-\d{2}-\d{2}$/.test(older) || !/^\d{4}-\d{2}-\d{2}$/.test(newer)) {
        setStatus('Choose valid older and newer dates.', 'bad');
        return;
      }
      if (older === newer) {
        setStatus('Choose two different daily imagery dates.', 'bad');
        return;
      }
      left = makeGibsLayer(older, 'takNrtLeftPaneI525', settings, source);
      right = makeGibsLayer(newer, 'takNrtRightPaneI525', settings, source);
    }

    saveSettings(settings);
    removeImagery();
    try {
      ensurePanes();
      bindMapEvents();
      tileErrors = 0;
      leftLayer = left;
      rightLayer = right;
      attachLayerStatus(leftLayer, 'left');
      attachLayerStatus(rightLayer, 'right');
      leftLayer.addTo(mapRef);
      rightLayer.addTo(mapRef);
      activeComparison = true;
      ensureOverlay();
      applySlider(settings.slider, false);
      const button = by('nrtSatStartI525');
      if (button) button.textContent = 'Reload Comparison';
    } catch (error) {
      removeImagery();
      setStatus('Could not create the date comparison: ' + String(error && error.message || error), 'bad');
    }
  }

  function swapSides() {
    const source = sourceDef();
    if (source.kind === 'sentinel') {
      const left = by('nrtSatSentinelLeftI535');
      const right = by('nrtSatSentinelRightI535');
      if (!left || !right) return;
      const value = left.value;
      left.value = right.value;
      right.value = value;
    } else if (source.kind === 'landsat') {
      const left = by('nrtSatLandsatLeftI525');
      const right = by('nrtSatLandsatRightI525');
      if (!left || !right) return;
      const value = left.value;
      left.value = right.value;
      right.value = value;
    } else {
      const left = by('nrtSatGibsOlderI525');
      const right = by('nrtSatGibsNewerI525');
      if (!left || !right) return;
      const value = left.value;
      left.value = right.value;
      right.value = value;
    }
    saveSettings(currentSettings());
    updateOverlayLabels();
    if (activeComparison) startComparison();
  }

  function setRecentGibsDates() {
    const dates = defaultDates();
    by('nrtSatGibsOlderI525').value = dates.older;
    by('nrtSatGibsNewerI525').value = dates.newer;
    saveSettings(currentSettings());
    updateOverlayLabels();
    setStatus('Recent daily dates selected. Start the comparison to load them.', '');
  }

  function populateSentinel(groups) {
    sentinelSceneGroups = groups.map((row) => Object.assign({}, row, {key:String(row.date || ''), ms:Date.parse(String(row.date || '') + 'T00:00:00Z')}));
    const left = by('nrtSatSentinelLeftI535');
    const right = by('nrtSatSentinelRightI535');
    const saved = readSettings();
    left.innerHTML = '';
    right.innerHTML = '';
    sentinelSceneGroups.forEach((group) => {
      [left, right].forEach((select) => {
        const option = d.createElement('option');
        option.value = group.key;
        option.textContent = sentinelSceneLabel(group);
        select.appendChild(option);
      });
    });
    if (!sentinelSceneGroups.length) return;
    let newer = sentinelSceneGroups[0];
    let older = sentinelSceneGroups[sentinelSceneGroups.length - 1];
    for (const group of sentinelSceneGroups) {
      if (newer.ms - group.ms >= 30 * 86400000) { older = group; break; }
    }
    if (saved.sentinel.leftDate && sentinelGroup(saved.sentinel.leftDate)) older = sentinelGroup(saved.sentinel.leftDate);
    if (saved.sentinel.rightDate && sentinelGroup(saved.sentinel.rightDate)) newer = sentinelGroup(saved.sentinel.rightDate);
    left.value = older.key;
    right.value = newer.key;
    saveSettings(currentSettings());
    updateOverlayLabels();
  }

  async function findSentinelDates() {
    const mapRef = mapObject();
    if (!mapRef) { setStatus('TAK Map is not ready yet.', 'warn'); return; }
    const status = await sentinelStatus(true);
    if (!status.configured) {
      setStatus('Configure Sentinel Hub from your account menu before searching imagery.', 'bad');
      return;
    }
    if (!status.verified) {
      setStatus('Test and verify the saved Sentinel Hub connection from your account menu first.', 'bad');
      return;
    }
    const settings = currentSettings();
    const b = mapRef.getBounds();
    const body = {
      bbox: [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()],
      days: Math.max(1, settings.sentinel.days || 180),
      max_cloud: clamp(settings.sentinel.maxcc, 0, 100),
    };
    setStatus('Searching Sentinel-2 L2A acquisitions intersecting the current map view…', 'warn');
    try {
      const response = await fetch('/api/tak-map/sentinel-hub/search', {
        method:'POST', credentials:'same-origin', cache:'no-store',
        headers:{'Content-Type':'application/json'}, body:JSON.stringify(body),
      });
      const payload = await response.json().catch(() => ({ok:false,error:'HTTP '+response.status}));
      if (!response.ok || !payload.ok) throw new Error(payload.error || ('HTTP ' + response.status));
      populateSentinel(payload.scenes || []);
      const count = (payload.scenes || []).length;
      if (count < 2) {
        setStatus('Only ' + count + ' Sentinel-2 acquisition date matched. Increase lookback or cloud cover, or zoom/pan to another area.', 'bad');
        return;
      }
      setStatus('Found ' + count + ' Sentinel-2 acquisition dates. Choose two dates and start the comparison.', 'ok');
    } catch (error) {
      setStatus('Sentinel-2 date search failed: ' + String(error && error.message || error), 'bad');
    }
  }

  function populateLandsat(groups) {
    landsatSceneGroups = groups;
    const left = by('nrtSatLandsatLeftI525');
    const right = by('nrtSatLandsatRightI525');
    const saved = readSettings();
    left.innerHTML = '';
    right.innerHTML = '';
    groups.forEach((group) => {
      [left, right].forEach((select) => {
        const option = d.createElement('option');
        option.value = group.key;
        option.textContent = landsatSceneLabel(group);
        select.appendChild(option);
      });
    });
    if (!groups.length) return;
    let newer = groups[0];
    let older = groups[groups.length - 1];
    for (const group of groups) {
      if (newer.ms - group.ms >= 60 * 86400000) {
        older = group;
        break;
      }
    }
    if (saved.landsat.leftDate && landsatGroup(saved.landsat.leftDate)) older = landsatGroup(saved.landsat.leftDate);
    if (saved.landsat.rightDate && landsatGroup(saved.landsat.rightDate)) newer = landsatGroup(saved.landsat.rightDate);
    left.value = older.key;
    right.value = newer.key;
    saveSettings(currentSettings());
  }

  async function findLandsatDates() {
    const mapRef = mapObject();
    if (!mapRef) {
      setStatus('TAK Map is not ready yet.', 'warn');
      return;
    }
    const settings = currentSettings();
    const end = new Date();
    const start = new Date(end.getTime() - Math.max(1, settings.landsat.days || 365) * 86400000);
    const bounds = mapRef.getBounds();
    const crs = mapRef.options.crs;
    const southWest = crs.project(bounds.getSouthWest());
    const northEast = crs.project(bounds.getNorthEast());
    const where = "CloudCover <= " + clamp(settings.landsat.maxcc, 0, 100) +
      " AND AcquisitionDate >= DATE '" + isoDay(start) + " 00:00:00'" +
      " AND AcquisitionDate <= DATE '" + isoDay(end) + " 23:59:59'";
    const url = LANDSAT_QUERY + '?' + encode({
      f: 'json',
      where: where,
      geometry: [southWest.x, southWest.y, northEast.x, northEast.y].join(','),
      geometryType: 'esriGeometryEnvelope',
      inSR: 3857,
      spatialRel: 'esriSpatialRelIntersects',
      outFields: 'OBJECTID,SensorName,AcquisitionDate,CloudCover,dataset_id,WRS_Path,WRS_Row',
      orderByFields: 'AcquisitionDate DESC,CloudCover ASC',
      returnGeometry: false,
      resultRecordCount: 250,
    });
    setStatus('Searching Landsat acquisitions intersecting the current map view…', 'warn');
    try {
      const response = await fetch(url, { mode: 'cors', credentials: 'omit', cache: 'no-store' });
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const payload = await response.json();
      if (payload.error) throw new Error(payload.error.message || 'query failed');
      const grouped = new Map();
      for (const feature of payload.features || []) {
        const attributes = feature && feature.attributes || {};
        const ms = Number(attributes.AcquisitionDate);
        const id = Number(attributes.OBJECTID);
        if (!Number.isFinite(ms) || !Number.isFinite(id)) continue;
        const key = isoDay(ms);
        if (!grouped.has(key)) grouped.set(key, { key: key, ms: ms, ids: [], clouds: [], sensors: new Set() });
        const group = grouped.get(key);
        if (group.ids.length < 20 && !group.ids.includes(id)) group.ids.push(id);
        const cloud = Number(attributes.CloudCover);
        if (Number.isFinite(cloud)) group.clouds.push(cloud);
        if (attributes.SensorName) group.sensors.add(String(attributes.SensorName).replace(/_/g, ' '));
      }
      const groups = Array.from(grouped.values()).filter((group) => group.ids.length).sort((a, b) => b.ms - a.ms);
      populateLandsat(groups);
      if (groups.length < 2) {
        setStatus('Only ' + groups.length + ' acquisition date matched. Increase lookback or cloud cover, or zoom/pan to another area.', 'bad');
        return;
      }
      setStatus('Found ' + groups.length + ' Landsat acquisition dates. Choose the older and newer dates, then start the comparison.', 'ok');
    } catch (error) {
      setStatus('Landsat date search failed: ' + String(error && error.message || error), 'bad');
    }
  }

  function install() {
    installStyle();
    if (!ensurePanel()) return false;
    if (!wrapBasemapFunctions()) return false;
    bindMapEvents();
    ensureNrtOption();
    return true;
  }

  function waitForMap(attempt) {
    if (install()) return;
    if (attempt < 100) setTimeout(() => waitForMap(attempt + 1), 125);
  }

  w.TakMapNrtSatelliteI535 = Object.freeze({
    version: VERSION,
    sources: Object.freeze(Object.keys(SOURCES)),
    enter: enterNrtMode,
    exit: exitNrtMode,
    findDates: findLandsatDates,
    findSentinelDates: findSentinelDates,
    compare: startComparison,
    hide: removeImagery,
    settings: readSettings,
    diagnostics: function () {
      return {
        version: VERSION,
        nrtOptionPresent: !!Array.from(by('basemapSelect')?.options || []).find((item) => item.value === NRT_ID),
        panelPresent: !!by('nrtSatellitePanelI525'),
        panelVisible: !!by('nrtSatellitePanelI525') && !by('nrtSatellitePanelI525').hidden,
        nrtMode: nrtMode,
        fallbackBasemap: lastConventionalId,
        source: currentSettings().source,
        activeComparison: activeComparison,
        dividerPercent: dividerPercent,
        dividerDesign: 'beveled-rail-rounded-clamp',
        sidebarDividerSlider: false,
        toolbarAwareNewerLabel: true,
        imageryPaneZ: [230, 231],
        sourceCount: Object.keys(SOURCES).length,
        supportsLandsatDateSearch: true,
        supportsGibsDailyDates: true,
        supportsSentinel2L2A: true,
        sentinelConfigured: !!(sentinelStatusCache && sentinelStatusCache.configured),
        sentinelProduct: currentSettings().sentinel.product,
        sentinelProductCount: Object.keys(SENTINEL_PRODUCTS).length,
      };
    },
  });

  if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', () => waitForMap(0), { once: true });
  else waitForMap(0);
  [700, 1800, 4200].forEach((delay) => setTimeout(() => install(), delay));
})(window, document);
