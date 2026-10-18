"""Unprotected isolated-member reduced cross-section educational calculations.

Not for design. Standard fire only. Protected members, void/insulated wall
assemblies and Annex C are outside scope. No fire action is fabricated.
Primary source opened and visually read 18 October 2026: BS EN 1995-1-2:2004
including June 2006/March 2009 corrigenda, public copy linked below.
"""
from math import isfinite
from numbers import Real

SOURCE_URL = "https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.2.2004.pdf"
CLAUSES = {
    "charring": "EN 1995-1-2:2004 3.4.2, Equations (3.1)-(3.2), Table 3.1; printed pp.21-23",
    "effective": "EN 1995-1-2:2004 4.2.2, Equation (4.1), Table 4.1; printed pp.30-31",
    "strength": "EN 1995-1-2:2004 2.3, Equations (2.1),(2.4), Table 2.1; printed pp.15-16",
    "kmod_fi": "EN 1995-1-2:2004 4.2.2(5); printed p.31",
    "gamma_M_fi": "EN 1995-1-2:2004 2.3(1) Note 2; recommended NDP, printed p.15",
    "section": "Elementary rectangular-section geometry applied to EN 1995-1-2 4.2.2 effective section",
    "bending": "EN 1995-1-2:2004 4.1/4.2.2 and EN 1995-1-1 6.1.6; uniaxial section bending only, stability excluded",
}
_FACES = ("width_left", "width_right", "depth_front", "depth_back")


