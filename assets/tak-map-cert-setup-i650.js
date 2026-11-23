/* TAK Map HTTPS certificate setup: visible account-header control, safe CA download, explicit admin regeneration. */
(function(window,document){
'use strict';
const ID='takMapCertSetupBtnI650',MODAL='takMapCertModalI650';
const by=id=>document.getElementById(id);
const text=v=>String(v==null?'':v);
const escapeHtml=s=>text(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let pending=false,previousFocus=null;
function css(){if(by('takMapCertStyleI650'))return;const style=document.createElement('style');style.id='takMapCertStyleI650';style.textContent=`
#${ID}{display:inline-flex!important;align-items:center;justify-content:center;min-height:34px;padding:7px 12px;border:1px solid rgba(255,255,255,.21);border-radius:9px;background:#18232c;color:#eef5f9;font-weight:800;font-size:.76rem;white-space:nowrap;cursor:pointer}
#${ID}:focus-visible{outline:2px solid #ff6f2e;outline-offset:2px}
#${MODAL}{display:none;position:fixed;inset:0;z-index:12000;background:rgba(0,0,0,.72);align-items:center;justify-content:center;padding:14px}
#${MODAL}.open{display:flex}
#${MODAL} .cert-i650-dialog{width:min(610px,100%);max-height:calc(100vh - 28px);overflow:auto;box-sizing:border-box;border:1px solid #405364;border-radius:14px;background:#101d27;color:#e8f2f6;box-shadow:0 22px 65px rgba(0,0,0,.55);padding:16px}
#${MODAL} .cert-i650-head{display:flex;justify-content:space-between;align-items:center;gap:12px;border-bottom:1px solid #30404d;padding-bottom:10px}
#${MODAL} h2{margin:0;font-size:1.03rem}#${MODAL} p{color:#b7c6cf;font-size:.82rem;line-height:1.5}
#${MODAL} .cert-i650-lines{margin:10px 0;padding:10px;border:1px solid #334655;border-radius:9px;background:#0b1720;font-size:.78rem;line-height:1.6;overflow-wrap:anywhere}
#${MODAL} .cert-i650-status{color:#b7c6cf;margin:9px 0;font-size:.79rem;white-space:pre-wrap;overflow-wrap:anywhere}
#${MODAL} .cert-i650-buttons{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin:12px 0}
#${MODAL} button,#${MODAL} .cert-i650-download{display:inline-flex;align-items:center;justify-content:center;min-height:33px;box-sizing:border-box;border:1px solid #546b7c;border-radius:9px;padding:6px 12px;background:#223440;color:#edf5f8;font-size:.79rem;text-decoration:none;cursor:pointer}
#${MODAL} .cert-i650-download{background:#234034;border-color:#468764}#${MODAL} button:disabled,#${MODAL} .cert-i650-download.disabled{opacity:.42;pointer-events:none}
#${MODAL} details{margin:12px 0;border-top:1px solid #314351;padding-top:12px}#${MODAL} summary{cursor:pointer;font-weight:800;font-size:.83rem}
#${MODAL} label{display:block;margin:8px 0;font-size:.8rem;color:#bdccd4}
#${MODAL} textarea,#${MODAL} input{box-sizing:border-box;display:block;width:100%;margin:5px 0;background:#08121a;color:#ecf6fa;border:1px solid #435d6e;border-radius:7px;padding:8px;font:inherit}
#${MODAL} .cert-i650-error{color:#ffaca4}
`;document.head.appendChild(style)}
function ensure(){
 css();const top=document.querySelector('.top-actions');
 if(top&&!by(ID)){
  const b=document.createElement('button');b.type='button';b.id=ID;b.textContent='Cert Setup';b.setAttribute('aria-haspopup','dialog');b.addEventListener('click',open);
  const account=top.querySelector('#takAccountV511,.tak-account-v511');top.insertBefore(b,account||top.firstChild);
 }
 if(by(MODAL))return;
 const backdrop=document.createElement('div');backdrop.id=MODAL;backdrop.setAttribute('aria-hidden','true');
 backdrop.innerHTML=`<section class="cert-i650-dialog" role="dialog" aria-modal="true" aria-labelledby="certTitleI650">
 <div class="cert-i650-head"><h2 id="certTitleI650">HTTPS Certificate Setup</h2><button type="button" id="certCloseI650" aria-label="Close certificate setup">Close</button></div>
 <p>Trust the TAK Map HTTPS certificate on this computer by downloading and verifying the local CA certificate. This does not change TAK Gateway's client-certificate settings.</p>
 <div id="certInfoI650" class="cert-i650-lines">Checking certificate status…</div>
 <div class="cert-i650-buttons"><a id="certDownloadI650" class="cert-i650-download disabled" href="/ca-cert.crt" download="tak-local-ca.crt" aria-disabled="true">Download CA Certificate</a><button type="button" id="certRefreshI650">Refresh Status</button></div>
 <p>Before trusting a root CA on Windows, compare its SHA-256 certificate fingerprint with the one reported on your TAK Map server. Import it into <strong>Trusted Root Certification Authorities</strong> only after verification.</p>
 <details id="certAdvancedI650" hidden><summary>Advanced — Generate / Regenerate Certificate</summary>
 <p>Only generate a new certificate if necessary. Regenerating the CA can invalidate trust on previously configured clients. This action may briefly interrupt HTTPS.</p>
 <label>Additional DNS names or IP addresses (one per line)<textarea id="certSansI650" rows="3" placeholder="takmap.local"></textarea></label>
 <label>Type <strong id="certPhraseLabelI650">REGENERATE</strong> to confirm<input type="text" id="certPhraseI650" spellcheck="false" autocomplete="off"></label>
 <button type="button" id="certGenerateI650" disabled>Generate / Regenerate Certificate</button>
 </details><div class="cert-i650-status" id="certStatusI650" aria-live="polite"></div>
 </section>`;
 document.body.appendChild(backdrop);
 backdrop.addEventListener('click',e=>{if(e.target===backdrop&&!pending)close()});
 by('certCloseI650').addEventListener('click',close);
 by('certRefreshI650').addEventListener('click',refresh);
 by('certPhraseI650').addEventListener('input',()=>{const expected=by('certPhraseLabelI650').textContent;by('certGenerateI650').disabled=pending||by('certPhraseI650').value.trim()!==expected});
 by('certGenerateI650').addEventListener('click',generate);
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&by(MODAL)?.classList.contains('open')&&!pending)close()});
}
function setStatus(value,isError){const el=by('certStatusI650');if(!el)return;el.textContent=text(value);el.classList.toggle('cert-i650-error',!!isError)}
function open(){ensure();previousFocus=document.activeElement;const modal=by(MODAL);modal.classList.add('open');modal.setAttribute('aria-hidden','false');by('certCloseI650').focus();refresh()}
function close(){if(pending)return;const modal=by(MODAL);if(!modal)return;modal.classList.remove('open');modal.setAttribute('aria-hidden','true');by('certAdvancedI650').open=false;by('certPhraseI650').value='';if(previousFocus&&typeof previousFocus.focus==='function')previousFocus.focus()}
async function refresh(){
 ensure();setStatus('Checking HTTPS certificate status…',false);
 const link=by('certDownloadI650');link.classList.add('disabled');link.setAttribute('aria-disabled','true');
 try{
  const r=await fetch('/api/tak-map/cert-setup/status',{credentials:'same-origin',cache:'no-store',headers:{'Accept':'application/json'}});
  const j=await r.json();if(!r.ok||!j.ok)throw new Error(j.error||('HTTP '+r.status));
  const expiry=j.cert_expiration||{},ca=expiry.dashboard_ca||{},server=expiry.dashboard_server||{};
  const info=[['CA certificate',j.ca_exists?'Installed':'Not generated'],['Server certificate',j.server_cert_exists?'Installed':'Not generated'],['CA SHA-256 fingerprint',j.ca_fingerprint_sha256||'Unavailable'],['Server certificate expiry',server.not_after||server.expires||server.message||server.status||'See certificate details'],['CA certificate expiry',ca.not_after||ca.expires||ca.message||ca.status||'See certificate details'],['Configured IP addresses',(j.ips||[]).join(', ')||'Not detected']];
  by('certInfoI650').innerHTML=info.map(([k,v])=>'<div><b>'+escapeHtml(k)+':</b> '+escapeHtml(v)+'</div>').join('');
  if(j.ca_exists&&j.ca_download_url){link.href='/ca-cert.crt';link.classList.remove('disabled');link.removeAttribute('aria-disabled');}
  by('certAdvancedI650').hidden=!j.is_admin;
  const phrase=j.ca_exists?'REGENERATE':'GENERATE';by('certPhraseLabelI650').textContent=phrase;by('certPhraseI650').value='';by('certGenerateI650').disabled=true;
  setStatus(j.ca_exists?'Existing CA available. Download it without regenerating certificates.':'No local CA certificate found. An administrator can generate one below.',false);
 }catch(e){by('certInfoI650').textContent='Unable to load certificate status.';by('certAdvancedI650').hidden=true;setStatus(e.message||String(e),true)}
}
async function generate(){
 const phrase=by('certPhraseLabelI650').textContent;if(pending||by('certPhraseI650').value.trim()!==phrase)return;
 if(!window.confirm('This operation may replace the TAK Map HTTPS certificate and potentially the trusted CA. Continue?'))return;
 pending=true;by('certGenerateI650').disabled=true;setStatus('Certificate operation running…',false);
 try{
  const r=await fetch('/api/tak-map/cert-setup/generate',{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify({confirmation:phrase,extra_sans:by('certSansI650').value})});
  const j=await r.json();if(!r.ok||!j.ok)throw new Error(j.error||j.stderr||('HTTP '+r.status));
  setStatus('Certificate operation completed. HTTPS may require reconnecting. Refresh this page if necessary.',false);
 }catch(e){setStatus('Certificate operation failed: '+(e.message||String(e)),true)}finally{pending=false;by('certGenerateI650').disabled=true}
}
window.TakMapCertSetupI650=Object.freeze({open,close,refresh});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ensure,{once:true});else ensure();
window.addEventListener('takmap:runtime-ready-i553',ensure,{once:true});
})(window,document);
