/* Page-wiring unit checks using a DOM stub, not browser rendering or UI QA. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..');
class Element{
 constructor(id){this.id=id;this.innerHTML='';this.textContent='';this.value='';this.hidden=false;this.disabled=false;this.events={};}
 addEventListener(type,fn){this.events[type]=fn;}
 click(){if(this.events.click)this.events.click();}
}
const elements={};let download=null;
const document={getElementById(id){return elements[id]??=(new Element(id));},querySelectorAll(){return [];},createElement(){const e=new Element('download');e.click=()=>{download={name:e.download,blob:lastBlob};};return e;}};
let lastBlob;
class BlobStub{constructor(data,options){this.data=data;this.options=options;lastBlob=this;}}
const context=vm.createContext({document,structuredClone,console,Blob:BlobStub,URL:{createObjectURL(){return 'blob:unit-test';},revokeObjectURL(){}},setTimeout(fn){fn();},katex:{render(){}}});
for(const n of ['connections.js','materials_fire_racking.js','joint_case.mjs'])vm.runInContext(fs.readFileSync(path.join(root,'web',n),'utf8'),context,{filename:n});
const page=fs.readFileSync(path.join(root,'20261018_v4_TimberJointCase.html'),'utf8');
const scripts=[...page.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(x=>x[1]);
vm.runInContext(scripts.at(-1),context,{filename:'joint-case-page-inline.js'});
const result=()=>JSON.parse(elements.json.textContent);
let checks=0;
function check(name,fn){fn();checks++;console.log('PASS '+name);}
function input(key,value){elements['input-'+key].events.input({target:{value:String(value)}});}
check('initial result and source-backed creep values',()=>{assert(Math.abs(result().design_capacity.group_design_capacity_N-10026.1225)<.01);assert(elements['scenario-result'].innerHTML.includes('1.198 mm'));assert(elements['baseline-result'].innerHTML.includes('class="ok"'));});
check('diameter changes hole and exposes incompatible fixed detailing',()=>{input('diameter_mm',16);assert.equal(result().inputs.hole_diameter_mm,17);assert.equal(result().geometry.status,'FAIL');assert(elements['scenario-result'].innerHTML.includes('class="fail"'));});
check('reset restores reference',()=>{elements.reset.click();assert.equal(result().inputs.diameter_mm,12);assert.equal(result().geometry.status,'PASS_IN_SCOPE');});
check('permanent-only governing result is displayed',()=>{input('Gk_N',6000);input('Qk_N',0);assert.equal(result().load_duration_checks.governing_case,'permanent_only');assert(elements['scenario-result'].innerHTML.includes('8.100 kN'));assert(elements['scenario-result'].innerHTML.includes('7.520 kN'));assert(result().failed_component_checks.length>0);});
check('free play is added once and exposes chosen-budget exceedance',()=>{elements.reset.click();input('additional_freeplay_mm',1.5);assert(Math.abs(result().slip.final_total_mm-2.69799479)<1e-7);assert(elements['scenario-result'].innerHTML.includes('Exceeds chosen study budget'));});
check('download contains current scenario and result',()=>{elements.download.click();const exported=JSON.parse(download.blob.data.join(''));assert.equal(exported.inputs.additional_freeplay_mm,1.5);assert.equal(download.name,'20261018_v4_TimberJointScenario.json');});
check('blank input hides stale results and disables download',()=>{input('diameter_mm','');assert(elements['scenario-result'].hidden);assert(!elements.error.hidden);assert(elements.download.disabled);assert(elements.json.textContent.includes('Invalid scenario'));});
check('reset recovers from invalid input',()=>{elements.reset.click();assert(!elements['scenario-result'].hidden);assert(elements.error.hidden);assert(!elements.download.disabled);assert.equal(result().inputs.diameter_mm,12);});
check('negative free play is rejected',()=>{input('additional_freeplay_mm',-1);assert(elements['scenario-result'].hidden);assert(elements.download.disabled);});
check('sensitivity rows and reference record are present',()=>{assert(elements.sensitivity.innerHTML.includes('Diameter 16 mm'));assert(elements.sensitivity.innerHTML.includes('Outer thickness 35 mm'));assert(elements['baseline-result'].innerHTML.includes('10.026 kN'));});
const record={status:'PASS',checks,method:'Node VM with DOM stub; excludes real-browser layout, focus, KaTeX rendering and console checks',browser_preview:'NOT_COMPLETED_LOCAL_FILE_URL_BLOCKED',page:'20261018_v4_TimberJointCase.html'};
fs.writeFileSync(path.join(root,'20261018_v4_JointCasePageChecks.json'),JSON.stringify(record,null,2)+'\n');
console.log(JSON.stringify(record));