def _number(name, value, *, positive=False, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise ValueError(f"{name} must be a finite real number")
    if positive and value <= 0:
        raise ValueError(f"{name} must be positive")
    if nonnegative and value < 0:
        raise ValueError(f"{name} must be non-negative")
    return float(value)


def fire_parameters(material_type, rho_k_kg_m3):
    """Verified softwood/glulam/LVL rows only, with their density conditions."""
    rho = _number("rho_k_kg_m3", rho_k_kg_m3, positive=True)
    if material_type == "solid_softwood" and rho >= 290:
        beta_n, kfi = 0.8, 1.25
    elif material_type == "glulam_softwood" and rho >= 290:
        beta_n, kfi = 0.7, 1.15
    elif material_type == "lvl" and rho >= 480:
        beta_n, kfi = 0.7, 1.10
    else:
        raise ValueError("UNVERIFIED charring-rate applicability for this material/density")
    return dict(beta_0_mm_min=0.65, beta_n_mm_min=beta_n, kfi=kfi,
                kmod_fi=1.0, gamma_M_fi_recommended=1.0,
                gamma_status="RECOMMENDED_NDP_NOT_NATIONAL_ANNEX_VERIFIED",
                source_url=SOURCE_URL, source=CLAUSES["charring"] + "; " + CLAUSES["strength"])


def charring_depths(time_min, beta_0_mm_min, beta_n_mm_min, d0_mm=7.0):
    """3.4.2 Eqs 3.1/3.2; 4.2.2 Eq4.1/Table4.1, unprotected surfaces."""
    t = _number("time_min", time_min, nonnegative=True)
    b0 = _number("beta_0_mm_min", beta_0_mm_min, positive=True)
    bn = _number("beta_n_mm_min", beta_n_mm_min, positive=True)
    d0 = _number("d0_mm", d0_mm, positive=True)
    if d0 != 7.0:
        raise ValueError("This verified 2004 reduced-section method requires d0_mm = 7")
    k0 = min(t / 20.0, 1.0)
    return dict(time_min=t, dchar_0_mm=b0*t, dchar_n_mm=bn*t,
                k0=k0, d0_mm=d0, effective_char_depth_mm=bn*t+k0*d0,
                source=CLAUSES["charring"] + "; " + CLAUSES["effective"])


def effective_char_depth(time_min, beta_n_mm_min):
    """Convenience scalar with verified d0=7, unprotected k0=min(t/20,1)."""
    t = _number("time_min", time_min, nonnegative=True)
    bn = _number("beta_n_mm_min", beta_n_mm_min, positive=True)
    return bn*t + min(t/20.0, 1.0)*7.0


def reduced_section_rectangular(width_mm, depth_mm, time_min, beta_n_mm_min,
                                exposed_faces, beta_0_mm_min=0.65, d0_mm=7.0,
                                protected=False, insulated_assembly=False):
    """Face names state which dimension is reduced, preventing 45/145 confusion.

    depth_front/back reduce depth, width_left/right reduce width. The y axis
    has I_y = b*h^3/12 and W_y=b*h^2/6, where b is width and h is depth.
    Centroid shifts are returned, but applied actions must be referred to the
    effective-section centroid. Original-axis eccentric compression is not
    treated as concentric loading after one-sided section loss.
    """
    b = _number("width_mm", width_mm, positive=True)
    h = _number("depth_mm", depth_mm, positive=True)
    if protected is not False or insulated_assembly is not False:
        raise ValueError("Protected members and insulated assemblies are OUT_OF_SCOPE")
    if not isinstance(exposed_faces, (list, tuple)) or not exposed_faces:
        raise ValueError("exposed_faces requires at least one explicit face")
    if len(set(exposed_faces)) != len(exposed_faces) or any(face not in _FACES for face in exposed_faces):
        raise ValueError("Use unique explicit width_left/right or depth_front/back face names")
    char = charring_depths(time_min, beta_0_mm_min, beta_n_mm_min, d0_mm)
    de, dn = char["effective_char_depth_mm"], char["dchar_n_mm"]
    nw = sum(face.startswith("width_") for face in exposed_faces)
    nh = sum(face.startswith("depth_") for face in exposed_faces)
    be, he = max(0.0, b-nw*de), max(0.0, h-nh*de)
    br, hr = max(0.0, b-nw*dn), max(0.0, h-nh*dn)
    exhausted = be == 0 or he == 0
    return dict(**char, width_mm=b, depth_mm=h, exposed_faces=list(exposed_faces),
        residual_width_mm=br, residual_depth_mm=hr,
        effective_width_mm=be, effective_depth_mm=he,
        effective_area_mm2=be*he,
        I_y_mm4=be*he**3/12.0, W_y_mm3=be*he**2/6.0,
        I_z_mm4=he*be**3/12.0, W_z_mm3=he*be**2/6.0,
        centroid_shift_width_mm=None if exhausted else (float("width_left" in exposed_faces)-float("width_right" in exposed_faces))*de/2.0,
        centroid_shift_depth_mm=None if exhausted else (float("depth_front" in exposed_faces)-float("depth_back" in exposed_faces))*de/2.0,
        status="SECTION_EXHAUSTED" if exhausted else "SECTION_ONLY_NOT_FIRE_RESISTANCE_APPROVAL",
        orientation="depth_front/back reduce depth; width_left/right reduce width; y bending uses width*depth^2/6",
        limitations=["Isolated unprotected member under standard fire only", "No protected or insulated assembly assessment", "No fire actions, stability, connection fire check or separating-function classification"])


def check_fire_bending(section, design_bending_moment_Nmm, fm_k_MPa, *, kfi,
                       gamma_M_fi, kmod_fi, axis="y"):
    """Uniaxial elastic section check only; no fire moment is assumed."""
    if axis not in ("y", "z"):
        raise ValueError("axis must be explicitly y or z")
    required = [name for name, value in [("design_bending_moment_Nmm", design_bending_moment_Nmm),
                ("fm_k_MPa", fm_k_MPa), ("kfi", kfi), ("gamma_M_fi", gamma_M_fi), ("kmod_fi", kmod_fi)] if value is None]
    if required:
        return dict(status="REQUIRED_INPUT", required_inputs=required, utilisation=None,
                    capacity_Nmm=None, passed=None, source=CLAUSES["bending"])
    demand = abs(_number("design_bending_moment_Nmm", design_bending_moment_Nmm))
    fk = _number("fm_k_MPa", fm_k_MPa, positive=True)
    kf = _number("kfi", kfi, positive=True)
    gm = _number("gamma_M_fi", gamma_M_fi, positive=True)
    km = _number("kmod_fi", kmod_fi, positive=True)
    if km != 1.0:
        raise ValueError("Verified reduced cross-section method requires kmod_fi = 1.0")
    W = _number("section modulus", section[f"W_{axis}_mm3"], nonnegative=True)
    fd = km*kf*fk/gm
    if W == 0:
        return dict(status="SECTION_EXHAUSTED", capacity_Nmm=0.0, utilisation=None,
                    passed=False, fd_fi_MPa=fd, demand_Nmm=demand, source=CLAUSES["bending"])
    cap = fd*W
    return dict(status="SECTION_BENDING_ONLY", capacity_Nmm=cap,
                utilisation=demand/cap, passed=demand <= cap, fd_fi_MPa=fd,
                demand_Nmm=demand, axis=axis,
                source=CLAUSES["strength"] + "; " + CLAUSES["kmod_fi"] + "; " + CLAUSES["bending"],
                limitations=["No beam stability or combined-action check", "No fire-action combination is generated", "Not a fire-resistance time rating"])


def evaluate(operation, inputs):
    if operation == "parameters":
        return fire_parameters(inputs["material_type"], inputs["rho_k_kg_m3"])
    if operation == "char_depth":
        return charring_depths(inputs["time_min"], inputs["beta_0_mm_min"], inputs["beta_n_mm_min"], inputs.get("d0_mm", 7.0))
    if operation == "section":
        return reduced_section_rectangular(inputs["width_mm"], inputs["depth_mm"], inputs["time_min"], inputs["beta_n_mm_min"], inputs["exposed_faces"],
                inputs.get("beta_0_mm_min", 0.65), inputs.get("d0_mm", 7.0), inputs.get("protected", False), inputs.get("insulated_assembly", False))
    if operation == "bending":
        section = inputs.get("section") or evaluate("section", inputs)
        return check_fire_bending(section, inputs.get("design_bending_moment_Nmm"), inputs.get("fm_k_MPa"),
                kfi=inputs.get("kfi"), gamma_M_fi=inputs.get("gamma_M_fi"), kmod_fi=inputs.get("kmod_fi"), axis=inputs.get("axis", "y"))
    raise ValueError("Unknown fire operation")


def parity_cases():
    base = dict(width_mm=45.0, depth_mm=145.0, exposed_faces=["depth_front"], beta_0_mm_min=0.65, beta_n_mm_min=0.8)
    specs = [("parameters", {"material_type": m, "rho_k_kg_m3": r}) for m, r in [("solid_softwood",350.0),("glulam_softwood",385.0),("lvl",480.0)]]
    specs += [("char_depth", dict(time_min=t, beta_0_mm_min=0.65, beta_n_mm_min=0.8)) for t in (0.0,10.0,19.999,20.0,30.0,60.0)]
    specs += [("section", dict(base, time_min=t)) for t in (10.0,30.0,60.0)]
    specs += [("section", dict(base, exposed_faces=["width_left"], time_min=60.0))]
    specs += [("bending", dict(base, time_min=30.0, design_bending_moment_Nmm=d, fm_k_MPa=24.0, kfi=1.25, gamma_M_fi=1.0, kmod_fi=1.0)) for d in (None,1e6)]
    return [{"operation": op, "inputs": args, "expected": evaluate(op, args)} for op, args in specs]
