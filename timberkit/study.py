"""Export the explicitly illustrative study and Python/JavaScript fixtures.

AI-assisted educational tool, not for design. No network or solver calls.
Run from the repository root with ``python -m timberkit.study``.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from . import connections, fire, materials, racking, seismic
from .release import PREFIX

ROOT = Path(__file__).resolve().parents[1]
MODULES = {"connections": connections, "materials": materials,
           "fire": fire, "racking": racking, "seismic": seismic}


def connection_inputs(case):
    c = case["connection"]
    return dict(rho_k=c["rho_k_kg_m3"], rho_m=c["rho_mean_kg_m3"],
                d=c["diameter_mm"], fu_k=c["fu_MPa"],
                t1=c["timber_thickness_mm"], t_steel=c["steel_plate_thickness_mm"],
                n=c["number_in_row"], a1=c["spacing_parallel_mm"],
                kmod=c["kmod"], gamma_M=c["gamma_M"],
                alpha_deg=c["load_angle_deg"], Fax_Rk=c["Fax_Rk_N"],
                fastener=c["fastener_type"], steel_factor=c["steel_slip_factor"],
                hole_tolerance_mm=c.get("hole_tolerance_mm"),
                spacing_actual=dict(a1=c["spacing_parallel_mm"],
                    a2=c["spacing_perpendicular_mm"], a3_t=c["loaded_end_mm"],
                    a3_c=c["unloaded_end_mm"], a4_t=c["loaded_edge_mm"],
                    a4_c=c["unloaded_edge_mm"]),
                design_shear_N=c["design_shear_demand_N"],
                anchor_capacity_N=c["anchor_design_capacity_N"])


def seismic_inputs(case):
    p, s = case["panel"], case["seismic"]
    categories={"brittle":"brittle_attached", "ductile":"ductile", "non_interfering":"non_interfering"}
    return dict(alpha=s["alpha"], soil_factor=s["soil_factor"],
                z_m=s["element_height_m"], H_m=s["building_height_m"],
                Ta_s=s["element_period_s"], T1_s=s["fundamental_period_s"],
                height_mm=p["height_mm"], width_mm=p["width_mm"],
                self_weight_kN_m2=p["self_weight_kN_m2"], gamma_a=s["gamma_a"],
                q_a=s["q_a"], dr_mm=s["design_interstorey_drift_mm"],
                storey_height_mm=s["storey_height_mm"], nu=s["nu"],
                category=categories.get(s["element_category"],s["element_category"]),
                bolt_diameter_mm=s["slot_bolt_diameter_mm"],
                installation_allowance_mm=s["slot_installation_allowance_mm"],
                load_shares=s["bracket_load_shares"])


def calculate_case(case):
    """Return component calculations without an overall design-pass flag."""
    p, f, s = case["panel"], case["fire"], case["seismic"]
    cs = connections.evaluate("connection_summary", connection_inputs(case))
    eta = case["connection"].get("anchor_ETA_reference")
    if not isinstance(eta, str) or not eta.strip():
        cs["missing_inputs"].append("anchor_ETA_reference")
        if cs["status"] == "PASS_IN_SCOPE":
            cs["status"] = "UNVERIFIED"
    ss = seismic.evaluate("case_summary", seismic_inputs(case))
    ss["slot"] = seismic.slot_length_mm(s["design_interstorey_drift_mm"],
        s["slot_bolt_diameter_mm"], s["slot_installation_allowance_mm"],
        s["slot_centred"], s["slot_movement_factor"])
    sections=[]
    for t in f["times_min"]:
        inputs={k:f[k] for k in ("width_mm","depth_mm","beta_n_mm_min","beta_0_mm_min","d0_mm","exposed_faces")}
        section=fire.evaluate("section",dict(inputs,time_min=t))
        check=fire.check_fire_bending(section,f["design_bending_moment_Nmm"],f["fm_k_MPa"],
            kfi=f["kfi"],gamma_M_fi=f["gamma_M_fi"],kmod_fi=f["kmod_fi"],axis="y")
        sections.append(dict(section=section,bending=check))
    rk=racking.evaluate("panel",case["racking"])
    # Area and pressure resultants are elementary geometry, not a design combination.
    area=p["height_mm"]*p["width_mm"]/1e6
    return dict(status="EDUCATIONAL_COMPONENT_RESULTS_NO_OVERALL_DESIGN_PASS",
        panel_area_m2=area, characteristic_wind_resultant_kN=area*p["characteristic_wind_kN_m2"],
        connection=cs,seismic=ss,fire=sections,racking=rk,
        materials={g:materials.get_material(g) for g in ("C24","GL24h")},
        learner_verification_records=case["learner_verification_records"])


def verification_rows():
    """Independent manual targets retain their stated rounding precision.

    Tolerances reflect displayed rounding, not broad code-validation claims.
    Exact equations are tested separately in pytest. Source IDs refer to
    opened handbook/standards records; printed examples are distinct fixtures.
    """
    embed=connections.evaluate("embedment",dict(rho_k=350,d=12,fastener="bolt"))
    my=connections.evaluate("yield_moment",dict(d=12,fu_k=400,fastener="bolt"))
    slip=connections.evaluate("slip_modulus",dict(rho_m=420,d=12,fastener="bolt",steel_factor=1))
    ne=connections.evaluate("effective_number",dict(n=5,a1=84,d=12,fastener="bolt"))
    sa=seismic.seismic_coefficient(.2,1.15,12,15,.05,.5)
    wa=seismic.panel_weight_kN(2700,1250,.6)
    rows=[]
    def add(name,expected,value,unit,tolerance,source):
        rows.append(dict(quantity=name,reference_value=expected,toolkit_value=value,
            difference=value-expected,unit=unit,tolerance=tolerance,
            passed=abs(value-expected)<=tolerance+1e-12,source=source))
    add("Bolt embedment parallel to grain",25.3,embed["fh_k"],"MPa",.05,"Hand: EN 1995-1-1 8.5.1.1 Eq8.32")
    add("M12 characteristic yield moment",76.7,my["My_Rk"]/1000,"kN mm",.05,"Hand: EN 1995-1-1 8.5.1.1 Eq8.30")
    add("Timber-to-timber Kser per plane",4.49,slip["Kser_N_per_mm"]/1000,"kN/mm",.005,"Hand: EN 1995-1-1 Table7.1")
    add("Timber-to-timber Ku per plane",2.99,slip["Ku_N_per_mm"]/1000,"kN/mm",.005,"Hand: EN 1995-1-1 2.2.2(2)")
    add("Effective number of five bolts at 7d",3.65,ne["n_eff"],"count",.005,"Hand: EN 1995-1-1 Eq8.34")
    for t,target in ((10,11.5),(30,31.),(60,55.)):
        add(f"Effective section loss at {t} min",target,fire.effective_char_depth(t,.8),"mm",1e-10,"Hand: EN 1995-1-2 4.2.2 Eq4.1/Table4.1")
    add("Non-structural seismic coefficient Sa",.571,sa,"dimensionless",.0005,"Hand: EN 1998-1 4.3.5.2 Eq4.25")
    add("Whole-panel weight",2.03,wa,"kN",.0050001,"Hand: stated area times assumed self-weight;2.025 exact")
    add("Whole-panel seismic force Fa",.578,seismic.seismic_force_kN(sa,wa,1,2),"kN",.0005,"Hand: EN 1998-1 4.3.5.2 Eq4.24")
    for category,target in (("brittle_attached",15.),("ductile",22.5),("non_interfering",30.)):
        value=seismic.drift_check(15,3000,.5,category)["limit_mm"]
        add(f"Reduced drift RHS, {category}",target,value,"mm",1e-10,"Hand: EN 1998-1 4.4.3.2 Eqs4.31-4.33; compares dr*nu")
    add("Method A sheet width factor ci",.926,racking.method_a_geometry(1250,2700)["width_factor_ci"],"dimensionless",.0005,"Hand: EN 1995-1-1 9.2.4.2 Eq9.22")
    for ex in connections.published_examples():
        pairs=[("published_Fv_Rk_N","toolkit_Fv_Rk_N","characteristic",10),
               ("published_total_design_N","toolkit_total_design_N","group design",100),
               ("published_no_rope_N","toolkit_no_rope_N","no rope",2),
               ("published_with_rope_N","toolkit_with_rope_N","with rope",10),
               ("published_design_N","toolkit_design_N","design",10)]
        for ref,actual,label,tol in pairs:
            if ref in ex:add(ex["id"]+" "+label,ex[ref],ex[actual],"N",tol,"Published: Swedish Wood Vol3 2022 "+ex["id"]+"; documented example parameters")
    return rows


def plot_data(case):
    c=connection_inputs(case);s=seismic_inputs(case);f=case["fire"]
    bolt=[]
    for d in range(6,25,2):
        out=connections.evaluate("connection_summary",dict(c,d=float(d)))
        bolt.append(dict(diameter_mm=d,per_fastener_design_N=out["design"]["Fv_Rd_per_plane_N"],
            group_design_N=out["design"]["group_design_capacity_N"],plate_class=out["modes"]["plate_class"],
            governing=out["modes"]["governing_mode"],status=out["status"]))
    heights=[]
    for i in range(21):
        ratio=i/20;sa=seismic.seismic_coefficient(s["alpha"],s["soil_factor"],ratio*s["H_m"],s["H_m"],s["Ta_s"],s["T1_s"])
        heights.append(dict(z_over_H=ratio,Fa_kN=seismic.seismic_force_kN(sa,seismic.panel_weight_kN(s["height_mm"],s["width_mm"],s["self_weight_kN_m2"]),s["gamma_a"],s["q_a"])))
    residual=[]
    for t in range(0,61,2):
        section=fire.reduced_section_rectangular(f["width_mm"],f["depth_mm"],t,f["beta_n_mm_min"],f["exposed_faces"],f["beta_0_mm_min"],f["d0_mm"])
        residual.append(dict(time_min=t,physical_residual_depth_mm=section["residual_depth_mm"],effective_depth_mm=section["effective_depth_mm"]))
    return dict(bolt=bolt,seismic=heights,fire=residual)


def figures(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    specifications=[("BoltCapacity","bolt","diameter_mm","per_fastener_design_N","Bolt diameter (mm)","Per-fastener design resistance (N)","Fixed plate and timber geometry; detailing remains conditional"),
        ("SeismicHeight","seismic","z_over_H","Fa_kN",r"Element height ratio $z/H$","Whole-panel seismic force (kN)","Illustrative non-structural element demand"),
        ("FireDepth","fire","time_min","effective_depth_mm","Standard-fire duration (min)","Effective section depth (mm)","One depth face; isolated unprotected stud")]
    for name,key,x,y,xlabel,ylabel,title in specifications:
        rows=data[key];fig,ax=plt.subplots(figsize=(6.3,3.3),layout="constrained")
        ax.plot([r[x] for r in rows],[r[y] for r in rows],color="#2563eb",lw=2)
        if key=="fire":ax.plot([r[x] for r in rows],[r["physical_residual_depth_mm"] for r in rows],color="#64748b",ls="--",label="Physical notional-char residual");ax.legend(fontsize=8)
        ax.set(xlabel=xlabel,ylabel=ylabel,title=title);ax.grid(alpha=.16)
        fig.savefig(ROOT/(PREFIX+name+".png"),dpi=160);plt.close(fig)


def main():
    case=json.loads((ROOT/(PREFIX+"CaseStudyInputs.json")).read_text(encoding="utf-8"))
    result=calculate_case(case); rows=verification_rows(); plots=plot_data(case)
    if not all(r["passed"] for r in rows):raise AssertionError([r for r in rows if not r["passed"]])
    for name,data in (("CaseStudyResults",result),("PlotData",plots),("Verification",dict(status="PASS",checks=rows,published_examples=connections.published_examples()))):
        (ROOT/(PREFIX+name+".json")).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    with (ROOT/(PREFIX+"Verification.csv")).open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    for key,values in plots.items():
        with (ROOT/(PREFIX+key.title()+"Results.csv")).open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(values[0]));w.writeheader();w.writerows(values)
    vectors=[]
    for name,module in MODULES.items():
        vectors.extend(dict(module=name,**v) for v in module.parity_cases())
    invalid=[
        ("connections","embedment",dict(rho_k=350,d=0,fastener="bolt")),
        ("connections","embedment",dict(rho_k=-1,d=12,fastener="bolt")),
        ("connections","embedment",dict(rho_k=350,d=12,fastener="bolt",alpha_deg=91)),
        ("connections","yield_moment",dict(d=12,fu_k=-400,fastener="bolt")),
        ("materials","kmod",dict(load_duration="short",service_class=3,material_type="osb3")),
        ("fire","char_depth",dict(time_min=-1,beta_0_mm_min=.65,beta_n_mm_min=.8)),
        ("fire","section",dict(width_mm=45,depth_mm=145,time_min=30,beta_n_mm_min=.8,exposed_faces=["unknown"])),
        ("racking","geometry",dict(sheet_width_mm=0,wall_height_mm=2700)),
        ("seismic","seismic_coefficient",dict(alpha=.2,soil_factor=1.15,z_m=12,H_m=0,Ta_s=.05,T1_s=.5)),
        ("seismic","facade_behaviour_factor",dict(q_a=2.01)),
        ("seismic","bracket_forces",dict(force_kN=.578,load_shares=[.4,.4])),
    ]
    for name,op,values in invalid:
        try:MODULES[name].evaluate(op,values)
        except (ValueError,TypeError):vectors.append(dict(module=name,operation=op,inputs=values,expectedError=True))
        else:raise AssertionError(f"Invalid input was accepted: {name}/{op}")
    (ROOT/(PREFIX+"ParityVectors.json")).write_text(json.dumps(vectors,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    figures(plots)
    print(json.dumps(dict(verification="PASS",benchmarks=len(rows),parity_vectors=len(vectors),case_status=result["status"],input_sha256=hashlib.sha256((ROOT/(PREFIX+"CaseStudyInputs.json")).read_bytes()).hexdigest()),indent=2))


if __name__=="__main__":main()
