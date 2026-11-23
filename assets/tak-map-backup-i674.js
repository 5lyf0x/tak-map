/* TAK Map 1.4.0-i674 · encrypted, independently selective Backup/Restore */
(()=>{'use strict';
const cats=[['points','Points / Markers'],['shapes','Shapes / Areas'],['routes','Routes'],['basemaps','Added Basemaps'],['veil','XTAK VEIL Nodes & Credentials'],['geofences','Geofences & Settings'],['adsb','ADS-B Settings'],['gateway_data','Gateway Data Configuration'],['mesh_sync','Mesh Sync Settings / Certificates / QR'],['data_sync','Data Sync'],['local_data','Local Data'],['offline_maps','Offline Maps'],['satellite','Satellite Tracking Settings']];
const categoryForKey=k=>{
 k=String(k).toLowerCase();
 if(/satellite|celestrak|tle|sat\./.test(k))return 'satellite';
 if(/mesh|xtm1|xms1|token.?sync/.test(k))return 'mesh_sync';
 if(/veil|xtak/.test(k))return 'veil';
 if(/gateway|replay|takclient|ots/.test(k))return 'gateway_data';
 if(/data.?sync|mission|unlock/.test(k))return 'data_sync';
 if(/geofence/.test(k))return 'geofences';
 if(/adsb|aircraft/.test(k))return 'adsb';
 if(/basemap|layer.?stack|layer.?opacity|map.?style/.test(k))return 'basemaps';
 if(/offline|terrain|dem|elevation/.test(k))return 'offline_maps';
 if(/route|waypoint/.test(k))return 'routes';
 if(/marker|point|pin/.test(k))return 'points';
 if(/shape|drawing|polygon/.test(k))return 'shapes';
 if(/takmap|tak.map|tak-map/.test(k))return 'local_data';
 return null;
};
const dbForName=n=>{n=String(n).toLowerCase();if(/satellite|celestrak/.test(n))return 'satellite';if(/offline|terrain|dem|elevation|tile/.test(n))return 'offline_maps';if(/takmap|tak-map|tak_map/.test(n))return 'local_data';return null};
const $=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const request=async(path,data)=>{const r=await fetch('/api/tak-map/backup/'+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-TAK-Backup':'1'},body:JSON.stringify(data)});const x=await r.json();if(!r.ok||!x.ok)throw Error(x.error||'HTTP '+r.status);return x};
const u8toa=u8=>{let s='';for(let i=0;i<u8.length;i+=32768)s+=String.fromCharCode(...u8.subarray(i,i+32768));return btoa(s)};
const atou8=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
async function packValue(value,depth=0){
 if(depth>30)throw Error('Nested browser value exceeds safe depth');
 if(value==null||typeof value!=='object')return value;
 if(value instanceof Blob)return {__takmbk:'blob',mime:value.type,base64:u8toa(new Uint8Array(await value.arrayBuffer()))};
 if(value instanceof ArrayBuffer)return {__takmbk:'arraybuffer',base64:u8toa(new Uint8Array(value))};
 if(ArrayBuffer.isView(value))return {__takmbk:'typed',constructor:value.constructor.name,base64:u8toa(new Uint8Array(value.buffer,value.byteOffset,value.byteLength))};
 if(value instanceof Date)return {__takmbk:'date',value:value.toISOString()};
 if(value instanceof Map){const items=[];for(const [k,v] of value)items.push([await packValue(k,depth+1),await packValue(v,depth+1)]);return {__takmbk:'map',entries:items}}
 if(value instanceof Set){const items=[];for(const v of value)items.push(await packValue(v,depth+1));return {__takmbk:'set',items}}
 if(Array.isArray(value)){const items=[];for(const v of value)items.push(await packValue(v,depth+1));return items}
 const out={};for(const [k,v] of Object.entries(value))out[k]=await packValue(v,depth+1);return out;
}
function unpackValue(value,depth=0){
 if(depth>30)throw Error('Nested restore value exceeds safe depth');
 if(value==null||typeof value!=='object')return value;
 if(Array.isArray(value))return value.map(v=>unpackValue(v,depth+1));
 if(value.__takmbk){
   const x=value;
   if(x.__takmbk==='blob')return new Blob([atou8(x.base64)],{type:x.mime||''});
   if(x.__takmbk==='arraybuffer')return atou8(x.base64).buffer;
   if(x.__takmbk==='typed'){const bytes=atou8(x.base64);const constructors={Uint8Array,Int8Array,Uint16Array,Int16Array,Uint32Array,Int32Array,Float32Array,Float64Array,Uint8ClampedArray};const ctor=constructors[x.constructor]||Uint8Array;return new ctor(bytes.buffer)}
   if(x.__takmbk==='date')return new Date(x.value);
   if(x.__takmbk==='map')return new Map((x.entries||[]).map(([k,v])=>[unpackValue(k,depth+1),unpackValue(v,depth+1)]));
   if(x.__takmbk==='set')return new Set((x.items||[]).map(v=>unpackValue(v,depth+1)));
 }
 const out={};for(const [k,v] of Object.entries(value))out[k]=unpackValue(v,depth+1);return out;
}
async function takeDb(dbName){
 return new Promise((resolve,reject)=>{let req=indexedDB.open(dbName);req.onerror=()=>reject(req.error);req.onupgradeneeded=()=>{req.transaction.abort();reject(Error('Database unavailable: '+dbName))};req.onsuccess=async()=>{const db=req.result;try{const stores=[];for(const name of db.objectStoreNames){const rows=await new Promise((yes,no)=>{const tx=db.transaction(name,'readonly');const st=tx.objectStore(name);const items=[];const cur=st.openCursor();cur.onerror=()=>no(cur.error);cur.onsuccess=()=>{const c=cur.result;if(!c)return yes(items);items.push({key:c.key,value:c.value});c.continue()}});const packed=[];for(const row of rows)packed.push({key:await packValue(row.key),value:await packValue(row.value)});stores.push({name,keyPath:db.transaction(name,'readonly').objectStore(name).keyPath,autoIncrement:db.transaction(name,'readonly').objectStore(name).autoIncrement,rows:packed})}resolve({name:dbName,version:db.version,stores})}catch(e){reject(e)}finally{db.close()}}});
}
async function captureBrowser(selected){
 const out={};for(const c of selected)out[c]={localStorage:{},indexedDB:[]};
 for(let i=0;i<localStorage.length;i++){const key=localStorage.key(i);const cat=categoryForKey(key);if(cat&&out[cat])out[cat].localStorage[key]=localStorage.getItem(key)}
 if(!indexedDB.databases&&selected.some(c=>c==='offline_maps'||c==='satellite'||c==='local_data'))throw Error('This browser cannot enumerate its IndexedDB data. Use a Chromium browser with indexedDB.databases() support; no incomplete backup was created.');
 if(indexedDB.databases){for(const info of await indexedDB.databases()){const cat=dbForName(info.name);if(cat&&out[cat])out[cat].indexedDB.push(await takeDb(info.name))}}
 const sz=new Blob([JSON.stringify(out)]).size;if(sz>28*1024*1024)throw Error('Browser data is '+Math.ceil(sz/1048576)+' MB, beyond the safe inline transfer limit. No backup was created. Large IndexedDB packages require a separate streamed export.');
 return out;
}
async function restoreBrowser(data,selected){
 for(const cat of selected){const state=data[cat];if(!state)continue;
   for(const [k,v] of Object.entries(state.localStorage||{})){if(categoryForKey(k)===cat)localStorage.setItem(k,v)}
   for(const item of state.indexedDB||[]){if(dbForName(item.name)!==cat)throw Error('Unexpected browser database category');
     await new Promise((resolve,reject)=>{const req=indexedDB.open(item.name,item.version);req.onerror=()=>reject(req.error);req.onupgradeneeded=()=>{const db=req.result;for(const x of item.stores||[])if(!db.objectStoreNames.contains(x.name))db.createObjectStore(x.name,{keyPath:x.keyPath==null?undefined:x.keyPath,autoIncrement:!!x.autoIncrement})};req.onsuccess=async()=>{const db=req.result;try{for(const st of item.stores||[]){if(!db.objectStoreNames.contains(st.name))throw Error('Missing database store '+st.name);await new Promise((yes,no)=>{const tx=db.transaction(st.name,'readwrite');const s=tx.objectStore(st.name);for(const entry of st.rows||[]){const key=unpackValue(entry.key),val=unpackValue(entry.value);st.keyPath!=null?s.put(val):s.put(val,key)}tx.oncomplete=yes;tx.onerror=()=>no(tx.error)})}resolve()}catch(e){reject(e)}finally{db.close()}}})
   }
 }
}
function createModal(){
 if($('takmapBackupI674'))return;
 const style=document.createElement('style');style.id='takmapBackupStyleI674';style.textContent=`
 #takmapBackupI674{position:fixed;inset:0;z-index:250000;background:rgba(0,0,0,.76);display:flex;align-items:center;justify-content:center;padding:22px;box-sizing:border-box;color:#e5edf0;font-family:inherit}
 #takmapBackupI674 .mb-dialog{width:min(860px,96vw);max-height:92vh;overflow:auto;background:#101b24;border:1px solid #405261;border-radius:15px;box-shadow:0 20px 80px #000a;padding:22px;box-sizing:border-box}
 #takmapBackupI674 .mb-head{display:flex;justify-content:space-between;gap:14px;align-items:center;margin-bottom:14px}
 #takmapBackupI674 h2{margin:0;font-size:19px;letter-spacing:.06em}
 #takmapBackupI674 button{background:#233441;border:1px solid #435361;color:#e7f0f3;border-radius:8px;padding:9px 13px;cursor:pointer;font:inherit}
 #takmapBackupI674 button.primary{background:#22536d;border-color:#3c8bb1;font-weight:700}
 #takmapBackupI674 .mb-tabs,#takmapBackupI674 .mb-actions{display:flex;gap:9px;flex-wrap:wrap;margin:12px 0}
 #takmapBackupI674 .mb-categories{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin:12px 0}
 #takmapBackupI674 .mb-categories label{display:flex;align-items:center;gap:9px;border:1px solid #304451;border-radius:9px;padding:9px 11px;background:#14232e;font-size:13px}
 #takmapBackupI674 input[type=password],#takmapBackupI674 input[type=file]{max-width:100%;box-sizing:border-box;background:#07131c;color:#e5edf0;border:1px solid #485766;border-radius:8px;padding:10px;width:100%}
 #takmapBackupI674 .mb-field{display:grid;gap:7px;margin:12px 0;font-size:13px}
 #takmapBackupI674 .mb-info{font-size:12px;color:#a8b9c3;line-height:1.55}
 #takmapBackupI674 .mb-status{min-height:40px;padding:10px;border-radius:8px;background:#0a1720;white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}
 @media(max-width:640px){#takmapBackupI674{padding:5px}#takmapBackupI674 .mb-dialog{padding:14px;width:100%;max-height:98vh}#takmapBackupI674 .mb-categories{grid-template-columns:1fr}}`;
 document.head.appendChild(style);
 const overlay=document.createElement('div');overlay.id='takmapBackupI674';overlay.innerHTML=`<div class="mb-dialog" role="dialog" aria-modal="true" aria-labelledby="mbTitle"><div class="mb-head"><h2 id="mbTitle">BACKUP & RESTORE</h2><button id="mbClose" aria-label="Close">✕</button></div><div class="mb-tabs"><button id="mbTabBackup" class="primary">CREATE BACKUP</button><button id="mbTabRestore">RESTORE BACKUP</button></div><div class="mb-info">13 independently selectable categories. Encrypted backup includes TAK Map-owned data and credentials, not the Gateway, NDM, or VEIL servers.</div><div class="mb-actions"><button id="mbAll">Select All</button><button id="mbNone">Clear All</button></div><div class="mb-categories">${cats.map(([id,title])=>`<label><input type="checkbox" data-category="${id}" checked> ${esc(title)}</label>`).join('')}</div><div class="mb-field"><label for="mbPass">Encryption password (12+ characters, never stored)</label><input id="mbPass" type="password" autocomplete="new-password" minlength="12"></div><div id="mbBackupPart"><div class="mb-info">Offline packages are included when selected. Large browser-only IndexedDB collections may require a streamed export and will cause the backup to stop rather than omit data silently.</div><div class="mb-actions"><button id="mbCreate" class="primary">Create & Download Backup</button></div></div><div id="mbRestorePart" hidden><div class="mb-field"><label for="mbFile">Select encrypted TAK Map backup (.takmbk)</label><input type="file" id="mbFile" accept=".takmbk"></div><div class="mb-actions"><button id="mbInspect">Verify & Preview</button><button id="mbRestore" class="primary" disabled>Restore Selected</button></div><div class="mb-info">Selected configuration is restored from the verified archive. Mesh/Data Sync restoration requires an automatic, brief TAK Map service restart. This does not rewind newer updates on other devices; review peer revision history before reenabling synchronization.</div></div><div class="mb-status" id="mbStatus" role="status">Ready.</div></div>`;
 document.body.appendChild(overlay);
 const state={tab:'backup',file:null,preview:null};const status=(s)=>{$('mbStatus').textContent=String(s)};
 const sel=()=>Array.from(overlay.querySelectorAll('[data-category]:checked')).map(x=>x.dataset.category);
 const tab=(mode)=>{state.tab=mode;$('mbBackupPart').hidden=mode!=='backup';$('mbRestorePart').hidden=mode!=='restore';$('mbTabBackup').classList.toggle('primary',mode==='backup');$('mbTabRestore').classList.toggle('primary',mode==='restore');status('Ready.');};
 $('mbClose').onclick=()=>overlay.remove();overlay.addEventListener('click',e=>{if(e.target===overlay)overlay.remove()});
 $('mbTabBackup').onclick=()=>tab('backup');$('mbTabRestore').onclick=()=>tab('restore');$('mbAll').onclick=()=>overlay.querySelectorAll('[data-category]').forEach(x=>x.checked=true);$('mbNone').onclick=()=>overlay.querySelectorAll('[data-category]').forEach(x=>x.checked=false);
 const password=()=>{const p=$('mbPass').value;if(p.length<12)throw Error('Enter a backup password of at least 12 characters');return p};
 $('mbCreate').onclick=async()=>{const button=$('mbCreate');button.disabled=true;try{const selected=sel();if(!selected.length)throw Error('Choose at least one category');const pw=password();status('Capturing browser-owned settings and local data…');const browser=await captureBrowser(selected);status('Creating encrypted, verified server backup…');const result=await request('create',{categories:selected,password:pw,browser});status('Encrypted backup created. Downloading '+result.file+' ('+Math.ceil(result.bytes/1048576)+' MB)…');const a=document.createElement('a');a.href='/api/tak-map/backup/download?file='+encodeURIComponent(result.file);a.download=result.file;document.body.append(a);a.click();a.remove();status('Backup created and download requested: '+result.file+'. Store the password separately.');}catch(e){status('Backup failed: '+e.message)}finally{button.disabled=false}};
 $('mbFile').onchange=()=>{state.file=null;state.preview=null;$('mbRestore').disabled=true;status('Choose Verify & Preview to check the archive.')};
 $('mbInspect').onclick=async()=>{try{const f=$('mbFile').files[0];if(!f)throw Error('Select a backup file');const pw=password();status('Uploading encrypted file…');const r=await fetch('/api/tak-map/backup/upload',{method:'POST',body:f,credentials:'same-origin',headers:{'Content-Type':'application/octet-stream','X-TAK-Backup':'1'}});const up=await r.json();if(!r.ok||!up.ok)throw Error(up.error||'Upload failed');state.file=up.file;status('Verifying password, integrity, categories and archive contents…');const info=await request('inspect',{file:state.file,password:pw});state.preview=info;overlay.querySelectorAll('[data-category]').forEach(x=>{x.disabled=!info.categories.includes(x.dataset.category);x.checked=info.categories.includes(x.dataset.category)});$('mbRestore').disabled=false;status('Verified '+info.files+' files. Available: '+info.categories.join(', ')+'. Source: '+info.source_version+'. Choose categories and restore mode.');}catch(e){status('Verification failed: '+e.message)}};
 $('mbRestore').onclick=async()=>{const btn=$('mbRestore');btn.disabled=true;try{const selected=sel();if(!selected.length)throw Error('No categories selected');if(!state.file||!state.preview)throw Error('Verify backup first');const pw=password();const sync=selected.some(x=>x==='mesh_sync'||x==='data_sync');if(!confirm('Replace the selected TAK Map categories on this server? Existing selected settings may be overwritten.'))return;status('Verifying selected categories…');await request('restore',{file:state.file,password:pw,categories:selected,preview_only:true,confirm:'RESTORE'});
 if(sync){
    const typed=prompt('Mesh/Data Sync journal migration requires a TAK Map restart and may conflict with newer remote revisions. Confirm that peers will be reconciled before resuming. Type REPLACE SYNC JOURNALS to proceed:');
    if(typed!=='REPLACE SYNC JOURNALS')throw Error('Sync migration confirmation was not provided');
    const browserResult=await request('browser',{file:state.file,password:pw,categories:selected});
    status('Scheduling isolated journal restore. TAK Map will restart briefly…');
    const task=await request('schedule',{file:state.file,password:pw,categories:selected,sync_confirmation:typed});
    let answer=null;
    for(let i=0;i<180;i++){
      await new Promise(resolve=>setTimeout(resolve,2000));
      try{const r=await fetch('/api/tak-map/backup/job-status?job='+encodeURIComponent(task.job)+'&check='+encodeURIComponent(task.read_token),{credentials:'same-origin',cache:'no-store'});const j=await r.json();if(j.pending){status('Journal migration is in progress. TAK Map may restart…');continue}answer=j;break}catch(e){status('Waiting for TAK Map to restart and report restore result…')}
    }
    if(!answer)throw Error('Restore job has not returned; check the TAK Map service logs before retrying');
    if(!answer.ok)throw Error(answer.error||'Maintenance restore failed');
    await restoreBrowser(browserResult.browser||{},selected);
    status('Restore completed after TAK Map restart. '+answer.files_restored+' server files updated. Check peer synchronization before enabling Mesh/Data Sync.');
 }else{
    status('Restoring selected server data…');
    const result=await request('restore',{file:state.file,password:pw,categories:selected,confirm:'RESTORE'});
    status('Server restore completed. Applying browser-owned settings…');
    await restoreBrowser(result.browser||{},selected);
    status('Restore completed. '+result.files_restored+' server files updated. Reload TAK Map to apply all settings.');
 }}catch(e){status('Restore not completed: '+e.message)}finally{btn.disabled=false}};
 tab('backup');$('mbClose').focus();
}
window.TakMapBackupI674=Object.freeze({open:()=>createModal(),categories:cats.map(x=>x[0]),captureBrowser});
})();
