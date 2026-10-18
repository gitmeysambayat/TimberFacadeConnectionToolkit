/* Page-wiring unit checks using a DOM stub, not browser rendering or UI QA. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..');
const prefix=process.env.TFK_OUTPUT_PREFIX||'20261018_v5_';
if(!/^\d{8}_v[1-9]\d*_$/.test(prefix))throw Error('Invalid release prefix');
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
const page=fs.readFileSync(path.join(root,prefix+'TimberJointCase.html'),'utf8');
const scripts=[...page.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(x=>x[1]);
vm.runInContext(scripts.at(-1),context,{filename:'joint-case-page-inline.js'});
const result=()=>JSON.parse(elements.json.textContent);
let checks=0;
function check(name,fn){fn();checks++;console.log('PASS '+name);}
function input(key,value){elements['input-'+key].events.input({target:{value:String(value)}});}
check('initial result and source-backed creep values',()=>{assert(Math.abs(result().design_capacity.group_design_capacity_N-10026.1225)<.01);assert(elements['scenario-result'].innerHTML.includes('1.198 mm'));assert(elements['baseline-result'].innerHTML.includes('class="ok"'));});
check('diameter changes hole and exposes incompatible fixed detailing',()=>{input('diameter_mm',16);assert.equal(result().inputs.hole_diameter_mm,17);assert.equal(result().geometry.status,'FAIL');assert(elements['scenario-result'].innerHTML.includes('class="fail"'));});
check('reset restores reference',()=>{elements.reset.click();assert.equal(result().inputs.diameter_mm,12);assert.equal(result().geometry.status,'PASS_IN_SCOPE');});
check('permanent-only governing result is displayed with kN input conversion',()=>{input('Gk_N',6);input('Qk_N',0);assert.equal(result().inputs.Gk_N,6000);assert.equal(result().load_duration_checks.governing_case,'permanent_only');assert(elements['scenario-result'].innerHTML.includes('8.100 kN'));assert(elements['scenario-result'].innerHTML.includes('7.520 kN'));assert(result().failed_component_checks.length>0);});
check('free play is added once and exposes chosen-budget exceedance',()=>{elements.reset.click();input('additional_freeplay_mm',1.5);assert(Math.abs(result().slip.final_total_mm-2.69799479)<1e-7);assert(elements['scenario-result'].innerHTML.includes('Exceeds chosen study budget'));});
check('download contains current scenario and result',()=>{elements.download.click();const exported=JSON.parse(download.blob.data.join(''));assert.equal(exported.inputs.additional_freeplay_mm,1.5);assert.equal(download.name,prefix+'TimberJointScenario.json');});
check('blank input hides stale results and disables download',()=>{input('diameter_mm','');assert(elements['scenario-result'].hidden);assert(!elements.error.hidden);assert(elements.download.disabled);assert(elements.json.textContent.includes('Invalid scenario'));});
check('reset recovers from invalid input',()=>{elements.reset.click();assert(!elements['scenario-result'].hidden);assert(elements.error.hidden);assert(!elements.download.disabled);assert.equal(result().inputs.diameter_mm,12);});
check('negative free play is rejected',()=>{input('additional_freeplay_mm',-1);assert(elements['scenario-result'].hidden);assert(elements.download.disabled);});
check('sensitivity rows and reference record are present',()=>{assert(elements.sensitivity.innerHTML.includes('Diameter 16 mm'));assert(elements.sensitivity.innerHTML.includes('Outer thickness 35 mm'));assert(elements['baseline-result'].innerHTML.includes('10.026 kN'));});
check('M14 fixed-washer comparison fails washer minima but meets loaded-end distances',()=>{const m14=vm.runInContext('diameterPoints.find(p=>p.value===14).result',context);assert.equal(m14.inputs.washer_diameter_mm,40);assert.equal(m14.inputs.washer_thickness_mm,4);assert.equal(m14.geometry.checks.washer_diameter.status,'FAIL');assert.equal(m14.geometry.checks.washer_thickness.status,'FAIL');assert.equal(m14.geometry.checks.left_loaded_end.status,'PASS');assert.equal(m14.geometry.checks.right_loaded_end.status,'PASS');assert(elements.sensitivity.innerHTML.includes('Diameter 14 mm'));assert(elements.sensitivity.innerHTML.includes('reference Ø40 × 4 mm washers remain fixed'));});
check('force, movement and controlled sensitivity SVG charts have descriptions',()=>{assert(elements['scenario-result'].innerHTML.includes('id="scenario-force-desc"'));assert(elements['scenario-result'].innerHTML.includes('id="scenario-movement-desc"'));assert(elements.sensitivity.innerHTML.includes('id="diameter-sweep-desc"'));assert(elements.sensitivity.innerHTML.includes('excluded because detailing checks fail'));});
check('headline utilisation includes net tension when it governs',()=>{elements.reset.click();input('width_mm',17);const r=result(),maximum=r.load_duration_checks.combined.net_tension_utilisation;assert(maximum>r.design_capacity.utilisation);assert(elements['scenario-result'].innerHTML.includes(maximum.toFixed(3)));assert(elements['scenario-result'].innerHTML.includes('Net-section tension</small>'));});
function preset(value){elements.preset.events.change({target:{value}});}
check('thinner outer-member comparison updates numeric input and result',()=>{preset('thin');assert.equal(result().inputs.side_thickness_mm,35);assert.equal(elements['input-side_thickness_mm'].value,35);});
check('larger-bolt preset retains fixed washers and shows conflict',()=>{preset('large');assert.equal(result().inputs.diameter_mm,16);assert.equal(result().inputs.washer_diameter_mm,40);assert.equal(result().geometry.status,'FAIL');});
check('free-play comparison produces expected final movement',()=>{preset('play');assert.equal(result().inputs.additional_freeplay_mm,1.5);assert(Math.abs(result().slip.final_total_mm-2.6979947919310665)<1e-10);});
check('movement budget and quasi-permanent factor update API values',()=>{elements.reset.click();input('study_slip_budget_mm',1);assert(elements['scenario-result'].innerHTML.includes('Exceeds chosen study budget'));input('psi2',1);assert.equal(result().inputs.psi2,1);assert(result().slip.final_total_mm>1.4);});
check('invalid psi2, zero budget and impossible overlap reject current result',()=>{input('psi2',1.01);assert(elements.download.disabled);elements.reset.click();input('study_slip_budget_mm',0);assert(elements.download.disabled);elements.reset.click();input('overlap_mm',100);assert(elements.download.disabled);});
check('geometry controls can repair larger-bolt detailing conflicts',()=>{preset('large');input('end_distance_mm',120);input('overlap_mm',240);input('washer_diameter_mm',48);input('washer_thickness_mm',4.8);assert.equal(result().geometry.status,'PASS_IN_SCOPE');});
check('fixed reference result remains unchanged after edits',()=>{assert(elements['baseline-result'].innerHTML.includes('10.026 kN'));assert(elements['baseline-result'].innerHTML.includes('1.198 mm'));assert(!elements['baseline-result'].innerHTML.includes('8.100 kN'));});
check('public interface preserves essential scope and removes private coaching',()=>{assert(page.includes('Overall connection design and physical validation remain unresolved'));assert(!page.includes('Personal learning record'));assert(!page.includes('interview evidence'));assert(elements['scenario-result'].innerHTML.includes('All unresolved checks for this result'));assert(!elements['scenario-result'].innerHTML.includes('NO_FAILURE_IN_CHECKED_COMPONENTS'));});
check('all 13 controls have labels, bindings and human-readable errors',()=>{const fields=elements.fields.innerHTML+elements['advanced-fields'].innerHTML;for(const key of ['diameter_mm','side_thickness_mm','end_distance_mm','Gk_N','Qk_N','additional_freeplay_mm','centre_thickness_mm','width_mm','overlap_mm','washer_diameter_mm','washer_thickness_mm','study_slip_budget_mm','psi2']){assert(elements['input-'+key].events.input);assert(fields.includes('for="input-'+key+'"'));assert(fields.includes('id="input-'+key+'"'));}input('additional_freeplay_mm',-1);assert(!elements.error.innerHTML.includes('additional_freeplay_mm'));assert(elements.error.innerHTML.includes('Additional total free play'));});
const record={status:'PASS',checks,method:'Node VM with DOM stub; excludes real-browser layout, focus, KaTeX rendering and console checks',browser_preview:'NOT_ASSESSED_BY_DOM_STUB',page:prefix+'TimberJointCase.html'};
fs.writeFileSync(path.join(root,prefix+'JointCasePageChecks.json'),JSON.stringify(record,null,2)+'\n');
console.log(JSON.stringify(record));
