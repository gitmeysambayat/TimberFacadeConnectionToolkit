"""Educational dowel-type connection calculations, not a design approval.

AI-assisted implementation, 18 October 2026. N, mm, MPa, kg/m3.
Formulae were visually checked in the opened sources listed in SOURCES.
Every Johansen capacity is per fastener PER SHEAR PLANE. The caller must
not multiply a double-shear result twice and then multiply shear_planes again.
Unknown geometry/product resistance is never silently treated as a pass.
"""
from __future__ import annotations
import math

SOURCES = {
    "SW2_2022_UK": {
        "title": "Swedish Wood, Design of timber structures, Volume 2, UK edition 1:2022",
        "url": "https://www.universityofgalway.ie/media/timberengineeringresearchgroup/Design-of-timber-structures_Volume2_Rules-and-formulas-according-to-Eurocode-5.pdf",
        "pages": "33, 36-46", "opened": "2026-10-18",
    },
    "SW3_2022": {
        "title": "Swedish Wood, Design of timber structures, Volume 3, edition 3:2022",
        "url": "https://www.svenskttra.se/siteassets/5-publikationer/pdfer/sw-design-of-timber-structures-vol3-2022.pdf",
        "pages": "20-24, Examples 4.1 and 4.2", "opened": "2026-10-18",
    },
    "EC5_PUBLIC_2004_A1": {
        "title": "Public copy of BS EN 1995-1-1:2004+A1:2008, clause cross-check",
        "url": "https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.1.2004.pdf",
        "pages": "19-20, 52, 58-64, 71-74", "opened": "2026-10-18",
        "limitation": "Publicly hosted copy, not a current national standard service; no current-edition compliance claim.",
    },
}
ROPE_CAPS = {"nail_round": .15, "nail_square": .25, "nail_grooved": .25,
             "nail_other": .50, "screw": 1., "bolt": .25, "dowel": 0.}
SPACING_KEYS = ("a1", "a2", "a3_t", "a3_c", "a4_t", "a4_c")


def _positive(value, name):
    if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return float(value)


def _nonnegative(value, name):
    if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return float(value)


def _angle(alpha_deg):
    a = _nonnegative(alpha_deg, "alpha_deg")
    if a > 90:
        raise ValueError("alpha_deg is the principal load-to-grain angle, 0 to 90 degrees")
    return math.radians(a)


def _base(data, clause, source_ids=None, warnings=None):
    return dict(data, status="VERIFIED_FORMULA", clause=clause,
                source_ids=source_ids or ["SW2_2022_UK"], warnings=list(warnings or []))


def embedment_strength(rho_k, d, fastener="bolt", alpha_deg=0., predrilled=False, wood_type="softwood", nominal_d=None):
    """EN 1995-1-1 8.3.1.1 or 8.5.1.1; SW2 pp41/44.

    Nail embedment is angle-independent in the stated d<=8 mm rule.
    The angle correction is for bolts/dowels and screws using bolt rules.
    For smooth-shank screws d is the effective diameter; REQUIRED nominal_d selects
    the rule family at 6 mm (SW2 p46, EN 8.7.1). The supported conventional
    geometry has effective diameter no greater than nominal diameter.
    """
    rho_k=_positive(rho_k,"rho_k"); d=_positive(d,"d"); a=_angle(alpha_deg)
    rule_d=d
    if fastener=="screw":
        if nominal_d is None:raise ValueError("REQUIRED: screw nominal_d selects the 6 mm rule; d is the effective diameter")
        rule_d=_positive(nominal_d,"nominal_d")
        if d>rule_d:raise ValueError("UNVERIFIED: screw effective d must not exceed nominal_d in the supported geometry")
        if rule_d>30:raise ValueError("UNVERIFIED: screw nominal diameter is limited to 30 mm in this formula wrapper")
    if fastener.startswith("nail") or (fastener=="screw" and rule_d<=6):
        if d>8: raise ValueError("UNVERIFIED: nail embedment rule is limited to d <= 8 mm")
        if not predrilled and (rho_k>500 or d>6):
            raise ValueError("Pre-drilling required for rho_k > 500 kg/m3 or d > 6 mm")
        fh0=.082*rho_k*((1-.01*d) if predrilled else d**(-.3))
        return _base(dict(fh0_k=fh0,fh_k=fh0,k90=None),"EN1995-1-1 8.3.1.1; SW2 p41")
    if fastener not in ("bolt","dowel","screw"):raise ValueError("Unsupported fastener")
    if d>30:raise ValueError("UNVERIFIED: bolt/dowel embedment rule limited to d <= 30 mm")
    offsets={"softwood":1.35,"lvl":1.30,"hardwood":.90}
    if wood_type not in offsets:raise ValueError("wood_type must be softwood, lvl or hardwood")
    k90=offsets[wood_type]+.015*d; fh0=.082*(1-.01*d)*rho_k
    return _base(dict(fh0_k=fh0,fh_k=fh0/(k90*math.sin(a)**2+math.cos(a)**2),k90=k90),
                 "EN1995-1-1 8.5.1.1(2)-(3), Eqs8.31-8.33; SW2 p44")


