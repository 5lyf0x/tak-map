const fs=require('fs');const vm=require('vm');
const src=fs.readFileSync(process.argv[2]||'assets/tak-map-core-i553.js','utf8');
if(!src.includes('nonfatal_source_error_i590'))throw new Error('i590 tolerant parser missing');
if(!src.includes('tak-data-sync-warning-i590'))throw new Error('i590 card warning renderer missing');
if(!src.includes('last_known_good_preserved'))throw new Error('i590 last-known-good refresh preservation missing');
const start=src.indexOf('async function apiJsonResponse(r)');const end=src.indexOf('async function apiJsonResponseAllowFalse',start);const code=src.slice(start,end);
const context={Response,console};vm.createContext(context);vm.runInContext(code+';globalThis.f=apiJsonResponse;',context);
(async()=>{
  const partial=new Response(JSON.stringify({ok:false,error:'optional source unavailable',missions:[{name:'M'}],objects:[{uid:'U'}],mission_content:[],mission_uids:[]}),{status:200,headers:{'Content-Type':'application/json'}});
  const j=await context.f(partial);if(!j.ok||!j.partial||j.objects.length!==1)throw new Error('usable partial snapshot was rejected');
  let rejected=false;
  try{await context.f(new Response(JSON.stringify({ok:false,error:'authentication failed',missions:[],objects:[],mission_content:[],mission_uids:[]}),{status:200,headers:{'Content-Type':'application/json'}}));}catch(e){rejected=/authentication failed/.test(String(e));}
  if(!rejected)throw new Error('empty fatal snapshot was incorrectly accepted');
  console.log(JSON.stringify({ok:true,partial:j.partial,warnings:j.warnings,fatalEmptyRejected:true,lastKnownGoodPreserved:true}));
})().catch(e=>{console.error(e);process.exit(1)});
