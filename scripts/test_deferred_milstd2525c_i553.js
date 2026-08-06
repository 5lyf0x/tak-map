'use strict';

const fs = require('fs');
const vm = require('vm');

const manifest = JSON.parse(fs.readFileSync('assets/tak-map-deferred-i553.json', 'utf8'));
const rows = manifest.scripts.filter(row => row.id === 'takMapMilStd2525CLoaderI553');
if (rows.length !== 1) throw new Error(`expected one i553 resolver module, got ${rows.length}`);
const source = String(rows[0].code || '');
const catalog = JSON.parse(fs.readFileSync('assets/mil2525/icons.json', 'utf8'));
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
vm.runInContext(source, context, { filename: 'tak-map-milstd2525c-i553.js' });

const resolver = window.TakMapMilStd2525CI553;
if (!resolver) throw new Error('i553 resolver was not exported');
resolver._resetCatalogForTest(catalog);

if (catalog.length !== 1448) throw new Error(`expected 1448 catalog rows, got ${catalog.length}`);
if (svgNames.size !== 1448) throw new Error(`expected 1448 SVG files, got ${svgNames.size}`);

for (const icon of catalog) {
  if (!svgNames.has(icon.name)) throw new Error(`missing SVG for ${icon.name}`);
  const byName = resolver.resolveSymbol({ mil2525_name: icon.name });
  if (!byName.ok || byName.file !== `${icon.name}.svg` || byName.sidc !== icon.sidc) {
    throw new Error(`name resolution failed for ${icon.name}: ${JSON.stringify(byName)}`);
  }
  const bySidc = resolver.resolveSymbol({ sidc: icon.sidc });
  if (!bySidc.ok || !svgNames.has(bySidc.name) || bySidc.sidc !== icon.sidc) {
    throw new Error(`SIDC resolution failed for ${icon.sidc}: ${JSON.stringify(bySidc)}`);
  }
}

const cases = [
  [{ type: 'a-f-G-U-C-D' }, 'friendly-ground-unit-air-defense.svg', 'SFGPUCD--------'],
  [{ type: 'a-h-G-U-C-D' }, 'hostile-ground-unit-air-defense.svg', 'SHGPUCD--------'],
  [{ type: 'a-f-E-P' }, 'friendly-emergency-police.svg', 'SFEPP----------'],
  [{ type: 'a-f-G-I' }, 'friendly-ground-installation.svg', 'SFGPI----------'],
  [{ properties: { SIDC: 'SNGPUCD--------' } }, 'neutral-ground-unit-air-defense.svg', 'SNGPUCD--------'],
  [{ metadata: { cot_type: 'a-u-G-U-C-D' } }, 'unknown-ground-unit-air-defense.svg', 'SUGPUCD--------'],
  [{ xml: '<event uid="ANDROID-A" type="a-f-G-U-C-D"><detail/></event>' }, 'friendly-ground-unit-air-defense.svg', 'SFGPUCD--------'],
  [{ detail_xml: '<takmap_point sidc="SFGPUCD--------" mil2525Name="friendly-ground-unit-air-defense"/>' }, 'friendly-ground-unit-air-defense.svg', 'SFGPUCD--------'],
  [{ raw_xml: '<usericon iconsetpath="COT_MAPPING_2525C/a-f-G-U-C-D"/>' }, 'friendly-ground-unit-air-defense.svg', 'SFGPUCD--------'],
  [{ properties: { mil2525_name: 'FRIENDLY-GROUND-UNIT-AIR-DEFENSE.SVG' } }, 'friendly-ground-unit-air-defense.svg', 'SFGPUCD--------'],
  [{ detail: { usericon: { '@iconsetpath': 'COT_MAPPING_2525C/a-f-G-U-C-D' } } }, 'friendly-ground-unit-air-defense.svg', 'SFGPUCD--------'],
  [{ eventType: 'SFGPUCD--------' }, 'friendly-ground-unit-air-defense.svg', 'SFGPUCD--------']
];
for (const [input, file, sidc] of cases) {
  const actual = resolver.resolveSymbol(input);
  if (!actual.ok || actual.file !== file || actual.sidc !== sidc) {
    throw new Error(`case failed: ${JSON.stringify({ input, expected: { file, sidc }, actual })}`);
  }
}

// SIDC is authoritative over a conflicting stale icon filename.
const conflict = resolver.resolveSymbol({
  sidc: 'SFGPUCD--------',
  mil2525_name: 'hostile-ground-unit-armor'
});
if (conflict.file !== 'friendly-ground-unit-air-defense.svg') {
  throw new Error(`SIDC precedence failed: ${JSON.stringify(conflict)}`);
}