def panel_embedment_strength(d, t_panel, panel="osb", rho_k=None, head_d=None):
    """EN 8.3.1.3; head diameter >=2d is an applicability condition."""
    d=_positive(d,"d"); t=_positive(t_panel,"t_panel")
    if d>8:raise ValueError("UNVERIFIED: nail panel rule limited to d <= 8 mm")
    if panel in ("osb","particleboard"): fh=65*d**(-.7)*t**.1
    elif panel=="hardboard":fh=30*d**(-.3)*t**.6
    elif panel=="plywood":fh=.11*_positive(rho_k,"rho_k")*d**(-.3)
    else:raise ValueError("Unsupported panel")
    warnings=[]
    if head_d is None:warnings.append("REQUIRED: nail head diameter to verify head_d >= 2d")
    elif _positive(head_d,"head_d") < 2*d:warnings.append("FAIL: head diameter is below the formula applicability condition 2d")
    out=_base(dict(fh_k=fh,applicability_verified=not warnings),"EN1995-1-1 8.3.1.3; SW2 p41",warnings=warnings)
    if warnings:out["status"]="UNVERIFIED"
    return out


def yield_moment(d, fu_k, fastener="bolt", My_Rk_override=None):
    """SW2 pp40/44; smooth nail formula needs fu>=600 MPa.

    Other/proprietary nails need a declared/tested yield moment. Passing a
    grooved cross-section formula does not change an annular nail's rope cap.
    A screw caller must supply its applicable effective diameter, not assume it.
    """
    d=_positive(d,"d"); fu=_positive(fu_k,"fu_k")
    if My_Rk_override is not None:
        return _base(dict(My_Rk=_positive(My_Rk_override,"My_Rk_override"),coefficient=None),
                     "DECLARED_INPUT; not calculated from an unverified product formula",warnings=["Yield moment is a caller-supplied declared input"])
    if fastener in ("bolt","dowel","screw"):coefficient=.3; clause="EN1995-1-1 8.5.1.1(1), Eq8.30; SW2 p44"
    elif fastener in ("nail_round","nail_square","nail_grooved"):
        if fu<600:raise ValueError("UNVERIFIED: smooth nail formula requires fu_k >= 600 MPa")
        coefficient=.3 if fastener=="nail_round" else .45
        clause="EN1995-1-1 8.3.1.1(4); SW2 p40"
    else:raise ValueError("UNVERIFIED: declared My_Rk_override required for this fastener")
    return _base(dict(My_Rk=coefficient*fu*d**2.6,coefficient=coefficient),clause)


def _mode_result(values, rope_modes, fastener, Fax_Rk, planes, clause):
    if fastener not in ROPE_CAPS:raise ValueError("Unsupported rope-effect fastener category")
    fax=0. if Fax_Rk is None else _nonnegative(Fax_Rk,"Fax_Rk")
    cap=ROPE_CAPS[fastener]; modes={}
    for name,base in values.items():
        rope=min(fax/4,cap*base) if name in rope_modes else 0.
        modes[name]=dict(johansen_N=base,rope_N=rope,Fv_Rk_N=base+rope)
    governing=min(modes,key=lambda k:modes[k]["Fv_Rk_N"])
    f=modes[governing]["Fv_Rk_N"]
    notes=["Rope effect neglected; axial resistance is not established"] if fax==0 else []
    return _base(dict(modes=modes,governing_mode=governing,Fv_Rk_N=f,
                      shear_planes=planes,per_fastener_total_N=f*planes,rope_cap_fraction=cap),clause,warnings=notes)


