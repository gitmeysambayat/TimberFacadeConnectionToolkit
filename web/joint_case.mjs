/* AI-assisted educational joint case, 18 October 2026. Not for design.
 * Load web/connections.js and web/materials_fire_racking.js before this file.
 * This IIFE may be embedded in a standalone page. It deliberately has no
 * imports, exports, DOM side effects, network calls or solver submissions.
 * Source equations and scope match timberkit/joint_case.py.
 */
(function(root){
"use strict";
const STATUS="EDUCATIONAL_COMPONENT_RESULTS_NO_OVERALL_DESIGN_PASS";
const DEFAULTS={centre_thickness_mm:100,side_thickness_mm:50,width_mm:200,
 overlap_mm:200,end_distance_mm:100,diameter_mm:12,hole_diameter_mm:13,
 washer_diameter_mm:40,washer_thickness_mm:4,Gk_N:3000,Qk_N:2000,
 gamma_G:1.35,gamma_Q:1.5,kmod:.8,gamma_M:1.3,additional_freeplay_mm:0,
 study_slip_budget_mm:2,psi2:.3};
const ASSUMPTIONS={material_grade:"C24",
 bolt_grade:"8.8 (specified study assumption; product certification not verified)",
 bolt_fu_k_MPa:800,service_class:2,load_duration:"medium baseline; kmod overrides are numerical scenarios",load_to_grain_angle_deg:0,
 number_of_fasteners:1,shear_planes:2,size_factor_kh:1,rope_effect_N:0,
 washer_locations:"One washer under the head and one under the nut",
 action_basis:"Selected illustrative 1.35Gk + 1.5Qk; Nser = Gk + Qk. Not a verified project combination.",
 slip_basis:"Post-seating instantaneous elastic increment; two identical shear-plane springs in parallel.",
 freeplay_basis:"Additional total assembly movement is an explicit scenario input, not inferred from hole diameter.",
 study_budget_basis:"Chosen 2 mm study budget is not a Eurocode limit or product acceptance criterion.",
 final_slip_basis:"First-generation action-wise creep estimate, identical SC2 timbers: connection kdef = 2 x member kdef. psi2 is a selected scenario, not a verified occupancy category.",
 duration_envelope_basis:"Combined action uses the explicit kmod input; permanent-only action is separately checked with first-generation SC2 kmod = 0.6."};
const UNRESOLVED=[
 "Applicable current standard edition, National Annex and project action combinations",
 "Product and timber grading declarations; bolt yield moment and shank/thread position",
 "Bolt steel resistance, washer bearing resistance and full bearing in the assembled detail",
 "Brittle splitting, row shear and end tear-out; minimum distances alone are not verification",
 "Restraint against rotation: a single bolt has no established moment-resisting function",
 "Fabrication tolerances, seating/freeplay, tightening, moisture movement, corrosion and durability",
 "Applicability and physical validation of the long-term creep estimate; reversals, cyclic degradation and repeated assembly",
 "Fire resistance of the connection and the complete timber/envelope assembly",
 "Physical prototype testing, model calibration and manufacturing/assembly trials"];
function number(v,name,zero=false){
 if(typeof v!=="number"||!Number.isFinite(v))throw Error(name+" must be a finite real number");
 if(zero?v<0:v<=0)throw Error(name+" must be "+(zero?"non-negative":"positive"));return v;
}
function finiteResult(v){
 if(typeof v==="number"&&!Number.isFinite(v))throw Error("Case calculation overflowed the finite numerical range");
 if(Array.isArray(v))v.forEach(finiteResult);
 else if(v&&typeof v==="object")Object.values(v).forEach(finiteResult);
 return v;
}
function checked(overrides){
 if(overrides===undefined||overrides===null)overrides={};
 if(overrides===null||typeof overrides!=="object"||Array.isArray(overrides))throw Error("Case inputs must be an object");
 const unknown=Object.keys(overrides).filter(k=>!Object.hasOwn(DEFAULTS,k));
 if(unknown.length)throw Error("Unsupported case inputs: "+unknown.sort().join(", "));
 const p={...DEFAULTS,...overrides};
 for(const[k,v]of Object.entries(p))number(v,k,["Gk_N","Qk_N","additional_freeplay_mm","psi2"].includes(k));
 if(p.diameter_mm<6||p.diameter_mm>30)throw Error("Selected educational bolt scope is 6 <= diameter_mm <= 30");
 if(p.hole_diameter_mm<p.diameter_mm)throw Error("hole_diameter_mm must not be smaller than diameter_mm");
 if(p.hole_diameter_mm>=p.width_mm)throw Error("Hole must leave a positive timber net width");
 if(p.end_distance_mm>=p.overlap_mm)throw Error("Bolt must lie inside the overlap");
 if(p.gamma_G<1||p.gamma_Q<1||p.gamma_M<1)throw Error("Selected adverse-action/material partial factors must be at least 1");
 if(p.kmod>1.1)throw Error("Selected solid-timber kmod study scope is 0 < kmod <= 1.1");
 if(p.psi2>1)throw Error("Selected psi2 study scope is 0 <= psi2 <= 1");return p;
}
function geometry(p){
 const d=p.diameter_mm,minimum=root.TFKConnections.evaluate("minimum_spacings",{d,fastener:"bolt",alpha_deg:0}).minimum_mm,
 left=p.end_distance_mm,right=p.overlap_mm-left,edge=p.width_mm/2,checks={};
 function add(name,actual,required,clause,direction="minimum"){
  const satisfies=direction==="minimum"?actual+1e-10>=required:direction==="strictly_greater"?actual>required:actual<=required+1e-10;
  checks[name]={actual_mm:actual,required_mm:required,comparison:direction,status:satisfies?"PASS":"FAIL",clause};
 }
 const table="EN1995-1-1 8.5.1.1 Table8.4, parallel grain; SW2 p45";
 add("left_loaded_end",left,minimum.a3_t,table);add("right_loaded_end",right,minimum.a3_t,table);
 add("both_centred_edges",edge,Math.max(minimum.a4_t,minimum.a4_c),table);
 const detail="EN1995-1-1 10.4.3(1)-(2)";
 add("timber_hole_diameter",p.hole_diameter_mm,d+1,detail,"maximum");
 add("washer_diameter",p.washer_diameter_mm,3*d,detail);
 add("washer_thickness",p.washer_thickness_mm,.3*d,detail);
 add("washer_face_footprint",p.washer_diameter_mm/2,Math.min(left,right,edge),
  "Elementary footprint geometry; full bearing resistance remains unverified","maximum");
 add("washer_outer_diameter_exceeds_hole",p.washer_diameter_mm,p.hole_diameter_mm,
  "Elementary ring geometry; washer hole/product geometry remains unverified","strictly_greater");
 return{status:Object.values(checks).some(c=>c.status==="FAIL")?"FAIL":"PASS_IN_SCOPE",checks,
  opposite_end_mm:right,centred_edge_mm:edge,inter_fastener_spacing:"NOT_APPLICABLE_SINGLE_BOLT",bearing_resistance_status:"UNVERIFIED"};
}
function calculateCase(inputs){
 if(!root.TFKConnections||!root.TFKMaterials)throw Error("Joint case requires the connection and material modules");
 const p=checked(inputs),material=root.TFKMaterials.evaluate("material",{grade:"C24"}),d=p.diameter_mm,
 ned=p.gamma_G*p.Gk_N+p.gamma_Q*p.Qk_N,nser=p.Gk_N+p.Qk_N,
 fh=root.TFKConnections.evaluate("embedment",{rho_k:material.rho_k_kg_m3,d,fastener:"bolt",alpha_deg:0}),
 my=root.TFKConnections.evaluate("yield_moment",{d,fu_k:ASSUMPTIONS.bolt_fu_k_MPa,fastener:"bolt"}),
 johansen=root.TFKConnections.evaluate("timber_modes",{d,t1:p.side_thickness_mm,t2:p.centre_thickness_mm,
 fh1_k:fh.fh_k,fh2_k:fh.fh_k,My_Rk:my.My_Rk,shear:"double",fastener:"bolt",Fax_Rk:0}),
 capacity=root.TFKConnections.evaluate("design_capacity",{Fv_Rk_N:johansen.Fv_Rk_N,kmod:p.kmod,gamma_M:p.gamma_M,n_eff:1,shear_planes:2}),
 resistance=capacity.group_design_capacity_N;
 capacity.utilisation=ned/resistance;capacity.status=ned<=resistance+1e-10?"PASS_IN_SCOPE":"FAIL";
 const geo=geometry(p),ft_d=root.TFKMaterials.evaluate("design_strength",{fk_MPa:material.ft_0_k_MPa,kmod_value:p.kmod,gamma_M:p.gamma_M}).fd_MPa;
 function net(thickness,demand){const area=(p.width_mm-p.hole_diameter_mm)*thickness,rd=area*ft_d;
  return{net_area_mm2:area,demand_N:demand,stress_MPa:demand/area,design_resistance_N:rd,
   utilisation:demand/rd,status:demand<=rd+1e-10?"PASS_IN_SCOPE":"FAIL"};}
 const nets={centre:net(p.centre_thickness_mm,ned),one_side:net(p.side_thickness_mm,ned/2),
 ft_0_k_MPa:material.ft_0_k_MPa,ft_0_d_MPa:ft_d,size_factor_kh:1,
 clause:"EN1995-1-1 5.1(2), 6.1.2; SW2 p22. Net area at one hole, no favourable size increase."};
 const permanentNed=p.gamma_G*p.Gk_N,
 permanentKmod=root.TFKMaterials.evaluate("kmod",{load_duration:"permanent",service_class:2,material_type:"solid_timber"}).value,
 permanentRd=root.TFKConnections.evaluate("design_capacity",{Fv_Rk_N:johansen.Fv_Rk_N,kmod:permanentKmod,gamma_M:p.gamma_M,n_eff:1,shear_planes:2}).group_design_capacity_N,
 permanentFt=root.TFKMaterials.evaluate("design_strength",{fk_MPa:material.ft_0_k_MPa,kmod_value:permanentKmod,gamma_M:p.gamma_M}).fd_MPa,
 permanentCentreU=permanentNed/(nets.centre.net_area_mm2*permanentFt),
 permanentSideU=(permanentNed/2)/(nets.one_side.net_area_mm2*permanentFt),
 combinedMax=Math.max(capacity.utilisation,nets.centre.utilisation,nets.one_side.utilisation),
 permanentMax=Math.max(permanentNed/permanentRd,permanentCentreU,permanentSideU),
 durationChecks={combined:{NEd_N:ned,kmod:p.kmod,Rd_N:resistance,utilisation:capacity.utilisation,
 net_tension_utilisation:Math.max(nets.centre.utilisation,nets.one_side.utilisation),
 centre_net_tension_utilisation:nets.centre.utilisation,one_side_net_tension_utilisation:nets.one_side.utilisation,
 status:combinedMax>1?"FAIL":"PASS_IN_SCOPE"},
 permanent_only:{NEd_N:permanentNed,kmod:permanentKmod,Rd_N:permanentRd,utilisation:permanentNed/permanentRd,
 ft_0_d_MPa:permanentFt,net_tension_utilisation:Math.max(permanentCentreU,permanentSideU),
 centre_net_tension_utilisation:permanentCentreU,one_side_net_tension_utilisation:permanentSideU,
 status:permanentMax>1?"FAIL":"PASS_IN_SCOPE"},
 governing_case:permanentMax>combinedMax?"permanent_only":"combined",
 status:Math.max(combinedMax,permanentMax)>1?"FAIL":"PASS_IN_SCOPE",
 clause:"EN1995-1-1 3.1.3/Table3.1; SW2 pp7-8. Selected illustrative G and G+Q envelope, not a complete project combination set."};
 const perPlane=root.TFKConnections.evaluate("slip_modulus",{rho_m:material.rho_mean_kg_m3,d,fastener:"bolt",steel_factor:1}),
 kjoint=2*perPlane.Kser_N_per_mm,elastic=nser/kjoint,total=elastic+p.additional_freeplay_mm,
 memberKdef=root.TFKMaterials.evaluate("kdef",{service_class:2,material_type:"solid_timber"}).value,
 connectionKdef=2*memberKdef,finalG=p.Gk_N*(1+connectionKdef)/kjoint,
 finalQ=p.Qk_N*(1+p.psi2*connectionKdef)/kjoint,finalElastic=finalG+finalQ,finalTotal=finalElastic+p.additional_freeplay_mm,
 slip={Kser_per_plane_N_per_mm:perPlane.Kser_N_per_mm,Kjoint_N_per_mm:kjoint,
 postseating_elastic_mm:elastic,additional_freeplay_mm:p.additional_freeplay_mm,illustrative_total_mm:total,
 study_budget_mm:p.study_slip_budget_mm,study_budget_utilisation:total/p.study_slip_budget_mm,
 study_budget_status:total<=p.study_slip_budget_mm?"WITHIN_CHOSEN_STUDY_BUDGET":"EXCEEDS_CHOSEN_STUDY_BUDGET",
 clearance_model_status:"NOT_MODELLED_INPUT_SCENARIO_ONLY",member_kdef:memberKdef,connection_kdef:connectionKdef,psi2:p.psi2,
 final_G_component_mm:finalG,final_Q_component_mm:finalQ,final_elastic_mm:finalElastic,final_total_mm:finalTotal,
 final_budget_utilisation:finalTotal/p.study_slip_budget_mm,
 final_budget_status:finalTotal<=p.study_slip_budget_mm?"WITHIN_CHOSEN_STUDY_BUDGET":"EXCEEDS_CHOSEN_STUDY_BUDGET",
 final_deformation_status:"FIRST_GENERATION_CREEP_ESTIMATE_NOT_TEST_VALIDATED",
 clause:"EN1995-1-1 7.1 Table7.1, 2.3.2.2(3), 2.2.3(5); SW2 p33, SW1 pp157-159 Table5.4/Eq5.86. Parallel-spring equilibrium."},failed=[];
 if(capacity.status==="FAIL")failed.push("johansen_design_resistance");
 if(durationChecks.permanent_only.utilisation>1)failed.push("permanent_only_johansen_design_resistance");
 if(durationChecks.permanent_only.net_tension_utilisation>1)failed.push("permanent_only_net_tension");
 if(geo.status==="FAIL")failed.push("detail_geometry");
 for(const member of ["centre","one_side"])if(nets[member].status==="FAIL")failed.push("net_tension_"+member);
 return finiteResult({status:STATUS,inputs:p,assumptions:{...ASSUMPTIONS},material,
 actions:{NEd_N:ned,Nser_N:nser,per_plane_design_N:ned/2,per_plane_service_N:nser/2,centre_design_N:ned,one_side_design_N:ned/2},
 embedment:fh,yield_moment:my,johansen,design_capacity:capacity,geometry:geo,net_tension:nets,load_duration_checks:durationChecks,slip,
 component_resistance_and_geometry_status:failed.length?"FAIL_IN_SCOPE":"NO_FAILURE_IN_CHECKED_COMPONENTS",
 failed_component_checks:failed,unresolved_checks:[...UNRESOLVED],source_ids:["SW2_2022_UK","EC5_PUBLIC_2004_A1","SW1_2022"]});
}
function sensitivityCases(){
 const cases=[];
 for(const d of [8,10,12,14,16,20]){
  const p={...DEFAULTS,diameter_mm:d,hole_diameter_mm:d+1,washer_diameter_mm:Math.max(40,3*d),washer_thickness_mm:Math.max(4,.3*d)};
  cases.push({id:"diameter_"+d,changed_inputs:["diameter_mm","hole_diameter_mm","washer_diameter_mm","washer_thickness_mm"],result:calculateCase(p)});
 }
 for(const f of [0,.5,1,2])cases.push({id:"freeplay_"+(Number.isInteger(f)?f+".0":f),changed_inputs:["additional_freeplay_mm"],result:calculateCase({additional_freeplay_mm:f})});
 for(const k of [.6,.8,.9])cases.push({id:"kmod_"+k,changed_inputs:["kmod"],result:calculateCase({kmod:k})});
 for(const psi of [0,.3,1])cases.push({id:"psi2_"+(Number.isInteger(psi)?psi+".0":psi),changed_inputs:["psi2"],result:calculateCase({psi2:psi})});
 cases.push({id:"permanent_only",changed_inputs:["Qk_N","kmod"],result:calculateCase({Qk_N:0,kmod:.6})});
 return cases;
}
root.TFKJointCase={evaluate:calculateCase,calculateCase,defaultInputs(){return{...DEFAULTS};},sensitivityCases};
})(globalThis);
