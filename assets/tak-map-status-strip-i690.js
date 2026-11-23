/* TAK Map i690 status strip. Read-only consumer; never touches Leaflet, Cesium, or sidebar DOM. */
(function(){'use strict';
  if(window.TakMapStatusStripI690)return;
  const D=document,$=id=>D.getElementById(id);
  const S={mounted:false,busyEuds:false,busyLan:false,euds:null,veil:null,lan:null,failedEuds:false,failedVeil:false,failedLan:false,opened:'',activeKey:'',polls:0,rows:new Map(),lastOkEuds:0,lastOkVeil:0,timers:[],lastStatus:'',shell:null,items:{}};
  const esc=x=>String(x==null?'':x);
  function updateText(el,value){if(el&&el.textContent!==esc(value))el.textContent=esc(value)}
  function dot(id,kind){const el=$(id);if(!el)return;const cls='i690-dot '+(kind||'unknown');if(el.className!==cls)el.className=cls}
  function button(key,title){const b=D.createElement(key==='lan'||key==='internet'||key==='tak'?'span':'button');b.className='i690-status-item'+(b.tagName==='BUTTON'?' i690-clickable':'');b.id='statusI690'+key[0].toUpperCase()+key.slice(1);if(b.tagName==='BUTTON'){b.type='button';b.setAttribute('aria-haspopup','dialog');b.setAttribute('aria-expanded','false');b.addEventListener('click',ev=>{ev.preventDefault();ev.stopPropagation();toggle(key,b)})}
    const d=D.createElement('span');d.className='i690-dot unknown';d.id='dotI690'+key;const label=D.createElement('span');label.className='i690-label';label.textContent=title+':';const v=D.createElement('span');v.id='valueI690'+key;v.className='i690-value';v.textContent='—';b.append(d,label,v);S.items[key]=b;return b}
  function mount(){if(S.mounted)return true;const banner=$('mapStatusBanner');if(!banner)return false;
    let legacy=$('statusLegacyI690');if(!legacy){legacy=D.createElement('span');legacy.id='statusLegacyI690';legacy.hidden=true;while(banner.firstChild)legacy.appendChild(banner.firstChild);banner.appendChild(legacy)}
    const sc=D.createElement('div');sc.className='i690-status-items';sc.id='statusItemsI690';sc.setAttribute('aria-label','TAK Map connection and activity status');
    for(const [key,title] of [['euds','EUDs'],['veil','VEIL'],['downloads','Downloads'],['lan','LAN'],['internet','Internet'],['tak','TAK Server']])sc.appendChild(button(key,title));banner.appendChild(sc);
    const p=D.createElement('div');p.id='statusDropdownI690';p.setAttribute('role','dialog');p.setAttribute('aria-label','Status details');p.innerHTML='<div class="i690-panel-head"><b id="i690PanelTitle">Status</b><button type="button" id="i690Close" aria-label="Close status details">×</button></div><div id="i690PanelSummary" class="i690-panel-summary"></div><div id="i690PanelRows" class="i690-panel-rows"></div>';D.body.appendChild(p);p.querySelector('#i690Close').addEventListener('click',()=>close());
    D.addEventListener('pointerdown',ev=>{if(!S.opened)return;if(p.contains(ev.target)||ev.target.closest('#statusItemsI690'))return;close()},{passive:true});D.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&S.opened){close();S.items[S.opened]?.focus()}});window.addEventListener('resize',()=>{if(S.opened)position()},{passive:true});
    // Legacy scripts may keep updating their own hidden status elements; these are
    // intentionally not the authoritative i690 nodes. Preserve them for compatibility.
    S.shell=p;S.mounted=true;return true}
  function close(){if(!S.opened)return;const old=S.opened;S.opened='';S.activeKey='';S.shell.classList.remove('active');S.items[old]?.setAttribute('aria-expanded','false')}
  function position(){const trg=S.items[S.opened],p=S.shell;if(!trg||!p)return;const r=trg.getBoundingClientRect();const width=p.offsetWidth||274,height=p.offsetHeight||222;
    const left=Math.max(8,Math.min(r.left,window.innerWidth-width-8));const top=Math.min(Math.max(88,r.bottom+6),Math.max(8,window.innerHeight-height-8));p.style.left=Math.round(left)+'px';p.style.top=Math.round(top)+'px'}
  function toggle(key){if(S.opened===key){close();return}if(S.opened)close();S.opened=key;S.items[key]?.setAttribute('aria-expanded','true');S.shell.classList.add('active');renderMenu(true);position()}
  function rowLabel(key,row){if(key==='euds')return esc(row.callsign||row.client_label||row.client||row.uid||'Unknown EUD');return esc(row.name||row.displayName||row.nodeId||'VEIL node')}
  function syncRows(key,arr){const host=$('i690PanelRows'),needed=new Set();let position=host.firstChild;for(const row of arr){const id=esc(key==='euds'?(row.uid||row.callsign):(row.nodeId));if(!id)continue;const tag=key+':'+id;needed.add(tag);let b=S.rows.get(tag);if(!b){b=D.createElement('button');b.type='button';b.className='i690-row';b.dataset.key=tag;const head=D.createElement('div');head.className='i690-row-title';const indicator=D.createElement('span');indicator.className='i690-node-dot';const name=D.createElement('span');name.className='i690-name';head.append(indicator,name);const sub=D.createElement('div');sub.className='i690-row-sub';b.append(head,sub);b.addEventListener('click',()=>activateRow(key,id));S.rows.set(tag,b)}
      const title=b.querySelector('.i690-name'),sub=b.querySelector('.i690-row-sub'),indicator=b.querySelector('.i690-node-dot');updateText(title,rowLabel(key,row));let descriptor='';let kind='unknown';
      if(key==='euds'){descriptor=[row.client_label||row.client,row.team].filter(Boolean).join(' · ')||esc(row.status||'Connected');kind='good'}
      else{const rx=row.state==='receiving',subscribed=!!row.apiSubscribed,api=esc(row.apiState||'').toLowerCase();kind=rx||api==='connected'?'good':subscribed?'warn':'unknown';descriptor='UDP: '+(rx?'Receiving':row.state==='waiting'?'Waiting':'Inactive')+' · API: '+(subscribed?(row.apiState||'Subscribed'):'Not subscribed')}
      updateText(sub,descriptor);const cls='i690-node-dot '+kind;if(indicator.className!==cls)indicator.className=cls;
      if(b!==position)host.insertBefore(b,position);position=b.nextSibling; // no DOM move when order is unchanged
    }
    for(const [tag,b] of S.rows){if(!tag.startsWith(key+':'))continue;if(!needed.has(tag)){b.remove();S.rows.delete(tag)}}
    if(!arr.length){let empty=host.querySelector('.i690-empty');if(!empty){empty=D.createElement('div');empty.className='i690-empty';host.append(empty)}updateText(empty,key==='veil'?'No connected or subscribed VEIL nodes':'No connected EUDs')}else{host.querySelector('.i690-empty')?.remove()}
  }
  function renderMenu(force){if(!S.opened)return;const key=S.opened;
    let title=key==='euds'?'Connected EUDs':key==='veil'?'VEIL Nodes':key==='downloads'?'Downloads':'Status';updateText($('i690PanelTitle'),title);
    const rows=key==='euds'?(S.euds||[]):key==='veil'?(S.veil?.nodes||[]).filter(x=>x.state==='receiving'||x.apiSubscribed):[];
    let summary='';if(key==='euds')summary=S.failedEuds?'Stale — last successful snapshot':rows.length+' connected';else if(key==='veil')summary=S.failedVeil?'Stale — last successful snapshot':((S.veil?.receiving||0)+' receiving · '+rows.filter(x=>x.apiSubscribed).length+' subscribed');else if(key==='downloads')summary='Active downloads: '+(S.downloadCount??'—');
    updateText($('i690PanelSummary'),summary);$('i690PanelSummary').classList.toggle('i690-stale',key==='euds'?S.failedEuds: key==='veil'?S.failedVeil:false);
    const holder=$('i690PanelRows');const scroll=S.shell.scrollTop;const focused=D.activeElement?.dataset?.key||'';
    for(const [tag,b] of S.rows){if(!tag.startsWith(key+':')){b.remove();S.rows.delete(tag)}}
    if(key==='downloads'){
      for(const b of S.rows.values())b.remove();S.rows.clear();if(!holder.querySelector('.i690-empty')){const e=D.createElement('div');e.className='i690-empty';holder.appendChild(e)}updateText(holder.querySelector('.i690-empty'),(S.downloadCount||0)?'Download activity in Offline Maps':'No downloads active');
    }else syncRows(key,rows);
    S.shell.scrollTop=scroll; if(focused){const target=Array.from(holder.querySelectorAll('.i690-row')).find(b=>b.dataset.key===focused);if(target&&D.activeElement!==target)target.focus({preventScroll:true})}
    if(force)position()
  }
  function activateRow(key,id){if(key==='veil'){const open=window.TakMapVeilI666?.openNodeDetails;if(typeof open==='function'&&open(id)){close();return}const card=$('takVeilCardI665');if(card){card.scrollIntoView({behavior:'smooth',block:'center'});close()}return}
    // EUD status is read-only; no implicit map movement or object selection.
  }
  function normalizeEuds(json){if(!json||json.ok!==true||!Array.isArray(json.euds))throw Error('Invalid EUD response');const unique=new Map();for(const x of json.euds){const id=esc(x.uid||x.callsign).trim().toLowerCase();if(!id)continue;unique.set(id,x)}return [...unique.values()].sort((a,b)=>rowLabel('euds',a).localeCompare(rowLabel('euds',b))||esc(a.uid).localeCompare(esc(b.uid)))}
  async function fetchEuds(){if(S.busyEuds)return;S.busyEuds=true;const ctrl=new AbortController(),to=setTimeout(()=>ctrl.abort(),6500);try{
    const r=await fetch('/api/tak-map/euds?online=1',{cache:'no-store',credentials:'same-origin',signal:ctrl.signal});if(!r.ok||!String(r.headers.get('content-type')||'').includes('application/json'))throw Error('EUD endpoint unavailable');const next=normalizeEuds(await r.json());S.euds=next;S.failedEuds=false;S.lastOkEuds=Date.now();updateText($('valueI690euds'),next.length);dot('dotI690euds',next.length?'good':'unknown');if(S.opened==='euds')renderMenu(false)
  }catch(_){S.failedEuds=true;updateText($('valueI690euds'),'—');dot('dotI690euds','warn');if(S.opened==='euds')renderMenu(false)}finally{clearTimeout(to);S.busyEuds=false}}
  function recentTime(v){if(!v)return false;let t=typeof v==='number'?v*1000:Date.parse(String(v));if(!Number.isFinite(t))return false;return Date.now()-t>=-5000&&Date.now()-t<90000}
  function veilSnapshot(s){if(!s||s.ok!==true||!Array.isArray(s.nodes))return;const config=s.config||{},by=new Map();for(const node of s.nodes){const id=esc(node.nodeId).trim();if(id)by.set(id,node)}const nodes=[...by.values()].sort((a,b)=>{const score=x=>x.state==='receiving'?0:x.apiState==='connected'?1:x.apiSubscribed?2:3;return score(a)-score(b)||rowLabel('veil',a).localeCompare(rowLabel('veil',b))||esc(a.nodeId).localeCompare(esc(b.nodeId))});
    const receiving=config.enabled===false?0:nodes.filter(x=>x.state==='receiving'||(x.apiSubscribed&&x.apiState==='connected'&&recentTime(x.apiLastSync))).length;S.veil={nodes,receiving};S.failedVeil=false;S.lastOkVeil=Date.now();updateText($('valueI690veil'),receiving);dot('dotI690veil',receiving?'good':'unknown');if(S.opened==='veil')renderMenu(false)}
  function veilFailed(){S.failedVeil=true;updateText($('valueI690veil'),'—');dot('dotI690veil','warn');if(S.opened==='veil')renderMenu(false)}
  async function fetchLan(){if(S.busyLan)return;S.busyLan=true;const ctrl=new AbortController(),to=setTimeout(()=>ctrl.abort(),5500);try{const r=await fetch('/api/tak-map/status-network-i690',{cache:'no-store',credentials:'same-origin',signal:ctrl.signal});if(!r.ok||!String(r.headers.get('content-type')||'').includes('application/json'))throw Error('LAN API');const j=await r.json();if(!j.ok)throw Error('LAN API');S.lan=j.lan||{};const status=esc(S.lan.state||'Unknown');updateText($('valueI690lan'),status);dot('dotI690lan',status==='Available'?'good':status==='Offline'?'bad':'unknown');const tak=S.items.tak;const show=!!j.tak?.configured&&!!j.tak?.enabled;tak.hidden=!show;if(show){const v=esc(j.tak.state||'Unknown');updateText($('valueI690tak'),v);dot('dotI690tak',(v==='Connected'||v==='Running')?'good':v==='Offline'?'bad':'unknown')}
  }catch(_){updateText($('valueI690lan'),'Unknown');dot('dotI690lan','unknown');S.items.tak.hidden=true}finally{clearTimeout(to);S.busyLan=false}}
  function mirrorLegacy(){const dn=$('bannerDownloads'),ind=$('bannerInternet');if(dn){const raw=dn.textContent?.trim()||'0 Active';const num=Number.parseInt(raw,10);S.downloadCount=Number.isFinite(num)?num:0;updateText($('valueI690downloads'),raw);dot('dotI690downloads',S.downloadCount?'warn':'unknown')}
    if(ind){const raw=ind.textContent?.trim()||'Unknown';updateText($('valueI690internet'),raw);const d=$('bannerInternetDot');dot('dotI690internet',d?.classList.contains('good')?'good':d?.classList.contains('bad')?'bad':d?.classList.contains('warn')?'warn':'unknown')}
    if(S.opened==='downloads')renderMenu(false)
  }
  function boot(){if(!mount())return false;S.items.tak.hidden=true;S.items.euds.setAttribute('title','Connected EUDs');S.items.veil.setAttribute('title','Connected or subscribed VEIL nodes');S.items.downloads.setAttribute('title','Active downloads');
    D.addEventListener('takmap:veil-status-i690',e=>veilSnapshot(e.detail));D.addEventListener('takmap:veil-error-i690',veilFailed);
    const existing=window.TakMapVeilI666?.getStatus?.();if(existing?.ok)veilSnapshot(existing);
    fetchEuds();fetchLan();mirrorLegacy();
    S.timers.push(setInterval(()=>{if(!D.hidden)fetchEuds()},10000));S.timers.push(setInterval(()=>{if(!D.hidden)fetchLan()},30000));S.timers.push(setInterval(()=>{if(!D.hidden)mirrorLegacy()},2500));
    D.addEventListener('visibilitychange',()=>{if(!D.hidden){fetchEuds();fetchLan();mirrorLegacy()}});
    window.TakMapStatusStripI690={version:'i690',state:S,diagnostics:()=>({mounted:S.mounted,open:S.opened,eudCount:S.euds?.length,veilCount:S.veil?.receiving,failedEuds:S.failedEuds,failedVeil:S.failedVeil,polls:S.polls,intervals:S.timers.length})};return true}
  if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',()=>boot(),{once:true});else boot();
})();
