/* AI-assisted educational reference implementation. Not for design.
 * Sources/clauses match the Python modules and dated source register.
 * Missing design actions or applicability data never become assumed passes. */
(function(g){
'use strict';
const MCLAUSES={"C24": "Swedish Wood/TDUK UK Vol.2 1:2022, Table 3.3 p.10; EN 338:2016; EN 1995-1-1 3.2", "GL24h": "Swedish Wood/TDUK UK Vol.2 1:2022, Table 3.4 p.12; EN 14080:2013; EN 1995-1-1 3.3", "kmod": "EN 1995-1-1:2004 3.1.3/Table 3.1; UK handbook Table 3.2 p.8", "kdef": "EN 1995-1-1:2004 3.1.4/Table 3.2; UK handbook Table 9.1 p.32", "gamma_m": "EN 1995-1-1:2004 2.4.1/Table 2.3; UK handbook Table 3.1 p.7; recommended NDP", "design_strength": "EN 1995-1-1:2004 2.4.1, Equation (2.14); UK handbook 3.1 p.7"},MPROPS={"C24": {"material_type": "solid_timber", "fm_k_MPa": 24.0, "ft_0_k_MPa": 14.5, "ft_90_k_MPa": 0.4, "fc_0_k_MPa": 21.0, "fc_90_k_MPa": 2.5, "fv_k_MPa": 4.0, "E_0_mean_MPa": 11000.0, "E_0_05_MPa": 7400.0, "E_90_mean_MPa": 370.0, "G_mean_MPa": 690.0, "rho_k_kg_m3": 350.0, "rho_mean_kg_m3": 420.0}, "GL24h": {"material_type": "glulam", "fm_k_MPa": 24.0, "ft_0_k_MPa": 19.2, "ft_90_k_MPa": 0.5, "fc_0_k_MPa": 24.0, "fc_90_k_MPa": 2.5, "fv_k_MPa": 3.5, "fr_k_MPa": 1.2, "E_0_mean_MPa": 11500.0, "E_0_05_MPa": 9600.0, "E_90_mean_MPa": 300.0, "E_90_05_MPa": 250.0, "G_mean_MPa": 650.0, "G_05_MPa": 540.0, "rho_k_kg_m3": 385.0, "rho_mean_kg_m3": 420.0}},MURL="https://www.universityofgalway.ie/media/timberengineeringresearchgroup/Design-of-timber-structures_Volume2_Rules-and-formulas-according-to-Eurocode-5.pdf";
const FCLAUSES={"charring": "EN 1995-1-2:2004 3.4.2, Equations (3.1)-(3.2), Table 3.1; printed pp.21-23", "effective": "EN 1995-1-2:2004 4.2.2, Equation (4.1), Table 4.1; printed pp.30-31", "strength": "EN 1995-1-2:2004 2.3, Equations (2.1),(2.4), Table 2.1; printed pp.15-16", "kmod_fi": "EN 1995-1-2:2004 4.2.2(5); printed p.31", "gamma_M_fi": "EN 1995-1-2:2004 2.3(1) Note 2; recommended NDP, printed p.15", "section": "Elementary rectangular-section geometry applied to EN 1995-1-2 4.2.2 effective section", "bending": "EN 1995-1-2:2004 4.1/4.2.2 and EN 1995-1-1 6.1.6; uniaxial section bending only, stability excluded"},FURL="https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.2.2004.pdf",RCLAUSE="EN 1995-1-1:2004+A1:2008 9.2.4.2, Equations (9.21)-(9.22), printed pp.94-96; Swedish Wood/TDUK UK Vol.2 1:2022 pp.49-50";
const durations=['permanent','long','medium','short','instantaneous'];
const kmTimber={1:[.6,.7,.8,.9,1.1],2:[.6,.7,.8,.9,1.1],3:[.5,.55,.65,.7,.9]};
const kmOSB={1:[.4,.5,.7,.9,1.1],2:[.3,.4,.55,.7,.9]};
const gm={solid_timber:1.3,glulam:1.25,osb3:1.2,connections:1.3};
const get=(o,k,d)=>Object.prototype.hasOwnProperty.call(o,k)?o[k]:d;
function num(name,v,pos=false,nonneg=false){
 if(typeof v!=='number'||!Number.isFinite(v))throw Error(name+' must be a finite real number');
 if(pos&&v<=0)throw Error(name+' must be positive');
 if(nonneg&&v<0)throw Error(name+' must be non-negative');
 return v;
}
function positive(name,v){return num(name,v,true);}
function service(sc){if(![1,2,3].includes(sc)||typeof sc!=='number')throw Error('service_class must be explicitly selected as 1, 2 or 3');return sc;}
function material(grade){
 if(!Object.prototype.hasOwnProperty.call(MPROPS,grade))throw Error('UNVERIFIED material grade');
 return Object.assign({grade:grade},MPROPS[grade],{source:MCLAUSES[grade],source_url:MURL,status:'REFERENCE_PROPERTIES_NOT_PRODUCT_VERIFIED'});
}
function kmod(duration,sc,type='solid_timber'){
 service(sc);let i=durations.indexOf(duration);if(i<0)throw Error('Unknown load duration');
 let row;if(type==='solid_timber'||type==='glulam')row=kmTimber[sc];
 else if(type==='osb3')row=kmOSB[sc];
 if(!row)throw Error('UNVERIFIED material/service class for kmod');return row[i];
}
function kdef(sc,type='solid_timber'){
 service(sc);if(type==='solid_timber'||type==='glulam')return [.6,.8,2][sc-1];
 if(type==='osb3'&&sc<3)return [1.5,2.25][sc-1];throw Error('UNVERIFIED material/service class for kdef');
}
const Materials={evaluate(op,p){
 switch(op){
 case 'material':return material(p.grade);
 case 'kmod':return {value:kmod(p.load_duration,p.service_class,get(p,'material_type','solid_timber')),source:MCLAUSES.kmod};
 case 'kdef':return {value:kdef(p.service_class,get(p,'material_type','solid_timber')),source:MCLAUSES.kdef};
 case 'gamma_m':if(!Object.prototype.hasOwnProperty.call(gm,p.material_type))throw Error('UNVERIFIED gamma_M material');return {value:gm[p.material_type],status:'RECOMMENDED_NDP_NOT_NATIONAL_ANNEX_VERIFIED',source:MCLAUSES.gamma_m};
 case 'design_strength':return {fd_MPa:positive('fk_MPa',p.fk_MPa)*positive('kmod_value',p.kmod_value)/positive('gamma_M',p.gamma_M),source:MCLAUSES.design_strength};
 default:throw Error('Unknown materials operation');
 }} };
function parameters(type,rho){
 positive('rho_k_kg_m3',rho);let bn,kf;
 if(type==='solid_softwood'&&rho>=290){bn=.8;kf=1.25;}
 else if(type==='glulam_softwood'&&rho>=290){bn=.7;kf=1.15;}
 else if(type==='lvl'&&rho>=480){bn=.7;kf=1.1;}
 else throw Error('UNVERIFIED charring-rate applicability for this material/density');
 return {beta_0_mm_min:.65,beta_n_mm_min:bn,kfi:kf,kmod_fi:1,gamma_M_fi_recommended:1,gamma_status:'RECOMMENDED_NDP_NOT_NATIONAL_ANNEX_VERIFIED',source_url:FURL,source:FCLAUSES.charring+'; '+FCLAUSES.strength};
}
function chars(p){
 let t=num('time_min',p.time_min,false,true),b0=positive('beta_0_mm_min',p.beta_0_mm_min),bn=positive('beta_n_mm_min',p.beta_n_mm_min),d0=positive('d0_mm',get(p,'d0_mm',7));
 if(d0!==7)throw Error('This verified 2004 reduced-section method requires d0_mm = 7');
 let k0=Math.min(t/20,1);
 return {time_min:t,dchar_0_mm:b0*t,dchar_n_mm:bn*t,k0:k0,d0_mm:d0,effective_char_depth_mm:bn*t+k0*d0,source:FCLAUSES.charring+'; '+FCLAUSES.effective};
}
function section(p){
 let b=positive('width_mm',p.width_mm),h=positive('depth_mm',p.depth_mm),faces=p.exposed_faces;
 if(get(p,'protected',false)!==false||get(p,'insulated_assembly',false)!==false)throw Error('Protected members and insulated assemblies are OUT_OF_SCOPE');
 let allowed=['width_left','width_right','depth_front','depth_back'];
 if(!Array.isArray(faces)||faces.length===0||new Set(faces).size!==faces.length||faces.some(x=>!allowed.includes(x)))throw Error('Use unique explicit width_left/right or depth_front/back face names');
 let c=chars({time_min:p.time_min,beta_0_mm_min:get(p,'beta_0_mm_min',.65),beta_n_mm_min:p.beta_n_mm_min,d0_mm:get(p,'d0_mm',7)});
 let de=c.effective_char_depth_mm,dn=c.dchar_n_mm,nw=faces.filter(x=>x.startsWith('width_')).length,nh=faces.filter(x=>x.startsWith('depth_')).length;
 let be=Math.max(0,b-nw*de),he=Math.max(0,h-nh*de),ex=be===0||he===0;
 return Object.assign({},c,{width_mm:b,depth_mm:h,exposed_faces:faces.slice(),residual_width_mm:Math.max(0,b-nw*dn),residual_depth_mm:Math.max(0,h-nh*dn),effective_width_mm:be,effective_depth_mm:he,effective_area_mm2:be*he,I_y_mm4:be*he**3/12,W_y_mm3:be*he**2/6,I_z_mm4:he*be**3/12,W_z_mm3:he*be**2/6,
 centroid_shift_width_mm:ex?null:((faces.includes('width_left')?1:0)-(faces.includes('width_right')?1:0))*de/2,
 centroid_shift_depth_mm:ex?null:((faces.includes('depth_front')?1:0)-(faces.includes('depth_back')?1:0))*de/2,
 status:ex?'SECTION_EXHAUSTED':'SECTION_ONLY_NOT_FIRE_RESISTANCE_APPROVAL',
 orientation:'depth_front/back reduce depth; width_left/right reduce width; y bending uses width*depth^2/6',
 limitations:['Isolated unprotected member under standard fire only','No protected or insulated assembly assessment','No fire actions, stability, connection fire check or separating-function classification']});
}
function bending(p){
 let s=p.section;if(!s||Object.keys(s).length===0)s=section(p);
 let axis=get(p,'axis','y');if(!['y','z'].includes(axis))throw Error('axis must be explicitly y or z');
 let required=['design_bending_moment_Nmm','fm_k_MPa','kfi','gamma_M_fi','kmod_fi'].filter(k=>p[k]===null||p[k]===undefined);
 if(required.length)return {status:'REQUIRED_INPUT',required_inputs:required,utilisation:null,capacity_Nmm:null,passed:null,source:FCLAUSES.bending};
 let demand=Math.abs(num('design_bending_moment_Nmm',p.design_bending_moment_Nmm)),fk=positive('fm_k_MPa',p.fm_k_MPa),kf=positive('kfi',p.kfi),gamma=positive('gamma_M_fi',p.gamma_M_fi),km=positive('kmod_fi',p.kmod_fi);
 if(km!==1)throw Error('Verified reduced cross-section method requires kmod_fi = 1.0');
 let W=num('section modulus',s['W_'+axis+'_mm3'],false,true),fd=km*kf*fk/gamma;
 if(W===0)return {status:'SECTION_EXHAUSTED',capacity_Nmm:0,utilisation:null,passed:false,fd_fi_MPa:fd,demand_Nmm:demand,source:FCLAUSES.bending};
 let capacity=fd*W;
 return {status:'SECTION_BENDING_ONLY',capacity_Nmm:capacity,utilisation:demand/capacity,passed:demand<=capacity,fd_fi_MPa:fd,demand_Nmm:demand,axis:axis,source:FCLAUSES.strength+'; '+FCLAUSES.kmod_fi+'; '+FCLAUSES.bending,limitations:['No beam stability or combined-action check','No fire-action combination is generated','Not a fire-resistance time rating']};
}
const Fire={evaluate(op,p){
 switch(op){case 'parameters':return parameters(p.material_type,p.rho_k_kg_m3);case 'char_depth':return chars(p);case 'section':return section(p);case 'bending':return bending(p);default:throw Error('Unknown fire operation');}
}};
function geometry(p){
 let b=positive('sheet_width_mm',p.sheet_width_mm),h=positive('wall_height_mm',p.wall_height_mm);
 return {b0_mm:h/2,minimum_sheet_width_mm:h/4,width_factor_ci:Math.min(1,b/(h/2)),width_condition_passed:b>=h/4,source:RCLAUSE};
}
function panel(p){
 let z=geometry(p),s=positive('perimeter_spacing_mm',p.perimeter_spacing_mm),ef=positive('edge_capacity_factor',get(p,'edge_capacity_factor',1.2));
 if(ef!==1.2)throw Error('Verified Method A edge-capacity enhancement is 1.2');
 let enhanced=get(p,'fastener_capacity_already_edge_enhanced',false);if(typeof enhanced!=='boolean')throw Error('fastener_capacity_already_edge_enhanced must be Boolean');
 let required=[],failed=[];
 for(let k of ['tied_down','no_openings','regular_spacing','sheet_edge_sufficient','sheet_fixings_verified']){
  let v=get(p,k,null);if(v!==null&&typeof v!=='boolean')throw Error('Applicability flags must be explicitly True, False or None');
  if(v===null)required.push(k);if(v===false)failed.push(k);
 }
 if(!z.width_condition_passed)failed.push('sheet_width_below_h_over_4');
 let raw=get(p,'fastener_design_resistance_N',null),edge=null,formula=null;
 if(raw===null)required.push('fastener_design_resistance_N');
 else{edge=positive('fastener_design_resistance_N',raw)*(enhanced?1:ef);formula=edge*p.sheet_width_mm*z.width_factor_ci/s;}
 let status=failed.length?'INAPPLICABLE':required.length?'REQUIRED_INPUT':'CONDITIONAL_PANEL_SUBCHECK';
 return Object.assign({},z,{status:status,required_inputs:required,failed_conditions:failed,fastener_edge_factor_applied:enhanced?1:ef,edge_fastener_design_resistance_N:edge,formula_capacity_N:formula,capacity_N:status==='CONDITIONAL_PANEL_SUBCHECK'?formula:null,edge_factor_source:'EN 1995-1-1 9.2.4.2(5), 1.2 sheet-edge enhancement relative to Section 8',limitations:['Not a complete wall or façade resistance check','Method A national choice not verified','Stud buckling/bearing, sheet shear buckling, central fixings, inter-element transfer, anchorage and serviceability remain to be verified']});
}
const Racking={evaluate(op,p){switch(op){case 'geometry':return geometry(p);case 'panel':return panel(p);default:throw Error('Unknown racking operation');}}};
g.TFKMaterials=Materials;g.TFKFire=Fire;g.TFKRacking=Racking;
})(globalThis);
