/* Educational EN 1998-1:2004 Module E. Not for design.
 * Primary source read: https://www.phd.eng.br/wp-content/uploads/2015/02/en.1998.1.2004.pdf
 * Printed pp.67-68: 4.3.5.2 equations4.24/4.25, 4.3.5.3, Table4.4.
 * Printed pp.76-77: 4.4.3.2 equations4.31-4.33 and recommended nu NDP.
 * Slot geometry and bracket load shares are declared models, not code rules.
 * Mirrors timberkit/seismic.py. No anchor capacity or implicit bracket count.
 */
(function (root) {
  "use strict";
  function number(name, value, positive=false, nonnegative=false) {
    if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(name+" must be a finite real number");
    if (positive && value <= 0) throw new Error(name+" must be positive");
    if (nonnegative && value < 0) throw new Error(name+" must be non-negative");
    return value;
  }
  function seismic_coefficient(alpha, soil_factor, z_m, H_m, Ta_s, T1_s) {
    number("alpha",alpha,false,true); number("soil_factor",soil_factor,true);
    number("z_m",z_m,false,true); number("H_m",H_m,true);
    number("Ta_s",Ta_s,false,true); number("T1_s",T1_s,true);
    if(z_m>H_m) throw new Error("z_m must not exceed H_m in this toolkit");
    const floor=alpha*soil_factor;
    return Math.max(floor, floor*(3*(1+z_m/H_m)/(1+(1-Ta_s/T1_s)**2)-0.5));
  }
  function seismic_force_kN(Sa,weight_kN,gamma_a,q_a) {
    number("Sa",Sa,false,true);number("weight_kN",weight_kN,false,true);
    number("gamma_a",gamma_a,true);number("q_a",q_a,true);
    // 4.3.5.3: ordinary elements may use 1.0; specified life-safety/hazardous
    // cases require >=1.5. The caller must justify that classification.
    if(gamma_a<1) throw new Error("gamma_a must be at least 1.0 in this EN 1998-1 study");
    return Sa*weight_kN*gamma_a/q_a;
  }
  function facade_behaviour_factor(q_a) {
    number("q_a",q_a,true);
    if(q_a<1 || q_a>2) throw new Error("Facade q_a must be between 1.0 and the Table 4.4 upper limit 2.0");
    return q_a;
  }
  function panel_weight_kN(height_mm,width_mm,self_weight_kN_m2) {
    number("height_mm",height_mm,true);number("width_mm",width_mm,true);
    number("self_weight_kN_m2",self_weight_kN_m2,false,true);
    return height_mm*width_mm/1000000*self_weight_kN_m2;
  }
  function recommended_nu(importance_class) {
    if(["I","II"].includes(importance_class)) return 0.5;
    if(["III","IV"].includes(importance_class)) return 0.4;
    throw new Error("importance_class must be I, II, III or IV");
  }
  const coefficients={brittle_attached:0.005,ductile:0.0075,non_interfering:0.010};
  function drift_check(dr_mm,storey_height_mm,nu,category) {
    number("dr_mm",dr_mm,false,true);number("storey_height_mm",storey_height_mm,true);number("nu",nu,true);
    if(nu>1) throw new Error("nu must not exceed 1.0 in this reduction-factor study");
    if(!Object.hasOwn(coefficients,category)) throw new Error("category must be brittle_attached, ductile or non_interfering");
    const limit=coefficients[category]*storey_height_mm,demand=dr_mm*nu;
    return {category,demand_mm:demand,limit_mm:limit,dr_limit_mm:limit/nu,ratio:demand/limit,
      passes:demand<=limit || Math.abs(demand-limit)<=Math.max(1e-12,1e-12*Math.max(Math.abs(demand),Math.abs(limit)))};
  }
  function bracket_forces(force_kN,load_shares) {
    number("force_kN",force_kN,false,true);
    if(load_shares==null) throw new Error("REQUIRED input: bracket load shares from a justified load-path model");
    if(!Array.isArray(load_shares)) throw new Error("load_shares must be an array of non-negative numbers");
    load_shares.forEach(x=>number("load share",x,false,true));
    const sum=load_shares.reduce((a,b)=>a+b,0);
    if(!load_shares.length || Math.abs(sum-1)>1e-9) throw new Error("bracket load shares must be non-empty and sum to 1.0");
    return load_shares.map(x=>force_kN*x);
  }
  function slot_length_mm(dr_mm,bolt_diameter_mm,installation_allowance_mm=0,centred=true,movement_factor=1) {
    number("dr_mm",dr_mm,false,true);number("bolt_diameter_mm",bolt_diameter_mm,true);
    number("installation_allowance_mm",installation_allowance_mm,false,true);number("movement_factor",movement_factor,true);
    if(typeof centred!=="boolean") throw new Error("centred must be a Boolean");
    const travel=dr_mm*movement_factor;
    return {slot_length_mm:bolt_diameter_mm+(centred?2:1)*travel+installation_allowance_mm,
      travel_each_direction_mm:travel,reversed_motion_accommodated:centred,
      assumption:centred?"centred, friction-free, reversing translation":"one-sided translation only"};
  }
  function case_summary(p) {
    const Sa=seismic_coefficient(p.alpha,p.soil_factor,p.z_m,p.H_m,p.Ta_s,p.T1_s);
    const weight=panel_weight_kN(p.height_mm,p.width_mm,p.self_weight_kN_m2);
    const Fa=seismic_force_kN(Sa,weight,p.gamma_a,facade_behaviour_factor(p.q_a));
    return {Sa,weight_kN:weight,Fa_kN:Fa,
      bracket_forces_kN:p.load_shares==null?null:bracket_forces(Fa,p.load_shares),
      bracket_status:p.load_shares==null?"REQUIRED: justified bracket load shares":"DEMAND ONLY: supplied load shares",
      anchor_status:"REQUIRED: project-specific manufacturer ETA capacity; no default",
      drift:drift_check(p.dr_mm,p.storey_height_mm,p.nu,p.category),
      slot:slot_length_mm(p.dr_mm,p.bolt_diameter_mm,p.installation_allowance_mm===undefined?0:p.installation_allowance_mm)};
  }
  const operations={
    seismic_coefficient:p=>seismic_coefficient(p.alpha,p.soil_factor,p.z_m,p.H_m,p.Ta_s,p.T1_s),
    seismic_force_kN:p=>seismic_force_kN(p.Sa,p.weight_kN,p.gamma_a,p.q_a),
    facade_behaviour_factor:p=>facade_behaviour_factor(p.q_a),
    panel_weight_kN:p=>panel_weight_kN(p.height_mm,p.width_mm,p.self_weight_kN_m2),
    recommended_nu:p=>recommended_nu(p.importance_class),
    drift_check:p=>drift_check(p.dr_mm,p.storey_height_mm,p.nu,p.category),
    bracket_forces:p=>bracket_forces(p.force_kN,p.load_shares),
    slot_length_mm:p=>slot_length_mm(p.dr_mm,p.bolt_diameter_mm,p.installation_allowance_mm,p.centred,p.movement_factor),
    case_summary,
  };
  function evaluate(operation,inputs) {
    if(!Object.hasOwn(operations,operation)) throw new Error("Unknown seismic operation: "+operation);
    if(inputs===null || typeof inputs!=="object" || Array.isArray(inputs)) throw new Error("inputs must be an object");
    return operations[operation](inputs);
  }
  root.TFKSeismic={evaluate,seismic_coefficient,seismic_force_kN,facade_behaviour_factor,panel_weight_kN,
    recommended_nu,drift_check,bracket_forces,slot_length_mm,case_summary,DRIFT_COEFFICIENTS:coefficients};
})(globalThis);
