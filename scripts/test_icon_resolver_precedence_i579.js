'use strict';

const fs = require('fs');
const vm = require('vm');

const manifestPath = 'assets/tak-map-deferred-i553.json';
const resolverPath = 'assets/tak-map-milstd2525c-i553.js';
const catalogPath = 'assets/mil2525/icons.json';
const aliasPath = 'assets/mil2525/atak-compatibility-aliases-i553.json';

const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const rows = manifest.scripts.filter(row => row.id === 'takMapMilStd2525CLoaderI553');
if (rows.length !== 1) throw new Error(`expected one deferred i553 resolver, got ${rows.length}`);
const deferredSource = String(rows[0].code || '');
const standaloneSource = fs.readFileSync(resolverPath, 'utf8');
if (deferredSource !== standaloneSource) throw new Error('standalone/deferred resolver copies differ');

const catalog = JSON.parse(fs.readFileSync(catalogPath, 'utf8'));
const aliases = JSON.parse(fs.readFileSync(aliasPath, 'utf8'));
const svgNames = new Set(
  fs.readdirSync('assets/mil2525/svg')
    .filter(name => name.endsWith('.svg'))
    .map(name => name.replace(/\.svg$/i, ''))
);

const document = {
  readyState: 'loading',
  addEventListener() {},
  querySelectorAll() { return []; },
  documentElement: {},
  head: { appendChild() {} }
};
const window = {
  document,
  setTimeout() { return 0; },
  clearTimeout() {},
  fetch: async () => { throw new Error('network disabled in test'); }
};
const context = {
  window,
  document,
  console,
  Set,
  Map,
  Object,
  Array,
  String,
  RegExp,
  Promise,
  setTimeout() { return 0; },
  clearTimeout() {},
  encodeURIComponent,
  MutationObserver: class { observe() {} }
};
vm.createContext(context);
vm.runInContext(deferredSource, context, { filename: resolverPath });

const resolver = window.TakMapMilStd2525CI553;
if (!resolver) throw new Error('resolver was not exported');
resolver._resetCatalogForTest(catalog);

const canonicalBySidc = new Map();
const catalogRowsBySidc = new Map();
for (const icon of catalog) {
  if (!canonicalBySidc.has(icon.sidc)) canonicalBySidc.set(icon.sidc, icon);
  const rowsForSidc = catalogRowsBySidc.get(icon.sidc) || [];
  rowsForSidc.push(icon);
  catalogRowsBySidc.set(icon.sidc, rowsForSidc);
}

function aliasName(record) {
  return Array.isArray(record) ? record[0] : (record && record.name) || '';
}

const sidcCollisions = [];
for (const [sidc, record] of Object.entries(aliases.by_sidc || {})) {
  const canonical = canonicalBySidc.get(sidc);
  const selectedName = aliasName(record);
  if (!canonical || !selectedName || (catalogRowsBySidc.get(sidc) || []).length !== 1) continue;
  if (canonical.name !== selectedName) {
    sidcCollisions.push({ sidc, canonical, alias: record });
  }
}
if (sidcCollisions.length !== 92) {
  throw new Error(`expected 92 exact SIDC collisions, got ${sidcCollisions.length}`);
}

const cotCollisions = [];
for (const [cotType, record] of Object.entries(aliases.by_cot_type || {})) {
  const selectedName = aliasName(record);
  if (!selectedName) continue;
  const sidc = resolver.cotTypeToSidc(cotType);
  const canonical = canonicalBySidc.get(sidc);
  if (canonical && (catalogRowsBySidc.get(sidc) || []).length === 1 && canonical.name !== selectedName) {
    cotCollisions.push({ cotType, sidc, canonical, alias: record });
  }
}
if (cotCollisions.length !== 92) {
  throw new Error(`expected 92 exact CoT collisions, got ${cotCollisions.length}`);
}

for (const row of sidcCollisions) {
  const expectedFile = `${row.canonical.name}.svg`;
  if (!svgNames.has(row.canonical.name)) throw new Error(`missing canonical SVG ${row.canonical.name}`);

  const direct = resolver.resolveSymbol({ sidc: row.sidc });
  if (!direct.ok || direct.file !== expectedFile || direct.name !== row.canonical.name || direct.sidc !== row.sidc || !direct.exact || !direct.canonicalPrecedenceI579 || direct.reviewedAlias) {
    throw new Error(`SIDC canonical precedence failed: ${JSON.stringify({ row, direct })}`);
  }

  const decided = resolver.resolveSymbol({
    mission_cot_raw_sidc_i553: row.sidc,
    data_sync_symbol_decision_i553: {
      version: 'i553',
      authority: 'explicit-sidc',
      selected_sidc: row.sidc
    }
  });
  if (!decided.ok || decided.file !== expectedFile || !decided.canonicalPrecedenceI579 || !String(decided.source || '').startsWith('current-decision-sidc-i553')) {
    throw new Error(`Data Sync explicit-SIDC precedence failed: ${JSON.stringify({ row, decided })}`);
  }
}

