/* Node is used only to compare the browser modules with exported Python values. */
'use strict';
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..');
const prefix=process.env.TFK_OUTPUT_PREFIX || '20261018_v3_';
if(!/^[0-9]{8}_v[1-9][0-9]*_$/.test(prefix))throw new Error('Invalid TFK_OUTPUT_PREFIX');
new (require('vm').Script)(fs.readFileSync(path.join(root,'web','toolkit.js'),'utf8'),{filename:'web/toolkit.js'});
for(const name of ['connections.js','seismic.js','materials_fire_racking.js'])require(path.join(root,'web',name));
const modules={connections:globalThis.TFKConnections,seismic:globalThis.TFKSeismic,
  materials:globalThis.TFKMaterials,fire:globalThis.TFKFire,racking:globalThis.TFKRacking};
const vectors=JSON.parse(fs.readFileSync(path.join(root,prefix+'ParityVectors.json'),'utf8'));
const failures=[];let numbers=0,booleans=0,strings=0,maxRelative=0;
const ignoreProse=/(^|\.)(source|source_url|source_ids|clause|warnings|limitations|orientation|assumption|angle_convention|gamma_status)(\.|\[|$)/;
function compare(a,b,where){
  if(ignoreProse.test(where))return;
  if(typeof a==='number'){
    numbers++;if(typeof b!=='number'||!Number.isFinite(b)){failures.push(where+': non-finite/non-numeric browser result');return;}
    const delta=Math.abs(a-b),rel=delta/Math.max(Math.abs(a),1e-12);maxRelative=Math.max(maxRelative,rel);
    if(delta>Math.max(1e-9,0.001*Math.abs(a)))failures.push(where+`: Python ${a}, JavaScript ${b}`);
  }else if(a===null){if(b!==null)failures.push(where+': null mismatch');}
  else if(typeof a==='boolean'){booleans++;if(a!==b)failures.push(where+': Boolean mismatch');}
  else if(typeof a==='string'){strings++;if(a!==b)failures.push(where+`: classification mismatch ${a} / ${b}`);}
  else if(Array.isArray(a)){
    if(!Array.isArray(b)||a.length!==b.length){failures.push(where+': array length/type mismatch');return;}
    a.forEach((v,i)=>compare(v,b[i],where+'['+i+']'));
  }else{
    if(!b||typeof b!=='object'){failures.push(where+': object missing');return;}
    for(const key of Object.keys(a))compare(a[key],b[key],where+'.'+key);
  }
}
for(const [i,v] of vectors.entries()){
  try{const actual=modules[v.module].evaluate(v.operation,v.inputs);if(v.expectedError)failures.push('case'+i+': expected rejection');else compare(v.expected,actual,'case'+i);}
  catch(e){if(!v.expectedError)failures.push('case'+i+': '+e.message);}
}
const summary={status:failures.length?'FAIL':'PASS',vectors:vectors.length,numeric_comparisons:numbers,
  Boolean_comparisons:booleans,classification_comparisons:strings,relative_tolerance:0.001,
  absolute_tolerance:1e-9,max_relative_difference:maxRelative,failures,
  scope:'Numerical implementation parity only, separate from source and hand/worked-example checks.'};
fs.writeFileSync(path.join(root,prefix+'ParityResults.json'),JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify(summary,null,2));if(failures.length)process.exit(1);
