/* TAK Map i572 password-protected OpenTAKServer Mission unlock. */
(() => {
  'use strict';
  if (window.TakMapMissionUnlockI572) return;
  const VERSION='i572';
  const API='/api/tak-map/data-sync-mission-unlock-i572';
  const state={status:new Map(),pending:new Map(),active:null};
  const esc=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const key=mission=>String(mission||'').trim().toLowerCase();

  async function json(response){
    const text=await response.text(); let body={};
    try{body=text?JSON.parse(text):{};}catch(_){body={error:text||`HTTP ${response.status}`};}
    if(!response.ok||body.ok===false){const error=new Error(body.error||`HTTP ${response.status}`);error.status=response.status;error.payload=body;throw error;}
    return body;
  }
  async function status(mission,force=false){
    mission=String(mission||'').trim(); if(!mission) return {ok:true,protected:false,unlocked:true};
    const k=key(mission); if(!force&&state.status.has(k)) return state.status.get(k);
    const body=await json(await fetch(`${API}?mission=${encodeURIComponent(mission)}`,{cache:'no-store',credentials:'same-origin'}));
    state.status.set(k,body); return body;
  }
  function ensureStyle(){
    if(document.getElementById('takMapMissionUnlockStyleI572')) return;
    const style=document.createElement('style'); style.id='takMapMissionUnlockStyleI572';
    style.textContent=`
      #takMapMissionUnlockI572{position:fixed;inset:0;z-index:7600;display:grid;place-items:center;padding:20px;background:rgba(0,0,0,.62);backdrop-filter:blur(3px)}
      #takMapMissionUnlockI572[hidden]{display:none!important}
      #takMapMissionUnlockI572 .unlock-card-i572{width:min(430px,calc(100vw - 32px));border:1px solid #75828d;border-radius:13px;background:linear-gradient(180deg,#192733,#0b151e);box-shadow:0 28px 90px rgba(0,0,0,.72);color:#edf1f4;overflow:hidden}
      #takMapMissionUnlockI572 .unlock-head-i572{padding:15px 17px 11px;border-bottom:1px solid rgba(203,210,216,.22)}
      #takMapMissionUnlockI572 h2{margin:0 0 5px;font-size:17px}#takMapMissionUnlockI572 p{margin:0;color:#b8c2ca;font-size:11.5px;line-height:1.45}
      #takMapMissionUnlockI572 .unlock-body-i572{padding:14px 17px 17px}#takMapMissionUnlockI572 label{display:block;margin-bottom:6px;color:#d7dde2;font-size:11px;font-weight:800}
      #takMapMissionUnlockI572 input{box-sizing:border-box;width:100%;height:39px;padding:0 11px;border:1px solid #687682;border-radius:8px;background:#08121a;color:#f2f5f7;font:inherit;outline:none}
      #takMapMissionUnlockI572 input:focus{border-color:#d4dbe0;box-shadow:0 0 0 2px rgba(203,210,216,.18)}
      #takMapMissionUnlockI572 .unlock-status-i572{min-height:18px;margin-top:8px;color:#d4a8a4;font-size:10.5px;line-height:1.4}
      #takMapMissionUnlockI572 .unlock-actions-i572{display:flex;justify-content:flex-end;gap:8px;margin-top:12px}#takMapMissionUnlockI572 button{min-width:92px;min-height:34px;border:1px solid #687682;border-radius:8px;background:#17242e;color:#e9edf0;font-weight:800;cursor:pointer}
      #takMapMissionUnlockI572 button.primary{border-color:#e0e5e8;background:linear-gradient(180deg,#dde3e7,#aeb8bf);color:#111920}#takMapMissionUnlockI572 button:disabled{opacity:.55;cursor:wait}`;
    document.head.appendChild(style);
  }
  function modal(){
    ensureStyle(); let root=document.getElementById('takMapMissionUnlockI572'); if(root) return root;
    root=document.createElement('div'); root.id='takMapMissionUnlockI572'; root.hidden=true;
    root.innerHTML=`<form class="unlock-card-i572" autocomplete="off"><div class="unlock-head-i572"><h2>Unlock protected Mission</h2><p class="unlock-copy-i572"></p></div><div class="unlock-body-i572"><label for="takMapMissionPasswordI572">Mission password</label><input id="takMapMissionPasswordI572" type="password" autocomplete="new-password" maxlength="512" spellcheck="false"><div class="unlock-status-i572" aria-live="polite"></div><div class="unlock-actions-i572"><button type="button" data-cancel>Cancel</button><button type="submit" class="primary">Unlock</button></div></div></form>`;
    document.body.appendChild(root); return root;
  }
  function promptPassword(mission){
    return new Promise(resolve=>{
      const root=modal(), form=root.querySelector('form'), input=root.querySelector('input'), copy=root.querySelector('.unlock-copy-i572'), statusNode=root.querySelector('.unlock-status-i572'), submit=root.querySelector('button[type="submit"]'), cancel=root.querySelector('[data-cancel]');
      state.active={mission,resolve}; copy.textContent=`${mission} requires its OpenTAKServer Mission password before TAK Map can read or change Mission content.`; statusNode.textContent=''; input.value=''; root.hidden=false; setTimeout(()=>input.focus(),0);
      const finish=value=>{root.hidden=true;input.value='';form.onsubmit=null;cancel.onclick=null;state.active=null;resolve(value);};
      cancel.onclick=()=>finish(false);
      form.onsubmit=async event=>{event.preventDefault();const password=input.value;if(!password){statusNode.textContent='Enter the Mission password.';return;}submit.disabled=true;cancel.disabled=true;statusNode.textContent='Validating with OpenTAKServer…';
        try{const body=await json(await fetch(API,{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',cache:'no-store',body:JSON.stringify({action:'unlock',mission,password})}));state.status.set(key(mission),body);statusNode.textContent='Mission unlocked.';finish(true);}
        catch(error){statusNode.textContent=error.message||String(error);input.select();}
        finally{submit.disabled=false;cancel.disabled=false;input.value='';}
      };
    });
  }
  async function ensureUnlocked(mission){
    mission=String(mission||'').trim(); if(!mission) return true;
    const k=key(mission); if(state.pending.has(k)) return state.pending.get(k);
    const task=(async()=>{let info;try{info=await status(mission,true);}catch(_){info={protected:false,unlocked:true};}
      if(!info.protected||info.unlocked) return true;
      return promptPassword(mission);
    })().finally(()=>state.pending.delete(k)); state.pending.set(k,task); return task;
  }
  async function lock(mission){
    mission=String(mission||'').trim(); if(!mission) return false;
    const body=await json(await fetch(API,{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',cache:'no-store',body:JSON.stringify({action:'lock',mission})}));state.status.set(key(mission),body);return true;
  }
  window.TakMapMissionUnlockI572={version:VERSION,status,ensureUnlocked,open:ensureUnlocked,lock};
})();