for (const row of cotCollisions) {
  const expectedFile = `${row.canonical.name}.svg`;
  const direct = resolver.resolveByCotType(row.cotType, 'i579-cot-test');
  if (!direct || !direct.ok || direct.file !== expectedFile || direct.name !== row.canonical.name || direct.sidc !== row.sidc || !direct.exact || !direct.canonicalPrecedenceI579 || direct.reviewedAlias) {
    throw new Error(`CoT canonical precedence failed: ${JSON.stringify({ row, direct })}`);
  }

  const decided = resolver.resolveSymbol({
    type: row.cotType,
    cot_type: row.cotType,
    mission_cot_raw_type_i553: row.cotType,
    data_sync_symbol_decision_i553: {
      version: 'i553',
      authority: 'event-type',
      selected_cot_type: row.cotType
    }
  });
  if (!decided.ok || decided.file !== expectedFile || !decided.canonicalPrecedenceI579 || !String(decided.source || '').startsWith('current-decision-event-type-i553')) {
    throw new Error(`Data Sync event-type precedence failed: ${JSON.stringify({ row, decided })}`);
  }
}

// The reported generic Sensor case must use the exact star-like Sensor icon.
const sensor = resolver.resolveSymbol({
  mission_cot_raw_sidc_i553: 'SFGPES---------',
  mission_cot_raw_type_i553: 'a-f-G-E-S',
  data_sync_symbol_decision_i553: {
    version: 'i553', authority: 'explicit-sidc', selected_sidc: 'SFGPES---------'
  }
});
if (!sensor.ok || sensor.file !== 'friendly-ground-equipment-sensor.svg' || sensor.name !== 'friendly-ground-equipment-sensor' || sensor.reviewedAlias || !sensor.canonicalPrecedenceI579) {
  throw new Error(`generic Sensor correction failed: ${JSON.stringify(sensor)}`);
}

// A specific radar identity remains radar, but now uses its exact canonical icon
// rather than the broader radar-vehicle compatibility alias.
const radar = resolver.resolveSymbol({
  type: 'a-f-G-E-S-R',
  mission_cot_raw_type_i553: 'a-f-G-E-S-R',
  data_sync_symbol_decision_i553: {
    version: 'i553', authority: 'event-type', selected_cot_type: 'a-f-G-E-S-R'
  }
});
if (!radar.ok || radar.file !== 'friendly-ground-equipment-radar.svg' || radar.name !== 'friendly-ground-equipment-radar' || radar.reviewedAlias || !radar.canonicalPrecedenceI579) {
  throw new Error(`specific Radar preservation failed: ${JSON.stringify(radar)}`);
}

// Reviewed aliases are still required when the converted SIDC has no exact
// canonical catalog entry.
const construction = resolver.resolveByCotType('a-f-G-U-C-E-N', 'i579-alias-fallback');
if (!construction || !construction.ok || construction.file !== 'friendly-emergency-construction.svg' || !construction.reviewedAlias) {
  throw new Error(`Construction compatibility alias regressed: ${JSON.stringify(construction)}`);
}
const howitzer = resolver.resolveByCotType('a-f-G-E-W-H', 'i579-alias-fallback');
if (!howitzer || !howitzer.ok || howitzer.file !== 'friendly-ground-equipment-self-propelled-howitzer.svg' || !howitzer.reviewedAlias) {
  throw new Error(`Howitzer compatibility alias regressed: ${JSON.stringify(howitzer)}`);
}

// Older cached decisions must also upgrade to an exact current canonical type.
const oldSensor = resolver.resolveSymbol({
  mission_cot_raw_type_i550: 'a-f-G-E-S',
  mission_cot_raw_iconset_path_i550: 'COT_MAPPING_2525C/a-f-G-E-S-R',
  data_sync_symbol_decision_i550: {
    version: 'i550', authority: 'usericon-iconsetpath',
    selected_iconset_path: 'COT_MAPPING_2525C/a-f-G-E-S-R'
  }
});
if (!oldSensor.ok || oldSensor.file !== 'friendly-ground-equipment-sensor.svg' || !oldSensor.canonicalPrecedenceI579) {
  throw new Error(`cached Sensor canonical upgrade failed: ${JSON.stringify(oldSensor)}`);
}

// The four ambiguous rotary-wing duplicate SIDCs are deliberately outside
// this correction and continue to use the catalog's established first entry.
for (const sidc of ['SFAPMH---------', 'SHAPMH---------', 'SNAPMH---------', 'SUAPMH---------']) {
  const rowsForSidc = catalogRowsBySidc.get(sidc) || [];
  if (rowsForSidc.length !== 2) throw new Error(`expected two rotary-wing rows for ${sidc}`);
  const resolved = resolver.resolveSymbol({ sidc });
  if (!resolved.ok || resolved.file !== `${rowsForSidc[0].name}.svg`) {
    throw new Error(`duplicate SIDC behavior changed for ${sidc}: ${JSON.stringify(resolved)}`);
  }
}

const audit = resolver.audit();
if (!audit.exactCanonicalPrecedenceI579 || audit.catalogCount !== 1448 || audit.nameFailures || audit.sidcFailures) {
  throw new Error(`resolver audit failed: ${JSON.stringify(audit)}`);
}

console.log(JSON.stringify({
  ok: true,
  version: 'i579',
  exact_sidc_collisions_checked: sidcCollisions.length,
  exact_cot_collisions_checked: cotCollisions.length,
  generic_sensor_file: sensor.file,
  specific_radar_file: radar.file,
  compatibility_aliases_preserved: [construction.file, howitzer.file],
  standalone_deferred_parity: true
}, null, 2));