def timber_to_timber_modes(d,t1,t2,fh1_k,fh2_k,My_Rk,shear="single",fastener="bolt",Fax_Rk=None):
    """All Eq8.6 a-f / Eq8.7 g,h,j,k modes; SW2 pp36-38.

    Double shear assumes equivalent outer timber members; t1 is the controlling
    outer thickness/penetration and t2 the central timber thickness.
    """
    d=_positive(d,"d");t1=_positive(t1,"t1");t2=_positive(t2,"t2")
    f1=_positive(fh1_k,"fh1_k");f2=_positive(fh2_k,"fh2_k");my=_positive(My_Rk,"My_Rk")
    b=f2/f1;r=t2/t1
    hinge1=1.05*f1*t1*d/(2+b)*(math.sqrt(2*b*(1+b)+4*b*(2+b)*my/(f1*d*t1*t1))-b)
    hinge2=1.15*math.sqrt(2*b/(1+b))*math.sqrt(2*my*f1*d)
    if shear=="single":
        values={"a":f1*t1*d,"b":f2*t2*d,
                "c":f1*t1*d/(1+b)*(math.sqrt(b+2*b*b*(1+r+r*r)+b**3*r*r)-b*(1+r)),
                "d":hinge1,
                "e":1.05*f1*t2*d/(1+2*b)*(math.sqrt(2*b*b*(1+b)+4*b*(1+2*b)*my/(f1*d*t2*t2))-b),
                "f":hinge2}
        return _mode_result(values,{"c","d","e","f"},fastener,Fax_Rk,1,"EN1995-1-1 8.2.2 Eq8.6; SW2 pp36-38")
    if shear=="double":
        return _mode_result({"g":f1*t1*d,"h":.5*f2*t2*d,"j":hinge1,"k":hinge2},
                            {"j","k"},fastener,Fax_Rk,2,"EN1995-1-1 8.2.2 Eq8.7; SW2 pp37-38")
    raise ValueError("shear must be single or double")


def steel_to_timber_modes(d,t1,fh_k,My_Rk,t_steel,configuration="single",fastener="bolt",Fax_Rk=None,hole_tolerance_mm=None):
    """All Eq8.9-8.13 modes; steel strength is a separate required check.

    For central steel t1 is the smaller timber side thickness/penetration.
    For outer steel t1 denotes the full central timber thickness (EN t2).
    Interpolate the LIMITING CAPACITIES, not arbitrary paired Johansen modes.
    Thick/intermediate plate applicability remains UNVERIFIED without hole fit.
    """
    d=_positive(d,"d");t=_positive(t1,"t1");fh=_positive(fh_k,"fh_k")
    my=_positive(My_Rk,"My_Rk");ts=_positive(t_steel,"t_steel")
    bend=fh*t*d*(math.sqrt(2+4*my/(fh*d*t*t))-1)
    m2=2.3*math.sqrt(my*fh*d);m1=1.15*math.sqrt(2*my*fh*d)
    if configuration=="central":
        return _mode_result({"f":fh*t*d,"g":bend,"h":m2},{"g","h"},fastener,Fax_Rk,2,
                            "EN1995-1-1 8.2.3 Eq8.11; SW2 p38")
    if configuration=="single":
        thin=_mode_result({"a":.4*fh*t*d,"b":m1},{"b"},fastener,Fax_Rk,1,"EN1995-1-1 8.2.3 Eq8.9; SW2 p38")
        thick=_mode_result({"c":fh*t*d,"d":bend,"e":m2},{"d","e"},fastener,Fax_Rk,1,"EN1995-1-1 8.2.3 Eq8.10; SW2 p38")
    elif configuration=="outer":
        thin=_mode_result({"j":.5*fh*t*d,"k":m1},{"k"},fastener,Fax_Rk,2,"EN1995-1-1 8.2.3 Eq8.12; SW2 p39")
        thick=_mode_result({"l":.5*fh*t*d,"m":m2},{"m"},fastener,Fax_Rk,2,"EN1995-1-1 8.2.3 Eq8.13; SW2 p39")
    else:raise ValueError("configuration must be single, central or outer")
    if ts<=.5*d:
        out=thin;out["plate_class"]="thin";out["interpolation_fraction"]=0.
        out["applicability_verified"]=True
        return out
    fit_ok=hole_tolerance_mm is not None and _nonnegative(hole_tolerance_mm,"hole_tolerance_mm")<.1*d-1e-12*max(1.,d)
    if ts>=d:
        out=thick;out["plate_class"]="thick";out["interpolation_fraction"]=1.
    else:
        eta=(ts-.5*d)/(.5*d);fv=(1-eta)*thin["Fv_Rk_N"]+eta*thick["Fv_Rk_N"]
        out=_base(dict(modes={**{"thin_"+k:v for k,v in thin["modes"].items()},**{"thick_"+k:v for k,v in thick["modes"].items()}},
                       governing_mode="interpolation("+thin["governing_mode"]+","+thick["governing_mode"]+")",
                       Fv_Rk_N=fv,shear_planes=thin["shear_planes"],per_fastener_total_N=fv*thin["shear_planes"],
                       rope_cap_fraction=ROPE_CAPS[fastener],plate_class="intermediate",interpolation_fraction=eta,
                       thin_capacity_N=thin["Fv_Rk_N"],thick_capacity_N=thick["Fv_Rk_N"]),
                  "EN1995-1-1 8.2.3(1), Eqs8.9-8.13; SW2 pp38-39",warnings=thin["warnings"])
    out["applicability_verified"]=fit_ok
    if not fit_ok:
        out["status"]="UNVERIFIED"
        out["warnings"].append("REQUIRED: thick-plate limiting case needs hole-diameter tolerance < 0.1d")
    return out


