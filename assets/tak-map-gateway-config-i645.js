/* Staged i645 Gateway Data connection editor. Gateway Data only; Replay unchanged. */
(function(w,d){'use strict';
const V='i645-staging',BASE='/api/tak-map/gateway-data/settings';
const $=id=>d.getElementById(id);
let open=false,busy=false,previousFocus=null;
function styles(){if($('takGatewayConfigStyleI645'))return;
 const el=d.createElement('style');el.id='takGatewayConfigStyleI645';el.textContent=`
.gateway-data-v491 .gateway-config-actions-i645{display:flex;flex:0 0 auto;align-items:center;gap:6px}
.gateway-data-v491 .gateway-config-actions-i645 .layer-button{font-size:.76rem;padding:5px 7px;white-space:nowrap}
#takGatewayConfigModalI645{position:fixed;inset:0;z-index:2147483000;background:rgba(0,0,0,.73);display:flex;align-items:center;justify-content:center;padding:15px;box-sizing:border-box}
#takGatewayConfigModalI645[hidden],#takGatewayConfigModalI645 [hidden]{display:none!important}
#takGatewayConfigModalI645 *{box-sizing:border-box}
#takGatewayConfigModalI645 .gwc-dialog{width:min(100%,570px);max-height:min(90vh,780px);overflow:auto;border:1px solid #3b4c59;border-radius:13px;background:#101b25;color:#e8f2f7;box-shadow:0 22px 80px rgba(0,0,0,.68);font-family:inherit}
#takGatewayConfigModalI645 .gwc-heading{display:flex;align-items:center;justify-content:space-between;padding:18px 20px 12px;border-bottom:1px solid rgba(255,255,255,.10)}
#takGatewayConfigModalI645 h2{margin:0;color:#fff;font-size:1.1rem}
#takGatewayConfigModalI645 h3{margin:0 0 9px;font-size:.83rem;color:#c8d9e2}
#takGatewayConfigModalI645 .gwc-close{border:0;background:transparent;color:#d6e4ed;font-size:24px;padding:0 5px;cursor:pointer}
#takGatewayConfigModalI645 form{padding:16px 20px 20px}
#takGatewayConfigModalI645 p{margin:0 0 15px;color:#9db0be;font-size:.82rem;line-height:1.5}
#takGatewayConfigModalI645 .gwc-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px 12px;margin-bottom:16px}
#takGatewayConfigModalI645 label{display:flex;flex-direction:column;gap:5px;min-width:0;color:#cbd7df;font-size:.78rem;font-weight:650}
#takGatewayConfigModalI645 .gwc-wide{grid-column:1/-1}
#takGatewayConfigModalI645 input:not([type=checkbox]),#takGatewayConfigModalI645 select{min-height:37px;width:100%;border:1px solid #445968;border-radius:8px;background:#0a141d;color:#edf5fa;padding:8px;font:inherit;font-size:.89rem}
#takGatewayConfigModalI645 input:focus-visible,#takGatewayConfigModalI645 select:focus-visible,#takGatewayConfigModalI645 button:focus-visible{outline:2px solid #ff813e;outline-offset:2px}
#takGatewayConfigModalI645 .gwc-check{display:flex;flex-direction:row;align-items:center;gap:9px;margin-bottom:12px}
#takGatewayConfigModalI645 .gwc-check input{width:15px;height:15px;accent-color:#ff813e}
#takGatewayConfigModalI645 .gwc-subsection{padding-top:13px;border-top:1px solid rgba(255,255,255,.12)}
#takGatewayConfigModalI645 .gwc-details{display:grid;grid-template-columns:1fr;gap:10px;margin-bottom:13px}
#takGatewayConfigModalI645 .gwc-note{font-size:.76rem;color:#9fb1bf;background:rgba(255,255,255,.04);border-radius:7px;padding:9px 10px;line-height:1.4}
#takGatewayConfigModalI645 .gwc-status{min-height:22px;font-size:.83rem;margin:12px 0;white-space:pre-wrap;color:#afbfca}
#takGatewayConfigModalI645 .gwc-status.error{color:#ff9790}
#takGatewayConfigModalI645 .gwc-status.success{color:#70dea9}
#takGatewayConfigModalI645 .gwc-actions{display:flex;justify-content:flex-end;gap:9px;flex-wrap:wrap;margin-top:14px}
#takGatewayConfigModalI645 button.gwc-button{min-height:35px;border:1px solid #526473;border-radius:8px;padding:7px 13px;background:#263645;color:#e8f2f7;cursor:pointer;font-weight:750}
#takGatewayConfigModalI645 button.gwc-primary{background:#ee7534;border-color:#ef9b65;color:#131820}
#takGatewayConfigModalI645 button:disabled{opacity:.45;cursor:not-allowed}
@media(max-width:520px){#takGatewayConfigModalI645{padding:7px}#takGatewayConfigModalI645 form{padding:13px}#takGatewayConfigModalI645 .gwc-heading{padding:13px}#takGatewayConfigModalI645 .gwc-grid{grid-template-columns:1fr}#takGatewayConfigModalI645 .gwc-wide{grid-column:auto}}
`;d.head.appendChild(el)}
function button(){const row=$('gatewayDataStatusV476')?.parentElement,refresh=$('gatewayDataRefreshV476');
 if(!row||!refresh)return;
 let group=$('gatewayConfigActionGroupI645');
 if(!group||group.parentElement!==row){group=d.createElement('div');group.id='gatewayConfigActionGroupI645';group.className='gateway-config-actions-i645';refresh.insertAdjacentElement('beforebegin',group);group.appendChild(refresh)}
 if(!$('gatewayConfigButtonI645')){const btn=d.createElement('button');btn.type='button';btn.id='gatewayConfigButtonI645';btn.className='layer-button';btn.textContent='Configure';btn.title='Configure TAK Gateway data connection';btn.addEventListener('click',show);group.insertBefore(btn,refresh)}
}
function createModal(){if($('takGatewayConfigModalI645'))return;styles();const overlay=d.createElement('div');overlay.id='takGatewayConfigModalI645';overlay.hidden=true;
 overlay.innerHTML=`<div class="gwc-dialog" role="dialog" aria-modal="true" aria-labelledby="gwcTitleI645" tabindex="-1">
 <div class="gwc-heading"><h2 id="gwcTitleI645">Configure TAK Gateway</h2><button type="button" id="gwcCloseI645" class="gwc-close" aria-label="Close configuration">×</button></div>
 <form id="gwcFormI645" autocomplete="off"><p>Configure the server-side Gateway Data connection. These settings do not change Replay or TAK Gateway security policy.</p>
 <div class="gwc-grid"><label class="gwc-wide">Gateway IP address or hostname<input id="gwcHostI645" required placeholder="10.10.10.101" maxlength="253" spellcheck="false"></label>
 <label>Protocol<select id="gwcProtocolI645"><option value="http">HTTP (trusted LAN / VPN)</option><option value="https">HTTPS</option></select></label>
 <label>Port<input id="gwcPortI645" required type="number" min="1" max="65535" step="1" value="8090"></label>
 <label class="gwc-wide">Client authentication<select id="gwcAuthI645"><option value="none">No client certificate</option><option value="auto">Automatic — use existing certificate when present</option><option value="certificate">Require client certificate</option></select></label></div>
 <div class="gwc-subsection"><h3>Security and certificates</h3><label class="gwc-check"><input id="gwcVerifyI645" type="checkbox" checked>Verify the Gateway HTTPS server certificate</label>
 <div id="gwcCaBlockI645" class="gwc-details"><label>Gateway CA certificate path (on TAK Map server)<input id="gwcCaI645" placeholder="Existing system trust or /etc/tak-map/replay-ca.crt" spellcheck="false"></label></div>
 <div id="gwcClientBlockI645" class="gwc-details"><label>Client certificate path (on TAK Map server)<input id="gwcCertI645" placeholder="/etc/tak-map/replay-client.crt" spellcheck="false"></label><label>Client private key path (on TAK Map server)<input id="gwcKeyI645" placeholder="/etc/tak-map/replay-client.key" spellcheck="false"></label></div>
 <div id="gwcNetworkNoteI645" class="gwc-note"></div></div>
 <div id="gwcStatusI645" role="status" aria-live="polite" class="gwc-status"></div>
 <div class="gwc-actions"><button id="gwcCancelI645" class="gwc-button" type="button">Cancel</button><button id="gwcTestI645" class="gwc-button" type="button">Test Connection</button><button id="gwcSaveI645" class="gwc-button gwc-primary" type="submit">Save</button></div></form></div>`;
 d.body.appendChild(overlay);
 $('gwcCloseI645').addEventListener('click',hide);$('gwcCancelI645').addEventListener('click',hide);
 $('gwcProtocolI645').addEventListener('change',()=>{const port=$('gwcPortI645');if(port.value==='8090'||port.value==='9443')port.value=$('gwcProtocolI645').value==='https'?'9443':'8090';if($('gwcProtocolI645').value==='https')$('gwcVerifyI645').checked=true;else $('gwcAuthI645').value='none';refreshChoices()});
 $('gwcAuthI645').addEventListener('change',refreshChoices);
 $('gwcVerifyI645').addEventListener('change',refreshChoices);
 $('gwcTestI645').addEventListener('click',()=>submit(true));
 $('gwcFormI645').addEventListener('submit',event=>{event.preventDefault();submit(false)});
 overlay.addEventListener('click',event=>{if(event.target===overlay)hide()});
 d.addEventListener('keydown',event=>{if(!open)return;if(event.key==='Escape'){event.preventDefault();hide()}else if(event.key==='Tab'){const nodes=Array.from(overlay.querySelectorAll('button:not(:disabled),input:not(:disabled),select:not(:disabled)')).filter(n=>n.getClientRects().length);const index=nodes.indexOf(d.activeElement);if(!event.shiftKey&&index===nodes.length-1){event.preventDefault();nodes[0]?.focus()}else if(event.shiftKey&&index===0){event.preventDefault();nodes[nodes.length-1]?.focus()}}});
}
function status(message,kind=''){const el=$('gwcStatusI645');if(!el)return;el.textContent=message||'';el.className='gwc-status'+(kind?' '+kind:'')}
function refreshChoices(){const protocol=$('gwcProtocolI645').value,auth=$('gwcAuthI645').value,secure=protocol==='https';
 $('gwcCaBlockI645').hidden=!secure;$('gwcClientBlockI645').hidden=auth==='none';
 const verify=$('gwcVerifyI645');if(!secure)verify.checked=false;else if(auth==='none')verify.checked=true;
 verify.disabled=!secure||auth==='none';
 $('gwcNetworkNoteI645').textContent=!secure?
 'HTTP is unencrypted. Use it only on a private trusted LAN or VPN. Select No client certificate. The Gateway must allow your TAK Map server in Configure Security.':
 'HTTPS verifies the Gateway server. A custom CA may be needed for self-signed certificates. The Gateway must permit this authentication mode in Configure Security.';
}
function form(){return {host:$('gwcHostI645').value.trim(),protocol:$('gwcProtocolI645').value,port:$('gwcPortI645').value,auth_mode:$('gwcAuthI645').value,
 verify_tls:$('gwcVerifyI645').checked,ca_cert_path:$('gwcCaI645').value.trim(),client_cert_path:$('gwcCertI645').value.trim(),client_key_path:$('gwcKeyI645').value.trim()}}
function busyState(value){busy=value;for(const id of ['gwcTestI645','gwcSaveI645','gwcCancelI645','gwcCloseI645'])$(id).disabled=value}
async function request(url,options={}){const response=await fetch(url,{credentials:'same-origin',cache:'no-store',...options});let data;
 try{data=await response.json()}catch(_){throw Error(response.status===401?'TAK Map session expired.':'The server returned an invalid response (HTTP '+response.status+').')}
 if(!response.ok||!data||data.ok===false)throw Error(data?.error||'HTTP '+response.status);
 return data}
async function show(){if(open)return;createModal();previousFocus=d.activeElement;open=true;$('takGatewayConfigModalI645').hidden=false;
 status('Loading current Gateway Data settings…');busyState(true);$('gwcHostI645').focus();
 let loaded=false;try{const settings=await request(BASE);loaded=true;
 $('gwcHostI645').value=settings.host||'';$('gwcProtocolI645').value=settings.protocol==='https'?'https':'http';
 $('gwcPortI645').value=settings.port||($('gwcProtocolI645').value==='https'?9443:8090);
 $('gwcAuthI645').value=['none','auto','certificate'].includes(settings.auth_mode)?settings.auth_mode:'none';
 $('gwcVerifyI645').checked=settings.verify_tls!==false;
 $('gwcCaI645').value=settings.ca_cert_path||'';$('gwcCertI645').value=settings.client_cert_path||'';$('gwcKeyI645').value=settings.client_key_path||'';
 refreshChoices();status(settings.configuration_error||'Current Gateway Data URL: '+(settings.api_url||'(not set)'),settings.configuration_error?'error':'');
 }catch(error){status(error.message||String(error),'error')}
 finally{busyState(false);if(!loaded){$('gwcTestI645').disabled=true;$('gwcSaveI645').disabled=true}}}
function hide(){if(!open||busy)return;open=false;$('takGatewayConfigModalI645').hidden=true;previousFocus?.focus?.()}
async function submit(test){if(busy)return;const input=form();if(!input.host){status('Enter a Gateway hostname or IP address.','error');$('gwcHostI645').focus();return}
 if(input.protocol==='http'&&input.auth_mode!=='none'){status('HTTP requires No client certificate.','error');return}
 busyState(true);status(test?'Testing Gateway Data health and capabilities…':'Saving Gateway Data settings…');
 try{const result=await request(BASE+(test?'/test':''),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(input)});
  if(test){status(result.message||'Gateway connection succeeded.','success')}else{status('Settings saved. Reloading TAK Map to start a fresh Gateway Data snapshot…','success');w.location.reload()}
 }catch(error){status(error.message||String(error),'error')}finally{busyState(false)}}
function init(){styles();button();if(!d.body)return;
 const sidebar=$('sidebar')||d.body;
 if(!sidebar.__takGatewayConfigObservedI645){sidebar.__takGatewayConfigObservedI645=true;
 const observer=new MutationObserver(()=>{if(!$('gatewayConfigButtonI645'))button()});
 observer.observe(sidebar,{subtree:true,childList:true})}
}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',init,{once:true});else init();
[600,1800,4000].forEach(ms=>setTimeout(init,ms));
w.TakMapGatewayConfigI645=Object.freeze({version:V,open:show,diagnostics:()=>({buttonPresent:!!$('gatewayConfigButtonI645'),modalPresent:!!$('takGatewayConfigModalI645'),open,busy})});
})(window,document);
