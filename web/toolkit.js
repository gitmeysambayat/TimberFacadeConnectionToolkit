/* Local educational interface. No network, telemetry or external write calls. */
(function(){
'use strict';
const baseline=JSON.parse(document.getElementById('case-data').textContent);
const vectors=JSON.parse(document.getElementById('fixture-data').textContent);
let caseData=structuredClone(baseline), latest=null;
const $=id=>document.getElementById(id),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=(v,n=3)=>v===null||v===undefined?'Required / not evaluated':Number(v).toLocaleString('en-GB',{maximumFractionDigits:n});
const get=(obj,key)=>key.split('.').reduce((v,k)=>v[k],obj);
function set(obj,key,val){const parts=key.split('.');const end=parts.pop();parts.reduce((v,k)=>v[k],obj)[end]=val;}
function cInputs(c){return {rho_k:c.rho_k_kg_m3,rho_m:c.rho_mean_kg_m3,d:c.diameter_mm,fu_k:c.fu_MPa,t1:c.timber_thickness_mm,t_steel:c.steel_plate_thickness_mm,n:c.number_in_row,a1:c.spacing_parallel_mm,kmod:c.kmod,gamma_M:c.gamma_M,alpha_deg:c.load_angle_deg,Fax_Rk:c.Fax_Rk_N,fastener:c.fastener_type,steel_factor:c.steel_slip_factor,hole_tolerance_mm:c.hole_tolerance_mm??null,spacing_actual:{a1:c.spacing_parallel_mm,a2:c.spacing_perpendicular_mm,a3_t:c.loaded_end_mm,a3_c:c.unloaded_end_mm,a4_t:c.loaded_edge_mm,a4_c:c.unloaded_edge_mm},design_shear_N:c.design_shear_demand_N,anchor_capacity_N:c.anchor_design_capacity_N};}
function sInputs(c){const s=c.seismic,p=c.panel;return{alpha:s.alpha,soil_factor:s.soil_factor,z_m:s.element_height_m,H_m:s.building_height_m,Ta_s:s.element_period_s,T1_s:s.fundamental_period_s,height_mm:p.height_mm,width_mm:p.width_mm,self_weight_kN_m2:p.self_weight_kN_m2,gamma_a:s.gamma_a,q_a:s.q_a,dr_mm:s.design_interstorey_drift_mm,storey_height_mm:s.storey_height_mm,nu:s.nu,category:s.element_category==='brittle'?'brittle_attached':s.element_category,bolt_diameter_mm:s.slot_bolt_diameter_mm,installation_allowance_mm:s.slot_installation_allowance_mm,load_shares:s.bracket_load_shares};}
function calculate(c){
 const con=TFKConnections.evaluate('connection_summary',cInputs(c.connection));
 if(typeof c.connection.anchor_ETA_reference!=='string'||!c.connection.anchor_ETA_reference.trim()){con.missing_inputs.push('anchor_ETA_reference');if(con.status==='PASS_IN_SCOPE')con.status='UNVERIFIED';}
 const seis=TFKSeismic.evaluate('case_summary',sInputs(c));
 seis.slot=TFKSeismic.evaluate('slot_length_mm',{dr_mm:c.seismic.design_interstorey_drift_mm,bolt_diameter_mm:c.seismic.slot_bolt_diameter_mm,installation_allowance_mm:c.seismic.slot_installation_allowance_mm,centred:c.seismic.slot_centred,movement_factor:c.seismic.slot_movement_factor});
 const fire=c.fire.times_min.map(t=>{const section=TFKFire.evaluate('section',{...c.fire,time_min:t});return{section,bending:TFKFire.evaluate('bending',{...c.fire,section})};});
 return{connection:con,seismic:seis,fire,racking:TFKRacking.evaluate('panel',c.racking)};
}
const fieldGroups=[
 ['Connection and material',[
 ['connection.diameter_mm','Bolt diameter (mm)',.1],['connection.steel_plate_thickness_mm','Steel plate thickness (mm)',.1],['connection.timber_thickness_mm','Timber penetration (mm)',1],['connection.rho_k_kg_m3','Characteristic density (kg/m³)',1],['connection.rho_mean_kg_m3','Mean density (kg/m³)',1],['connection.fu_MPa','Fastener ultimate strength (MPa)',1],['connection.load_angle_deg','Load-to-grain angle (degrees)',1],['connection.number_in_row','Bolts in the grain-parallel row',1],['connection.spacing_parallel_mm','Spacing along grain (mm)',1],['connection.kmod','Modification factor kmod',.05],['connection.gamma_M','Recommended γM, editable NDP',.05],['connection.Fax_Rk_N','Axial resistance for rope effect (N)',1],['connection.steel_slip_factor','Steel slip multiplier: 1 or 2',1],['connection.hole_tolerance_mm','Bolt-hole tolerance (mm), required for thick-plate fit',.1],['connection.loaded_end_mm','Loaded end distance (mm)',1],['connection.unloaded_end_mm','Unloaded end distance (mm)',1],['connection.loaded_edge_mm','Loaded edge distance (mm)',1],['connection.unloaded_edge_mm','Unloaded edge distance (mm)',1],['connection.spacing_perpendicular_mm','Spacing across grain (mm)',1],['connection.design_shear_demand_N','Project design shear demand (N)',1],['connection.anchor_design_capacity_N','Anchor design resistance from ETA (N)',1]]],
 ['Panel and seismic demand',[
 ['panel.height_mm','Panel height (mm)',1],['panel.width_mm','Panel width (mm)',1],['panel.self_weight_kN_m2','Assumed self-weight (kN/m²)',.01],['panel.characteristic_wind_kN_m2','Assumed characteristic wind pressure (kN/m²)',.1],['seismic.alpha','α = ag/g',.01],['seismic.soil_factor','Soil factor S',.05],['seismic.building_height_m','Building height H (m)',.1],['seismic.element_height_m','Element height z (m)',.1],['seismic.fundamental_period_s','Building period T1 (s)',.01],['seismic.element_period_s','Element period Ta (s)',.01],['seismic.gamma_a','Element importance factor γa',.1],['seismic.q_a','Façade behaviour factor qa, maximum 2',.1],['seismic.nu','Recommended ν, editable NDP',.1],['seismic.storey_height_mm','Storey height h (mm)',1],['seismic.design_interstorey_drift_mm','Assumed design drift dr (mm)',1],['seismic.slot_bolt_diameter_mm','Sliding bolt shank diameter (mm)',.1],['seismic.slot_installation_allowance_mm','Total slot installation allowance (mm)',1]]],
 ['Isolated-member fire study',[
 ['fire.width_mm','Section width (mm)',1],['fire.depth_mm','Section depth (mm)',1],['fire.beta_0_mm_min','One-dimensional charring rate β0 (mm/min)',.01],['fire.beta_n_mm_min','Notional charring rate βn (mm/min)',.01],['fire.kfi','Verified solid-timber kfi',.05],['fire.gamma_M_fi','Recommended γM,fi, editable NDP',.05],['fire.design_bending_moment_Nmm','Fire design moment (N mm), required',1]]],
 ['Racking subcheck',[
 ['racking.fastener_design_resistance_N','Section 8 fastener design resistance (N), required',1],['racking.sheet_width_mm','Sheet width bi (mm)',1],['racking.wall_height_mm','Panel height h (mm)',1],['racking.perimeter_spacing_mm','Perimeter fastener spacing s (mm)',1]]]
];
function controls(){
 $('fields').innerHTML=fieldGroups.map(([title,fields],i)=>`<details ${i===0?'open':''}><summary>${title}</summary><div class="fields">${fields.map(([path,label,step])=>`<label>${label}<input type="number" data-path="${path}" step="${step}" value="${get(caseData,path)??''}" placeholder="Required input"></label>`).join('')}</div></details>`).join('');
 document.querySelectorAll('[data-path]').forEach(el=>el.addEventListener('input',()=>{set(caseData,el.dataset.path,el.value===''?null:Number(el.value));render();}));
 $('category').value=caseData.seismic.element_category;
 $('shares').value=caseData.seismic.bracket_load_shares?.join(', ')??'';
 $('eta-reference').value=caseData.connection.anchor_ETA_reference??'';
 $('face').value=caseData.fire.exposed_faces.join(',');
 for(const key of ['tied_down','no_openings','regular_spacing','sheet_edge_sufficient','sheet_fixings_verified'])$('rack-'+key).value=caseData.racking[key]===null?'unknown':String(caseData.racking[key]);
 $('json').value=JSON.stringify(caseData,null,2);
}
function table(headers,rows){return `<div class="scroll"><table><thead><tr>${headers.map(h=>'<th>'+h+'</th>').join('')}</tr></thead><tbody>${rows.map(row=>'<tr>'+row.map(x=>'<td>'+x+'</td>').join('')+'</tr>').join('')}</tbody></table></div>`;}
function plot(id,series,xlabel,ylabel,title){
 const width=560,height=285,left=65,right=22,top=28,bottom=55;
 const points=series.flatMap(s=>s.points),xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
 const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=0,ymax=Math.max(...ys)*1.12||1;
 const X=x=>left+(x-xmin)/(xmax-xmin||1)*(width-left-right),Y=y=>height-bottom-(y-ymin)/(ymax-ymin)*(height-top-bottom);
 let svg=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(title)}"><rect width="100%" height="100%" fill="white"/>`;
 for(let i=0;i<=4;i++){const y=ymax*i/4,x=xmin+(xmax-xmin)*i/4;svg+=`<path d="M${left} ${Y(y)}H${width-right}" stroke="#e2e8f0"/><text x="${left-8}" y="${Y(y)+4}" text-anchor="end">${fmt(y,2)}</text><text x="${X(x)}" y="${height-bottom+20}" text-anchor="middle">${fmt(x,2)}</text>`;}
 svg+=`<path d="M${left} ${top}V${height-bottom}H${width-right}" fill="none" stroke="#64748b"/>`;
 for(const s of series)svg+=`<polyline points="${s.points.map(p=>X(p[0])+','+Y(p[1])).join(' ')}" fill="none" stroke="${s.colour}" stroke-width="2.5" ${s.dashed?'stroke-dasharray="6 4"':''}/>`;
 svg+=`<text x="${(width+left-right)/2}" y="${height-10}" text-anchor="middle">${esc(xlabel)}</text><text transform="translate(16 ${(height-bottom+top)/2}) rotate(-90)" text-anchor="middle">${esc(ylabel)}</text></svg>`;
 $(id).innerHTML=svg;
}
function render(){
 $('json').value=JSON.stringify(caseData,null,2);
 try{
  latest=calculate(caseData);const c=latest.connection,s=latest.seismic;
  $('error').hidden=true;$('results').hidden=false;
  $('connection-metric').textContent=fmt(c.design.group_design_capacity_N/1000,3)+' kN';
  $('connection-caption').textContent='Calculated group component resistance; '+c.status;
  $('seismic-metric').textContent=fmt(s.Fa_kN,4)+' kN';
  const lastFire=latest.fire.at(-1).section;
  $('fire-metric').textContent=lastFire.status==='SECTION_EXHAUSTED'?'Exhausted':fmt(lastFire.effective_width_mm,1)+' × '+fmt(lastFire.effective_depth_mm,1)+' mm';
  $('modes').innerHTML=table(['Johansen mode','Base (kN)','Rope (kN)','Total (kN)','Governing'],Object.entries(c.modes.modes).map(([name,m])=>[esc(name),fmt(m.johansen_N/1000),fmt(m.rope_N/1000),fmt(m.Fv_Rk_N/1000),name===c.modes.governing_mode?'Yes':'']));
  $('connection-notes').innerHTML=`<p>Plate: <b>${esc(c.modes.plate_class)}</b>. Effective fasteners: <b>${fmt(c.effective_number.n_eff,4)}</b>. Embedment: <b>${fmt(c.embedment.fh_k)} MPa</b>. Yield moment: <b>${fmt(c.yield_moment.My_Rk/1000)} kN mm</b>.</p><p>Slip per fastener, per plane: base K<sub>ser</sub> ${fmt(c.slip.Kser_base_N_per_mm/1000)} kN/mm; selected K<sub>ser</sub> ${fmt(c.slip.Kser_N_per_mm/1000)} kN/mm; K<sub>u</sub> ${fmt(c.slip.Ku_N_per_mm/1000)} kN/mm. Bolt clearance slip is additional.</p><p class="muted">${esc(c.modes.clause)}. Rope is deliberately neglected when the supplied axial resistance is zero.</p><div id="design-equation"></div>`;
  katex.render('F_{v,Rd}=\\frac{k_{\\mathrm{mod}}F_{v,Rk}}{\\gamma_M}',$('design-equation'),{displayMode:true,throwOnError:false});
  $('spacings').innerHTML=table(['Dimension','Minimum (mm)','Supplied (mm)','Check'],Object.entries(c.spacing.checks).map(([name,r])=>[esc(name),fmt(r.required_mm),r.actual_mm===null?'Required':fmt(r.actual_mm),esc(r.status)]));
  const labels={a2:'Bolt-row spacing across grain',a3_t:'Loaded end distance',a3_c:'Unloaded end distance',a4_t:'Loaded edge distance',a4_c:'Unloaded edge distance',design_shear_N:'Project design shear demand','anchor_capacity_N from applicable ETA':'Anchor design resistance from the applicable ETA',anchor_ETA_reference:'Anchor ETA source reference'};
  $('required').innerHTML='<li>'+c.missing_inputs.map(x=>esc(labels[x]||x)).join('</li><li>')+'</li>';
  $('seismic-output').innerHTML=table(['Quantity','Value'],[['Sa',fmt(s.Sa,6)],['Whole-panel weight',fmt(s.weight_kN,6)+' kN'],['Per-bracket demand',s.bracket_forces_kN===null?'Required: justified load shares':s.bracket_forces_kN.map(v=>fmt(v,4)+' kN').join('; ')],['Reduced drift demand dr ν',fmt(s.drift.demand_mm)+' mm'],['Selected RHS limit c h',fmt(s.drift.limit_mm)+' mm'],['Selected inequality',s.drift.passes?'Satisfied in this input subcase':'Not satisfied'],['Unreduced dr limit',fmt(s.drift.dr_limit_mm)+' mm'],['Geometric slot illustration',fmt(s.slot.slot_length_mm)+' mm']]);
  $('fire-output').innerHTML=table(['Time (min)','Notional char (mm)','Effective loss (mm)','Effective width (mm)','Effective depth (mm)','Wᵧ (mm³)','Bending subcheck'],latest.fire.map(r=>[fmt(r.section.time_min),fmt(r.section.dchar_n_mm),fmt(r.section.effective_char_depth_mm),fmt(r.section.effective_width_mm),fmt(r.section.effective_depth_mm),fmt(r.section.W_y_mm3,0),r.section.status==='SECTION_EXHAUSTED'?'Section exhausted':r.bending.passed===null?'Required fire action':r.bending.passed?'Section only: satisfied':'Section only: not satisfied']));
  $('fire-status').textContent=lastFire.status==='SECTION_EXHAUSTED'?'The effective section is exhausted at the last time. The depth plot alone does not describe the remaining section.':'The displayed section dimensions follow the selected faces. These are section calculations, with fire actions and stability checks separate.';
  const r=latest.racking;$('racking-output').innerHTML=table(['Quantity','Value'],[['Width factor ci',fmt(r.width_factor_ci,6)],['Minimum sheet width h/4',fmt(r.minimum_sheet_width_mm)+' mm'],['Applicability',esc(r.status)],['Equation result',r.formula_capacity_N===null?'Required fastener resistance':fmt(r.formula_capacity_N/1000)+' kN'],['Applicable panel subcheck resistance',r.capacity_N===null?'Not established':fmt(r.capacity_N/1000)+' kN']]);
  const rackLabels={tied_down:'end tie-downs',no_openings:'absence of openings',regular_spacing:'constant perimeter spacing',sheet_edge_sufficient:'sheet edge detailing',sheet_fixings_verified:'sheet and fixing verification',fastener_design_resistance_N:'fastener design resistance',sheet_width_below_h_over_4:'sheet width below the permitted minimum'};
  $('rack-required').textContent=[...r.required_inputs,...r.failed_conditions].map(x=>rackLabels[x]||x).join('; ')||'Listed prerequisites supplied; remaining full-wall checks are outside scope.';
  const bolt=[];for(let d=6;d<=24;d+=2){const m=TFKConnections.evaluate('connection_summary',{...cInputs(caseData.connection),d});bolt.push([d,m.design.Fv_Rd_per_plane_N/1000]);}
  plot('boltplot',[{points:bolt,colour:'#2563eb'}],'Bolt diameter (mm)','Per-fastener resistance (kN)','Bolt capacity against diameter');
  const height=[];for(let i=0;i<=20;i++){const p=sInputs(caseData),sa=TFKSeismic.seismic_coefficient(p.alpha,p.soil_factor,p.H_m*i/20,p.H_m,p.Ta_s,p.T1_s);height.push([i/20,TFKSeismic.seismic_force_kN(sa,s.weight_kN,p.gamma_a,p.q_a)]);}
  plot('seismicplot',[{points:height,colour:'#2563eb'}],'Element height ratio z/H','Whole-panel Fa (kN)','Seismic force against height');
  const effective=[],physical=[];for(let t=0;t<=60;t+=2){const sec=TFKFire.evaluate('section',{...caseData.fire,time_min:t});effective.push([t,sec.effective_depth_mm]);physical.push([t,sec.residual_depth_mm]);}
  plot('fireplot',[{points:effective,colour:'#2563eb'},{points:physical,colour:'#64748b',dashed:true}],'Standard-fire duration (min)','Section depth (mm)','Residual depth against fire duration');
  $('source-clause').textContent=c.modes.clause;
 }catch(e){latest=null;$('results').hidden=true;$('error').hidden=false;$('error').textContent='Cannot calculate this input: '+e.message;}
}
for(const id of ['category','shares','face'])$(id).addEventListener('change',()=>{
 if(id==='category')caseData.seismic.element_category=$('category').value;
 if(id==='shares'){const value=$('shares').value.trim();caseData.seismic.bracket_load_shares=value===''?null:value.split(',').map(v=>Number(v.trim()));}
 if(id==='face')caseData.fire.exposed_faces=$('face').value.split(',');render();
});
$('eta-reference').addEventListener('change',()=>{caseData.connection.anchor_ETA_reference=$('eta-reference').value.trim()||null;render();});
$('shares').addEventListener('input',()=>{const value=$('shares').value.trim();caseData.seismic.bracket_load_shares=value===''?null:value.split(',').map(v=>Number(v.trim()));render();});
for(const key of ['tied_down','no_openings','regular_spacing','sheet_edge_sufficient','sheet_fixings_verified'])$('rack-'+key).addEventListener('change',()=>{const value=$('rack-'+key).value;caseData.racking[key]=value==='unknown'?null:value==='true';render();});
$('reset').addEventListener('click',()=>{caseData=structuredClone(baseline);controls();render();});
$('apply-json').addEventListener('click',()=>{try{caseData=JSON.parse($('json').value);controls();render();}catch(e){$('error').hidden=false;$('error').textContent='Invalid case JSON: '+e.message;$('results').hidden=true;}});
$('download').addEventListener('click',()=>{const blob=new Blob([JSON.stringify(caseData,null,2)+'\n'],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='20261018_v1_EditedCaseInputs.json';a.click();URL.revokeObjectURL(url);});
const globals={connections:TFKConnections,materials:TFKMaterials,fire:TFKFire,racking:TFKRacking,seismic:TFKSeismic};
$('fixture').innerHTML=vectors.map((v,i)=>`<option value="${i}">${esc(v.module+' / '+v.operation+' / '+(v.expectedError?'rejection check ':'fixture ')+(i+1))}</option>`).join('');
function fixture(){const v=vectors[Number($('fixture').value)];$('fixture-inputs').value=JSON.stringify(v.inputs,null,2);$('fixture-output').textContent='Select Run equation to calculate this separately labelled verification fixture.';}
$('fixture').addEventListener('change',fixture);$('run-fixture').addEventListener('click',()=>{const v=vectors[Number($('fixture').value)];try{$('fixture-output').textContent=JSON.stringify(globals[v.module].evaluate(v.operation,JSON.parse($('fixture-inputs').value)),null,2);}catch(e){$('fixture-output').textContent='Input rejected: '+e.message;}});
controls();render();fixture();
document.querySelectorAll('[data-tex]').forEach(el=>katex.render(el.dataset.tex,el,{throwOnError:false,displayMode:true}));
})();