def nail_kef(a1,d,predrilled=False):
    """EN8.3.1.1 Table8.1 / SW2 Table10.1, linear interpolation."""
    ratio=_positive(a1,"a1")/_positive(d,"d")
    points=[(5.,.5),(7.,.7),(10.,.85),(14.,1.)] if predrilled else [(7.,.7),(10.,.85),(14.,1.)]
    if ratio<points[0][0]:raise ValueError("UNVERIFIED: spacing is outside the verified nail kef table")
    value=1.
    for (x0,y0),(x1,y1) in zip(points,points[1:]):
        if x0<=ratio<=x1:value=y0+(ratio-x0)*(y1-y0)/(x1-x0);break
    return _base(dict(kef=value,a1_over_d=ratio),"EN1995-1-1 8.3.1.1 Table8.1; SW2 p41 Table10.1")


def effective_number(n,a1,d,fastener="bolt",alpha_deg=0.,predrilled=False,staggered=False):
    n=_positive(n,"n");d=_positive(d,"d");a=_angle(alpha_deg)
    if int(n)!=n:raise ValueError("n is a positive integer count in one row")
    if n==1:return _base(dict(n_eff=1.,n_eff_parallel=1.,kef=None),"Single fastener; no group reduction")
    a1=_positive(a1,"a1")
    if fastener in ("bolt","dowel") or (fastener=="screw" and d>6):
        parallel=min(n,n**.9*(a1/(13*d))**.25)
        neff=parallel+(n-parallel)*(math.degrees(a)/90.)
        return _base(dict(n_eff=neff,n_eff_parallel=parallel,kef=None),"EN1995-1-1 8.5.1.1(4), Eq8.34; SW2 p45")
    if fastener.startswith("nail") or (fastener=="screw" and d<=6):
        kef=nail_kef(a1,d,predrilled)["kef"]
        if staggered or alpha_deg==90:neff=n
        elif alpha_deg==0:neff=n**kef
        else:
            return dict(n_eff=None,n_eff_parallel=n**kef,kef=kef,status="UNVERIFIED",
                        clause="EN1995-1-1 8.3.1.1; SW2 p41",source_ids=["SW2_2022_UK"],
                        warnings=["Nail group rule verified for parallel/perpendicular loading; no intermediate-angle interpolation assumed"])
        return _base(dict(n_eff=neff,n_eff_parallel=n**kef,kef=kef),"EN1995-1-1 8.3.1.1; SW2 p41")
    raise ValueError("Unsupported fastener")