// i553: a current ATAK usericon-only update outranks stale derived SIDC/name.
const currentUsericon = resolver.resolveSymbol({
  sidc: 'SFGPEVA--------',
  mil2525_name: 'friendly-ground-equipment-armored-vehicle',
  type: 'a-f-G-U-C',
  mission_cot_raw_iconset_path_i553: 'COT_MAPPING_2525C/a-f-G-U-C-I'
});
if (!currentUsericon.ok || currentUsericon.file !== 'friendly-ground-unit-infantry.svg' || currentUsericon.sidc !== 'SFGPUCI--------') {
  throw new Error(`current usericon precedence failed: ${JSON.stringify(currentUsericon)}`);
}
// i579 package correction: DS-P13 carries an exact canonical Anti-Armor
// CoT type while ATAK leaves the old Air Defense usericon path attached. Exact
// canonical identity must win before the reviewed Tank Destroyer alias.
const dsP13 = resolver.resolveSymbol({
  type: 'a-f-G-U-C-A-A',
  cot_type: 'a-f-G-U-C-A-A',
  mission_cot_raw_type_i553: 'a-f-G-U-C-A-A',
  mission_cot_raw_iconset_path_i553: 'COT_MAPPING_2525C/a-f/a-f-G-U-C-D',
  data_sync_symbol_decision_i553: {
    version: 'i553',
    authority: 'event-type',
    reason: 'specific-type-changed-iconset-unchanged',
    conflict: true,
    selected_cot_type: 'a-f-G-U-C-A-A',
    selected_file: 'friendly-ground-unit-anti-armor.svg'
  }
});
if (!dsP13.ok || dsP13.file !== 'friendly-ground-unit-anti-armor.svg' || dsP13.sidc !== 'SFGPUCAA-------' || !dsP13.canonicalPrecedenceI579 || !dsP13.source.startsWith('current-decision-event-type-i553')) {
  throw new Error(`DS-P13 exact canonical precedence failed: ${JSON.stringify(dsP13)}`);
}

// The inverse case remains valid: a changed iconset with an unchanged generic
// type is explicitly selected by the backend and must win in the browser.
const iconOnlyDecision = resolver.resolveSymbol({
  type: 'a-f-G-U-C',
  mission_cot_raw_type_i553: 'a-f-G-U-C',
  mission_cot_raw_iconset_path_i553: 'COT_MAPPING_2525C/a-f-G-U-C-I',
  data_sync_symbol_decision_i553: {
    version: 'i553', authority: 'usericon-iconsetpath',
    selected_iconset_path: 'COT_MAPPING_2525C/a-f-G-U-C-I'
  }
});
if (!iconOnlyDecision.ok || iconOnlyDecision.file !== 'friendly-ground-unit-infantry.svg' || !iconOnlyDecision.source.startsWith('current-decision-iconset-i553')) {
  throw new Error(`i553 icon-only decision failed: ${JSON.stringify(iconOnlyDecision)}`);
}

// i553 systematic reviewed aliases: exact Construction candidate before parent fallback.
const construction = resolver.resolveSymbol({
  type: 'a-f-G-U-C-E-N',
  mission_cot_raw_type_i553: 'a-f-G-U-C-E-N',
  data_sync_symbol_decision_i553: {
    version: 'i553', authority: 'event-type', selected_cot_type: 'a-f-G-U-C-E-N'
  }
});
if (!construction.ok || construction.file !== 'friendly-emergency-construction.svg' || construction.sidc !== 'SFGPUCEN-------' || !construction.reviewedAlias) {
  throw new Error(`reviewed Construction alias failed: ${JSON.stringify(construction)}`);
}

// ATAK abbreviates Howitzer to a-f-G-E-W-H. The review's full candidate aliases
// share byte-identical Artillery/Howitzer artwork, so the safe prefix alias wins.
const howitzer = resolver.resolveSymbol({
  type: 'a-f-G-E-W-H',
  mission_cot_raw_type_i553: 'a-f-G-E-W-H',
  mission_cot_raw_iconset_path_i553: 'COT_MAPPING_2525C/a-f/a-f-G-E-V-U-S',
  data_sync_symbol_decision_i553: {
    version: 'i553', authority: 'event-type', selected_cot_type: 'a-f-G-E-W-H'
  }
});
if (!howitzer.ok || howitzer.file !== 'friendly-ground-equipment-self-propelled-howitzer.svg' || howitzer.sidc !== 'SFGPEWH--------' || !howitzer.reviewedAlias) {
  throw new Error(`reviewed Howitzer alias failed: ${JSON.stringify(howitzer)}`);
}

