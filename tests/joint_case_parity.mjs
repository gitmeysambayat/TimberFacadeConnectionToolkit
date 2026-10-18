/* Compare the browser case with exported Python vectors. This is numerical
 * parity, not independent source verification or physical validation. */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const prefix=process.env.TFK_OUTPUT_PREFIX||'20261018_v5_';
if(!/^[0-9]{8}_v[1-9][0-9]*_$/.test(prefix))throw Error('Invalid output prefix');
for(const name of ['connections.js','materials_fire_racking.js','joint_case.mjs'])
 vm.runInThisContext(fs.readFileSync(path.join(root,'web',name),'utf8'),{filename:name});
const vectors=JSON.parse(fs.readFileSync(path.join(root,prefix+'JointCaseParityVectors.json'),'utf8'));
const failures=[];
let numbers=0,classifications=0,errors=0,maxRelative=0;
const prose=/(^|\.)(source|source_url|source_ids|clause|warnings|unresolved_checks)(\.|\[|$)/;
function compare(expected,actual,where){
 if(prose.test(where))return;
 if(typeof expected==='number'){
  numbers++;if(typeof actual!=='number'||!Number.isFinite(actual)){failures.push(where+': finite number missing');return;}
  const delta=Math.abs(expected-actual),rel=delta/Math.max(Math.abs(expected),1e-12);maxRelative=Math.max(maxRelative,rel);
  if(delta>Math.max(1e-8,1e-10*Math.abs(expected)))failures.push(where+`: ${expected} != ${actual}`);
 }else if(expected===null){if(actual!==null)failures.push(where+': null mismatch');}
 else if(Array.isArray(expected)){
  if(!Array.isArray(actual)||actual.length!==expected.length){failures.push(where+': array mismatch');return;}
  expected.forEach((v,i)=>compare(v,actual[i],where+'['+i+']'));
 }else if(typeof expected==='object'){
  if(!actual||typeof actual!=='object'){failures.push(where+': object missing');return;}
  for(const[k,v]of Object.entries(expected))compare(v,actual[k],where+'.'+k);
 }else{classifications++;if(expected!==actual)failures.push(where+`: ${expected} != ${actual}`);}
}
for(const[i,v]of vectors.entries()){
 try{const actual=globalThis.TFKJointCase.evaluate(v.inputs);if(v.expectedError)failures.push('case'+i+': expected rejection');else compare(v.expected,actual,'case'+i);}
 catch(error){if(v.expectedError)errors++;else failures.push('case'+i+': '+error.message);}
}
const result={status:failures.length?'FAIL':'PASS',vectors:vectors.length,numeric_comparisons:numbers,
 classification_comparisons:classifications,expected_rejections:errors,max_relative_difference:maxRelative,
 relative_tolerance:1e-10,absolute_tolerance:1e-8,failures,
 scope:'Python/browser numerical parity only; separate from direct-source-equation tests and physical validation.'};
fs.writeFileSync(path.join(root,prefix+'JointCaseParityResults.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
if(failures.length)process.exitCode=1;