def minimum_spacings(d,fastener="bolt",alpha_deg=0.,rho_k=None,predrilled=False,connection_type="timber"):
    """Principal angle 0-90deg. Unloaded-end table evaluated at 180-alpha.

    Returned a3/a4 values refer to the identified loaded/unloaded sides.
    Nail panel/steel reductions affect a1/a2 ONLY, never end/edge distances.
    """
    d=_positive(d,"d");a=_angle(alpha_deg);c=math.cos(a);s=math.sin(a)
    f="bolt" if fastener=="screw" and d>6 else ("nail_round" if fastener=="screw" else fastener)
    if f=="bolt":
        vals=dict(a1=(4+c)*d,a2=4*d,a3_t=max(7*d,80.),a3_c=max(4.,1+6*s)*d,a4_t=max(2+2*s,3.)*d,a4_c=3*d)
        clause="EN1995-1-1 8.5.1.1 Table8.4; SW2 p45 Table10.4"
    elif f=="dowel":
        if not 6<=d<=30:raise ValueError("UNVERIFIED: dowel spacing scope is 6 <= d <= 30 mm")
        a3t=max(7*d,80.)
        a3c=max(3.5*d,40.) if alpha_deg<=30 else a3t*s
        vals=dict(a1=(3+2*c)*d,a2=3*d,a3_t=a3t,a3_c=a3c,a4_t=max(2+2*s,3.)*d,a4_c=3*d)
        clause="EN1995-1-1 8.6, amended table; SW2 p45 Table10.5 (A2:2014)"
    elif f.startswith("nail"):
        rho=_positive(rho_k,"rho_k")
        if not predrilled and (rho>500 or d>6):raise ValueError("Pre-drilling required")
        if predrilled:
            vals=dict(a1=(4+c)*d,a2=(3+s)*d,a3_t=(7+5*c)*d,a3_c=7*d,a4_t=(3+(2 if d<5 else 4)*s)*d,a4_c=3*d)
        elif rho<=420:
            vals=dict(a1=(5+(5 if d<5 else 7)*c)*d,a2=5*d,a3_t=(10+5*c)*d,a3_c=10*d,a4_t=(5+(2 if d<5 else 5)*s)*d,a4_c=5*d)
        else:
            vals=dict(a1=(7+8*c)*d,a2=7*d,a3_t=(15+5*c)*d,a3_c=15*d,a4_t=(7+(2 if d<5 else 5)*s)*d,a4_c=7*d)
        if connection_type not in ("timber","panel","steel"):raise ValueError("Unsupported connection_type")
        factor={"timber":1.,"panel":.85,"steel":.7}[connection_type]
        vals["a1"]*=factor;vals["a2"]*=factor
        clause="EN1995-1-1 8.3.1.2 Table8.2, 8.3.1.3/4; SW2 p42 Table10.2"
    else:raise ValueError("Unsupported fastener")
    out=_base(dict(minimum_mm=vals,angle_convention="principal 0-90; unloaded end uses 180-alpha"),clause)
    if f.startswith("nail"):
        out["national_annex_status"]="UNVERIFIED: recommended EN spacing values; applicable National Annex choices not confirmed"
        out["warnings"].append("Nail spacing table is marked NDP in the opened UK handbook; caller may supply confirmed minima to check_spacings")
    return out


def check_spacings(minimum_mm,actual_mm):
    checks={};missing=[]
    for key in SPACING_KEYS:
        need=_positive(minimum_mm[key],key+" minimum");actual=actual_mm.get(key)
        if actual is None:checks[key]=dict(required_mm=need,actual_mm=None,status="UNVERIFIED");missing.append(key)
        else:
            value=_nonnegative(actual,key)
            checks[key]=dict(required_mm=need,actual_mm=value,status="PASS" if value+1e-10>=need else "FAIL")
    statuses=[x["status"] for x in checks.values()]
    overall="FAIL" if "FAIL" in statuses else ("UNVERIFIED" if missing else "PASS")
    return dict(checks=checks,status=overall,missing_inputs=missing,source_ids=["SW2_2022_UK"],
                clause="EN1995-1-1 applicable spacing table; SW2 pp42/45")


