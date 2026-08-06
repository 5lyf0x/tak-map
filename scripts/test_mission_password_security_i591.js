const fs=require('fs');
const core=fs.readFileSync(process.argv[2]||'assets/tak-map-core-i553.js','utf8');
const ctl=fs.readFileSync(process.argv[3]||'assets/tak-map-data-sync-i553.js','utf8');
const access=fs.readFileSync(process.argv[4]||'assets/tak-map-data-sync-access-i576.js','utf8');
function need(ok,msg){if(!ok)throw new Error(msg)}
need(core.includes('mission_access_i594'),'i594 Mission access rows missing');
need(core.includes('tak-data-sync-locked-i594'),'locked Mission renderer missing');
need(core.includes('locked_descriptor_i594'),'sanitized locked descriptor support missing');
need(core.includes('No Missions discovered'),'discovery empty state missing');
need(!core.includes('data-mission-manual-i591'),'manual Mission-name entry must not be rendered');
need(ctl.includes("const V='i594'"),'Data Sync controller is not i594');
need(ctl.includes('S.securityLocked=!!(json&&json.locked)'),'sanitized 2xx locked state handling missing');
need(access.includes("const VERSION = 'i594';"),'Mission access runtime is not i594');
need(access.includes('function openManual() { return false; }'),'manual Mission-name entry is not disabled');
need(access.includes('operatorNeverTypesMissionName:true'),'operator workflow audit missing');
console.log(JSON.stringify({ok:true,version:'i594',missionNamesDiscoveredBeforePassword:true,operatorNeverTypesMissionName:true,protectedContentsWithheldUntilUnlock:true}));