// Upgrade compatibility: cached i550 rows can arrive before the first i553
// response normalization. The browser must reinterpret an older decision when
// the current specific type now has an exact reviewed alias.
const oldConstruction = {
  type: 'a-f-G-U-C-E-N',
  mission_cot_raw_type_i550: 'a-f-G-U-C-E-N',
  mission_cot_raw_iconset_path_i550: 'COT_MAPPING_2525C/a-f/a-f-G-U-C-D',
  data_sync_symbol_decision_i550: {
    version: 'i550', authority: 'event-type', selected_cot_type: 'a-f-G-U-C-E-N'
  },
  mil2525_file: 'friendly-ground-unit-engineer.svg',
  name: 'DS-P13'
};
const oldConstructionResolved = resolver.resolveSymbol(oldConstruction);
if (!oldConstructionResolved.ok || oldConstructionResolved.file !== 'friendly-emergency-construction.svg') {
  throw new Error(`cached i550 Construction compatibility failed: ${JSON.stringify(oldConstructionResolved)}`);
}
const oldConstructionHtml = resolver.iconHtml(oldConstruction);
if (!/friendly-emergency-construction\.svg\?v=i553/.test(oldConstructionHtml)) {
  throw new Error(`cached i550 Construction DOM image failed: ${oldConstructionHtml}`);
}

const oldHowitzer = {
  type: 'a-f-G-E-W-H',
  mission_cot_raw_type_i550: 'a-f-G-E-W-H',
  mission_cot_raw_iconset_path_i550: 'COT_MAPPING_2525C/a-f/a-f-G-E-V-U-S',
  data_sync_symbol_decision_i550: {
    version: 'i550', authority: 'usericon-iconsetpath',
    selected_iconset_path: 'COT_MAPPING_2525C/a-f/a-f-G-E-V-U-S'
  },
  mil2525_file: 'friendly-ground-equipment-semi.svg',
  name: 'DS-P10'
};
const oldHowitzerResolved = resolver.resolveSymbol(oldHowitzer);
if (!oldHowitzerResolved.ok || oldHowitzerResolved.file !== 'friendly-ground-equipment-self-propelled-howitzer.svg') {
  throw new Error(`cached i550 Howitzer compatibility failed: ${JSON.stringify(oldHowitzerResolved)}`);
}
const oldHowitzerHtml = resolver.iconHtml(oldHowitzer);
if (!/friendly-ground-equipment-self-propelled-howitzer\.svg\?v=i553/.test(oldHowitzerHtml)) {
  throw new Error(`cached i550 Howitzer DOM image failed: ${oldHowitzerHtml}`);
}

const customDescriptor = resolver.userIconDescriptor('COT_MAPPING_SPOTMAP/red-x.png');
if (!customDescriptor || customDescriptor.base !== 'red x' || !customDescriptor.letters) {
  throw new Error(`custom usericon fallback descriptor failed: ${JSON.stringify(customDescriptor)}`);
}

// Preserve an unknown child SIDC while using a known parent only as its visual fallback.
const parentFallback = resolver.resolveSymbol({ sidc: 'SFGPUCDZ-------' });
if (!parentFallback.ok || parentFallback.file !== 'friendly-ground-unit-air-defense.svg' || parentFallback.sidc !== 'SFGPUCDZ-------') {
  throw new Error(`controlled parent fallback failed: ${JSON.stringify(parentFallback)}`);
}

// This function core has mine-plow, mine-roller, and mine-breaching modifier variants.
// The resolver must not pick one when the source omits that distinguishing modifier.
const ambiguous = resolver.resolveSymbol({ sidc: 'SFGPEVENGM-----' });
const forbiddenSiblings = new Set([
  'friendly-ground-equipment-mine-plow.svg',
  'friendly-ground-equipment-mine-roller.svg',
  'friendly-ground-equipment-mine-breaching-vehicle.svg'
]);
if (!ambiguous.ok || ambiguous.exact || forbiddenSiblings.has(ambiguous.file) || ambiguous.file !== 'friendly-ground-equipment-engineer-vehicle.svg') {
  throw new Error(`ambiguous sibling handling failed: ${JSON.stringify(ambiguous)}`);
}

// A generic parent must not be promoted to an arbitrary child.
const genericUnit = resolver.resolveSymbol({ type: 'a-f-G-U' });
if (genericUnit.ok || genericUnit.file) {
  throw new Error(`generic unit mapped to arbitrary child: ${JSON.stringify(genericUnit)}`);
}

const audit = resolver.audit();
if (audit.catalogCount !== 1448 || audit.nameFailures || audit.sidcFailures || !audit.emergencyDimensionSupported) {
  throw new Error(`resolver audit failed: ${JSON.stringify(audit)}`);
}

console.log('i553 browser MIL-STD-2525C exhaustive catalog/source resolution tests passed');