def slip_modulus(rho_m,d,fastener="bolt",predrilled=False,steel_factor=1.,rho_m2=None):
    """EN7.1 Table7.1; optional factor2 in7.1(3); Ku in2.2.2(2).

    Bolt-hole clearance displacement is additional and not hidden in Kser.
    rho_m2 allows timber-to-timber geometric-mean density, not steel density.
    """
    rho=_positive(rho_m,"rho_m");d=_positive(d,"d")
    if rho_m2 is not None:rho=math.sqrt(rho*_positive(rho_m2,"rho_m2"))
    if steel_factor not in (1,2):raise ValueError("steel_factor must be explicitly 1 or 2")
    if fastener in ("bolt","dowel","screw") or (fastener.startswith("nail") and predrilled):base=rho**1.5*d/23
    elif fastener.startswith("nail"):base=rho**1.5*d**.8/30
    else:raise ValueError("Unsupported fastener")
    k=base*steel_factor
    return _base(dict(Kser_base_N_per_mm=base,Kser_N_per_mm=k,Ku_N_per_mm=2*k/3,steel_factor=float(steel_factor),rho_m_effective=rho),
                 "EN1995-1-1 7.1 Table7.1, 7.1(3), 2.2.2(2); SW2 p33",source_ids=["SW2_2022_UK","EC5_PUBLIC_2004_A1"],
                 warnings=["Bolt-hole clearance slip must be added separately"] if fastener=="bolt" else [])


def design_capacity(Fv_Rk_N,kmod,gamma_M,n_eff=1.,shear_planes=1):
    f=_positive(Fv_Rk_N,"Fv_Rk_N");k=_positive(kmod,"kmod");g=_positive(gamma_M,"gamma_M");n=_positive(n_eff,"n_eff")
    if shear_planes not in (1,2):raise ValueError("shear_planes must be 1 or 2")
    rd=k*f/g
    return _base(dict(Fv_Rd_per_plane_N=rd,group_design_capacity_N=rd*n*shear_planes,n_eff=n,shear_planes=shear_planes,kmod=k,gamma_M=g),
                 "EN1995-1-1 2.4.1, 8.1; SW2 p36")


def connection_summary(rho_k,rho_m,d,fu_k,t1,t_steel,n,a1,kmod,gamma_M,alpha_deg=0.,Fax_Rk=0.,fastener="bolt",wood_type="softwood",steel_factor=2.,hole_tolerance_mm=None,spacing_actual=None,design_shear_N=None,anchor_capacity_N=None,**unused):
    """Illustrative bolt/dowel single-shear steel bracket, not a full check.

    Nail and screw details require separate product, penetration and diameter
    conventions. Use the individual, explicitly bounded operations instead.
    """
    if fastener not in ("bolt","dowel"):
        raise ValueError("UNVERIFIED: connection_summary supports bolt/dowel brackets only; use individual operations with the required nail/screw conventions")
    fh=embedment_strength(rho_k,d,fastener,alpha_deg,wood_type=wood_type)
    my=yield_moment(d,fu_k,fastener)
    modes=steel_to_timber_modes(d,t1,fh["fh_k"],my["My_Rk"],t_steel,"single",fastener,Fax_Rk,hole_tolerance_mm)
    ne=effective_number(n,a1,d,fastener,alpha_deg)
    design=design_capacity(modes["Fv_Rk_N"],kmod,gamma_M,ne["n_eff"],1)
    minimum=minimum_spacings(d,fastener,alpha_deg,rho_k)
    actual=dict(spacing_actual or {});actual.setdefault("a1",a1)
    if actual["a1"] is not None and not math.isclose(_positive(actual["a1"],"spacing_actual.a1"),a1,rel_tol=1e-12,abs_tol=1e-9):
        raise ValueError("a1 and spacing_actual.a1 must describe the same row spacing")
    spacing=check_spacings(minimum["minimum_mm"],actual)
    slip=slip_modulus(rho_m,d,fastener,steel_factor=steel_factor)
    missing=list(spacing["missing_inputs"])
    demand=None if design_shear_N is None else _nonnegative(design_shear_N,"design_shear_N")
    anchor=None if anchor_capacity_N is None else _positive(anchor_capacity_N,"anchor_capacity_N")
    if demand is None:missing.append("design_shear_N")
    if anchor is None:missing.append("anchor_capacity_N from applicable ETA")
    utilisation=None if demand is None else demand/design["group_design_capacity_N"]
    anchor_utilisation=None if demand is None or anchor is None else demand/anchor
    fails=spacing["status"]=="FAIL" or (utilisation is not None and utilisation>1) or (anchor_utilisation is not None and anchor_utilisation>1)
    components={"embedment":fh,"yield_moment":my,"modes":modes,"effective_number":ne,"minimum_spacings":minimum,"slip":slip}
    unverified=[name for name,result in components.items() if result["status"]=="UNVERIFIED"]
    if minimum.get("national_annex_status","").startswith("UNVERIFIED"):
        missing.append("applicable National Annex spacing choice")
    status="FAIL" if fails else ("UNVERIFIED" if missing or unverified else "PASS_IN_SCOPE")
    return dict(status=status,embedment=fh,yield_moment=my,modes=modes,effective_number=ne,design=design,slip=slip,
                spacing=spacing,minimum_spacings=minimum,design_shear_N=demand,utilisation=utilisation,anchor_utilisation=anchor_utilisation,
                missing_inputs=missing,unverified_components=unverified,source_ids=["SW2_2022_UK","EC5_PUBLIC_2004_A1"],
                excluded_checks=["Steel plate/fastener steel resistance", "Timber splitting, block/plug shear and net section", "Combined axial/lateral action and eccentricity", "Bracket bending, prying and actual load path", "Concrete anchor-group and substrate verification", "Cyclic, fire, moisture and long-term behaviour"],
                warnings=["Educational calculation, not for design", "Load angle and timber penetration are illustrative inputs", "Rope effect explicitly neglected when Fax_Rk is zero"])


OPERATIONS={"embedment":embedment_strength,"panel_embedment":panel_embedment_strength,"yield_moment":yield_moment,
            "timber_modes":timber_to_timber_modes,"steel_modes":steel_to_timber_modes,"nail_kef":nail_kef,
            "effective_number":effective_number,"minimum_spacings":minimum_spacings,"check_spacings":check_spacings,
            "slip_modulus":slip_modulus,"design_capacity":design_capacity,"connection_summary":connection_summary}


def evaluate(operation,inputs):
    if operation not in OPERATIONS:raise ValueError("Unknown connection operation")
    return OPERATIONS[operation](**inputs)


def published_examples():
    """Reproduce published subcalculations, not certify either full detail.

    4.1: manufacturer effective diameter assumed by book, rope neglected, n=12
    multiplication follows book without a newly asserted group/layout check.
    4.2: annular nail My uses the book's explicitly simplified grooved formula;
    Fax=383 N is the book's limiting rounded input. Product values still needed.
    Both use gammaM=1.3; kmod .65 (SC3/M) and .8 (SC2/M), not case wind .9.
    """
    fh=embedment_strength(390,8,"screw",45,nominal_d=8)["fh_k"];my=yield_moment(8,410,"screw")["My_Rk"]
    one=steel_to_timber_modes(8,52,fh,my,8,fastener="screw",Fax_Rk=0,hole_tolerance_mm=0.)
    one_design=design_capacity(one["Fv_Rk_N"],.65,1.3,12)
    fhn=embedment_strength(390,4,"nail_other")["fh_k"];myn=yield_moment(4,600,"nail_grooved")["My_Rk"]
    two=steel_to_timber_modes(4,35,fhn,myn,5,fastener="nail_other",Fax_Rk=383.,hole_tolerance_mm=0.)
    two_no_rope=steel_to_timber_modes(4,35,fhn,myn,5,fastener="nail_other",Fax_Rk=0.,hole_tolerance_mm=0.)
    two_design=design_capacity(two["Fv_Rk_N"],.8,1.3)
    return [dict(id="SW3_4_1",published_Fv_Rk_N=4830.,toolkit_Fv_Rk_N=one["Fv_Rk_N"],published_total_design_N=29000.,toolkit_total_design_N=one_design["group_design_capacity_N"],modes=one["modes"],kmod=.65,gamma_M=1.3,source_ids=["SW3_2022","SW2_2022_UK"],notes="Book assumes effective screw diameter8mm, adequate geometry and thick steel support; hole fit assumed for reproduction. Total12 multiplication follows book, not a separate layout verification."),
            dict(id="SW3_4_2",published_no_rope_N=1607.,toolkit_no_rope_N=two_no_rope["Fv_Rk_N"],published_with_rope_N=1700.,toolkit_with_rope_N=two["Fv_Rk_N"],published_design_N=1050.,toolkit_design_N=two_design["Fv_Rd_per_plane_N"],modes=two["modes"],kmod=.8,gamma_M=1.3,source_ids=["SW3_2022","SW2_2022_UK"],notes="Book applies simplified grooved-nail yield formula to annular nails; other-nail50percent rope cap and rounded Fax383N. Hole fit assumed; no complete Gerber/steel/splitting design.")]