// Browser-side exact mission UID ownership must not depend on the TAK Map UID prefix.
const atakMissionUid = 'ANDROID-ATAK-AIR-DEFENSE-123';
const detailedMissionPoint = {
  uid: atakMissionUid,
  lat: 34.25,
  lon: -118.25,
  cot_type: 'a-f-G-U-C-D'
};
const genericLiveDuplicate = {
  uid: atakMissionUid,
  lat: 34.25,
  lon: -118.25,
  cot_type: 'a-f-G-U'
};
const unrelatedSamePosition = {
  uid: 'ANDROID-OTHER-UID',
  lat: 34.25,
  lon: -118.25,
  cot_type: 'a-f-G-U-C-D'
};

// Data Sync first, then Live TAK.
resolver.learnMissionPointUids({ objects: [detailedMissionPoint] });
let filtered = resolver.filterLivePayload({ markers: [genericLiveDuplicate, unrelatedSamePosition] });
if (filtered.markers.length !== 1 || filtered.markers[0].uid !== 'ANDROID-OTHER-UID') {
  throw new Error(`Data Sync-first exact UID filtering failed: ${JSON.stringify(filtered)}`);
}

// Live TAK first is corrected as soon as Data Sync ownership is learned and the
// subsequent refresh is filtered. Name/location equality must not suppress.
filtered = resolver.filterLivePayload({ euds: [genericLiveDuplicate, unrelatedSamePosition] });
if (filtered.euds.length !== 1 || filtered.euds[0].uid !== 'ANDROID-OTHER-UID') {
  throw new Error(`Live-first exact UID filtering failed: ${JSON.stringify(filtered)}`);
}
if (!resolver.missionPointUids().includes(atakMissionUid.toLowerCase())) {
  throw new Error('ATAK-style mission UID was not learned');
}


// A mission deletion tombstone must suppress an old retained Live TAK/EUD copy,
// while a genuinely newer CoT event with the same exact UID releases it.
const deletedUid = 'ANDROID-ATAK-DELETED-POINT-543';
const cutoffIso = '2026-07-25T04:00:00.000Z';
const cutoffEpoch = Date.parse(cutoffIso) / 1000;
resolver.learnMissionPointUids({
  objects: [],
  data_sync_deleted_uid_tombstones_i553: {
    tombstones: [{
      uid: deletedUid,
      cutoff_epoch: cutoffEpoch,
      observed_at_epoch: cutoffEpoch + 2
    }]
  }
});
if (!resolver.deletedMissionPointUids().includes(deletedUid.toLowerCase())) {
  throw new Error('i553 browser tombstone was not learned');
}
let tombstoneFiltered = resolver.filterLivePayload({
  markers: [{ uid: deletedUid, updated: cutoffIso, cot_type: 'a-f-G-U' }],
  euds: [{ uid: deletedUid, time: '2026-07-25T03:59:59.000Z', cot_type: 'a-f-G-U' }]
});
if (tombstoneFiltered.markers.length || tombstoneFiltered.euds.length) {
  throw new Error(`old retained live copies were not tombstoned: ${JSON.stringify(tombstoneFiltered)}`);
}
const newerLive = resolver.filterLivePayload({
  markers: [{ uid: deletedUid, updated: '2026-07-25T04:00:03.000Z', cot_type: 'a-f-G-U-C-D' }]
});
if (newerLive.markers.length !== 1 || newerLive.markers[0].uid !== deletedUid) {
  throw new Error(`newer CoT did not release tombstone: ${JSON.stringify(newerLive)}`);
}
if (resolver.deletedMissionPointUids().includes(deletedUid.toLowerCase())) {
  throw new Error('released browser tombstone remained active');
}

// Re-associating a UID with Data Sync must clear a tombstone immediately.
resolver.learnMissionPointUids({
  objects: [],
  data_sync_deleted_uid_tombstones_i553: {
    tombstones: [{ uid: deletedUid, cutoff_epoch: cutoffEpoch, observed_at_epoch: cutoffEpoch + 5 }]
  }
});
resolver.learnMissionPointUids({
  objects: [{ uid: deletedUid, lat: 35, lon: -117, cot_type: 'a-f-G-U-C-D' }],
  data_sync_deleted_uid_tombstones_i553: { tombstones: [] }
});
if (resolver.deletedMissionPointUids().includes(deletedUid.toLowerCase())) {
  throw new Error('mission re-association did not clear browser tombstone');
}
if (!resolver.missionPointUids().includes(deletedUid.toLowerCase())) {
  throw new Error('mission re-association did not restore exact UID ownership');
}

console.log('i553 browser Data Sync UID ownership and deletion tombstone tests passed');

process.exit(0);