def parity_cases():
    """Public numerical vectors for independent JavaScript parity integration."""
    cases=[]
    def add(op,**inputs):cases.append(dict(operation=op,inputs=inputs,expected=evaluate(op,inputs)))
    for fastener in ("bolt","dowel","screw"):
        for angle in (0,45,90):add("embedment",rho_k=350,d=12,fastener=fastener,alpha_deg=angle,**({"nominal_d":12} if fastener=="screw" else {}))
    add("embedment",rho_k=350,d=5.5,fastener="screw",nominal_d=8,alpha_deg=45)
    add("embedment",rho_k=350,d=4,fastener="screw",nominal_d=5,alpha_deg=90)
    for pre in (False,True):
        add("embedment",rho_k=350,d=2.8,fastener="nail_round",predrilled=pre)
        add("slip_modulus",rho_m=420,d=2.8,fastener="nail_round",predrilled=pre)
    for f in ("bolt","dowel","nail_round","nail_square","nail_grooved","screw"):
        add("yield_moment",d=4 if f.startswith("nail") else 12,fu_k=600 if f.startswith("nail") else 400,fastener=f)
    for sh in ("single","double"):
        for f in ROPE_CAPS:add("timber_modes",d=12,t1=45,t2=80,fh1_k=25.256,fh2_k=30.,My_Rk=76700.,shear=sh,fastener=f,Fax_Rk=5000.)
    for config in ("single","central","outer"):
        for ts in (5.9,6.,9.,12.,12.1):
            add("steel_modes",d=12,t1=45,fh_k=25.256,My_Rk=76700.,t_steel=ts,configuration=config,fastener="bolt",Fax_Rk=5000.,hole_tolerance_mm=.1)
    for count in (1,2,5):
        for angle in (0,45,90):add("effective_number",n=count,a1=84,d=12,alpha_deg=angle)
    for ratio in (7,8.5,10,12,14,20):add("nail_kef",a1=ratio*2.8,d=2.8)
    add("nail_kef",a1=14.,d=2.8,predrilled=True)
    for f in ("bolt","dowel","nail_round"):
        for angle in (0,45,90):add("minimum_spacings",d=12 if f!="nail_round" else 2.8,fastener=f,alpha_deg=angle,rho_k=350)
    add("panel_embedment",d=2.8,t_panel=15,panel="osb",head_d=5.6)
    add("panel_embedment",d=2.8,t_panel=15,panel="osb")
    add("steel_modes",d=12,t1=45,fh_k=25.256,My_Rk=76700.,t_steel=12)
    add("effective_number",n=5,a1=28.,d=2.8,fastener="nail_round",alpha_deg=45.)
    mins=minimum_spacings(12)["minimum_mm"]
    add("check_spacings",minimum_mm=mins,actual_mm=mins)
    add("check_spacings",minimum_mm=mins,actual_mm={"a1":84.})
    add("check_spacings",minimum_mm=mins,actual_mm=dict(mins,a3_t=83.))
    for factor in (1,2):add("slip_modulus",rho_m=420,d=12,steel_factor=factor)
    add("design_capacity",Fv_Rk_N=5455.296,kmod=.9,gamma_M=1.3,n_eff=1.6)
    add("connection_summary",rho_k=350,rho_m=420,d=12,fu_k=400,t1=45,t_steel=6,n=2,a1=84,kmod=.9,gamma_M=1.3)
    bracket=dict(rho_k=350,rho_m=420,d=12,fu_k=400,t1=45,t_steel=6,n=2,a1=84,kmod=.9,gamma_M=1.3)
    for operation,inputs in [
        ("embedment",dict(rho_k=350,d=5.5,fastener="screw")),
        ("embedment",dict(rho_k=350,d=8,fastener="screw",nominal_d=6)),
        ("connection_summary",dict(bracket,fastener="screw")),
        ("connection_summary",dict(bracket,fastener="nail_round")),
        ("connection_summary",dict(bracket,spacing_actual={"a1":200.})),
    ]:
        try:evaluate(operation,inputs)
        except ValueError:cases.append(dict(operation=operation,inputs=inputs,expectedError=True))
        else:raise AssertionError("Invalid parity input was unexpectedly accepted")
    return cases
