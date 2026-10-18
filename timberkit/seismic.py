"""Educational EN 1998-1:2004 non-structural-element demand calculations.

Not for design. The equations estimate actions, not bracket or anchor capacity.
The existing-concrete anchorage requires project-specific ETA evidence. A force
estimate cannot establish fire, seismic or drift qualification of a detail.

Primary source actually opened and visually read on 18 October 2026:
https://www.phd.eng.br/wp-content/uploads/2015/02/en.1998.1.2004.pdf
Printed pp. 67-68 and 76-77 (PDF pp. 69-70 and 78-79).
The scope deliberately uses the 2004 edition requested in the study brief.
"""

from math import fsum, isfinite, isclose
from numbers import Real


SOURCE_URL = "https://www.phd.eng.br/wp-content/uploads/2015/02/en.1998.1.2004.pdf"
CLAUSES = {
    "Sa": "EN 1998-1:2004, 4.3.5.2(3), Equation (4.25), printed pp. 67-68",
    "Fa": "EN 1998-1:2004, 4.3.5.2(2), Equation (4.24), printed p. 67",
    "gamma_a": "EN 1998-1:2004, 4.3.5.3, printed p. 68",
    "q_a": "EN 1998-1:2004, 4.3.5.4, Table 4.4, printed p. 68",
    "drift": "EN 1998-1:2004, 4.4.3.2(1), Equations (4.31)-(4.33), printed p. 76",
    "nu": "EN 1998-1:2004, 4.4.3.2(2) Note, printed pp. 76-77; recommended NDP",
    "slot": "Declared kinematic model, not a Eurocode capacity or detailing rule",
    "load_shares": "Declared static load-allocation model, not a Eurocode bracket distribution rule",
}

DRIFT_COEFFICIENTS = {
    "brittle_attached": 0.005,
    "ductile": 0.0075,
    "non_interfering": 0.010,
}
FACADE_QA_UPPER_LIMIT = 2.0


def _number(name, value, *, positive=False, nonnegative=False):
    """Reject missing, Boolean, non-numeric, infinite and inappropriate inputs."""
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise ValueError(f"{name} must be a finite real number")
    if positive and value <= 0:
        raise ValueError(f"{name} must be positive")
    if nonnegative and value < 0:
        raise ValueError(f"{name} must be non-negative")
    return float(value)


def seismic_coefficient(alpha, soil_factor, z_m, H_m, Ta_s, T1_s):
    """Return dimensionless Sa, including the alpha*S lower bound.

    Equation (4.25), 4.3.5.2(3). alpha is ag/g, not acceleration in m/s².
    Both heights use the same foundation or rigid-basement reference level.
    Ta may be zero for the idealised rigid-element limiting case. T1 must be
    positive. This educational domain restricts z to [0, H]. The simplified
    procedure is not appropriate without justification for particularly
    important or dangerous elements: see 4.3.5.1(2)P-(3).
    """
    alpha = _number("alpha", alpha, nonnegative=True)
    soil_factor = _number("soil_factor", soil_factor, positive=True)
    z_m = _number("z_m", z_m, nonnegative=True)
    H_m = _number("H_m", H_m, positive=True)
    Ta_s = _number("Ta_s", Ta_s, nonnegative=True)
    T1_s = _number("T1_s", T1_s, positive=True)
    if z_m > H_m:
        raise ValueError("z_m must not exceed H_m in this toolkit")
    floor = alpha * soil_factor
    raw = floor * (3.0 * (1.0 + z_m / H_m) / (1.0 + (1.0 - Ta_s / T1_s) ** 2) - 0.5)
    return max(floor, raw)


def seismic_force_kN(Sa, weight_kN, gamma_a, q_a):
    """Return Fa in kN, Equation (4.24), 4.3.5.2(2).

    The force acts at the element centre of mass in the most unfavourable
    horizontal direction. gamma_a and q_a are mandatory caller inputs.
    This general equation does not assign the element to a Table 4.4 class.
    For the study facade, validate q_a with facade_behaviour_factor().
    The verified study admits gamma_a >= 1.0: 4.3.5.3 permits 1.0 for
    ordinary elements and requires at least 1.5 for its specified life-safety
    and hazardous cases. The caller must establish that classification.
    """
    Sa = _number("Sa", Sa, nonnegative=True)
    weight_kN = _number("weight_kN", weight_kN, nonnegative=True)
    gamma_a = _number("gamma_a", gamma_a, positive=True)
    q_a = _number("q_a", q_a, positive=True)
    if gamma_a < 1.0:
        raise ValueError("gamma_a must be at least 1.0 in this EN 1998-1 study")
    return Sa * weight_kN * gamma_a / q_a


def facade_behaviour_factor(q_a):
    """Validate an explicitly chosen facade qa against Table 4.4's upper limit.

    The table gives an upper limit of 2.0 for exterior/interior walls,
    partitions and facades. It does not qualify any particular bracket or
    anchor detail. A value below 1.0 is rejected as outside this study domain.
    """
    q_a = _number("q_a", q_a, positive=True)
    if not 1.0 <= q_a <= FACADE_QA_UPPER_LIMIT:
        raise ValueError("Facade q_a must be between 1.0 and the Table 4.4 upper limit 2.0")
    return q_a


def panel_weight_kN(height_mm, width_mm, self_weight_kN_m2):
    """Area times specified weight per unit area; inputs include all panel layers.

    This is dimensional arithmetic, not a Eurocode material-weight default.
    Insulation remains non-structural but its weight must still be included.
    """
    height_mm = _number("height_mm", height_mm, positive=True)
    width_mm = _number("width_mm", width_mm, positive=True)
    self_weight_kN_m2 = _number("self_weight_kN_m2", self_weight_kN_m2, nonnegative=True)
    return height_mm * width_mm / 1_000_000.0 * self_weight_kN_m2


def recommended_nu(importance_class):
    """Recommended NDP: I/II -> 0.5; III/IV -> 0.4, 4.4.3.2(2) Note.

    The applicable National Annex can specify different values by country or
    seismic zone. The caller must choose nu explicitly in drift_check().
    """
    if importance_class in ("I", "II"):
        return 0.5
    if importance_class in ("III", "IV"):
        return 0.4
    raise ValueError("importance_class must be I, II, III or IV")


def drift_check(dr_mm, storey_height_mm, nu, category):
    """Check dr*nu <= c*h and report both reduced and unreduced limits.

    4.4.3.2(1), Equations (4.31)-(4.33). dr is the design interstorey
    drift already obtained from the building analysis, including the relevant
    displacement amplification; the toolkit does not calculate that analysis.
    Category is a REQUIRED classification, not inferred from timber ductility.
    A sliding bracket alone does not prove the non-interfering classification.
    """
    dr_mm = _number("dr_mm", dr_mm, nonnegative=True)
    storey_height_mm = _number("storey_height_mm", storey_height_mm, positive=True)
    nu = _number("nu", nu, positive=True)
    if nu > 1:
        raise ValueError("nu must not exceed 1.0 in this reduction-factor study")
    if category not in DRIFT_COEFFICIENTS:
        raise ValueError("category must be brittle_attached, ductile or non_interfering")
    limit = DRIFT_COEFFICIENTS[category] * storey_height_mm
    demand = dr_mm * nu
    return {
        "category": category,
        "demand_mm": demand,
        "limit_mm": limit,
        "dr_limit_mm": limit / nu,
        "ratio": demand / limit,
        "passes": demand <= limit or isclose(demand, limit, rel_tol=1e-12, abs_tol=1e-12),
    }


def bracket_forces(force_kN, load_shares):
    """Allocate translational Fa using explicitly supplied shares summing to one.

    No bracket number or equal share is assumed. This is a declared static
    model, not a code rule. It omits eccentricity, torsion, prying, unequal
    bracket stiffness and connection interaction. A share is not a resistance.
    """
    force_kN = _number("force_kN", force_kN, nonnegative=True)
    if load_shares is None:
        raise ValueError("REQUIRED input: bracket load shares from a justified load-path model")
    try:
        shares = [_number("load share", x, nonnegative=True) for x in load_shares]
    except TypeError as exc:
        raise ValueError("load_shares must be an iterable of non-negative numbers") from exc
    if not shares or not isclose(fsum(shares), 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("bracket load shares must be non-empty and sum to 1.0")
    return [force_kN * share for share in shares]


def slot_length_mm(dr_mm, bolt_diameter_mm, installation_allowance_mm=0.0,
                   centred=True, movement_factor=1.0):
    """Return geometric slot length for an expressly assumed relative movement.

    This is NOT a Eurocode slot-design formula. The default model assumes a
    rigid panel attached at one storey datum, with the sliding bracket at the
    adjacent datum, so relative translation equals full design drift dr.
    The slot is parallel to movement, friction-free, and initially centred.
    Reversal requires travel +/-dr: L = d + 2*dr + total added allowance.
    If centred=False the caller assumes one-sided movement only, L=d+dr+a.
    movement_factor is an explicit kinematic multiplier, not a calibrated code
    parameter. Use actual hole clearance, tolerances, washers, edge distances,
    bolt bending, bearing, travel stops, friction and out-of-plane retention in
    a real detail. nu is NOT applied to the full-drift travel requirement.
    """
    dr_mm = _number("dr_mm", dr_mm, nonnegative=True)
    bolt_diameter_mm = _number("bolt_diameter_mm", bolt_diameter_mm, positive=True)
    installation_allowance_mm = _number("installation_allowance_mm", installation_allowance_mm, nonnegative=True)
    movement_factor = _number("movement_factor", movement_factor, positive=True)
    if not isinstance(centred, bool):
        raise ValueError("centred must be a Boolean")
    travel = dr_mm * movement_factor
    multiplier = 2.0 if centred else 1.0
    return {
        "slot_length_mm": bolt_diameter_mm + multiplier * travel + installation_allowance_mm,
        "travel_each_direction_mm": travel,
        "reversed_motion_accommodated": centred,
        "assumption": "centred, friction-free, reversing translation" if centred else "one-sided translation only",
    }


def case_summary(alpha, soil_factor, z_m, H_m, Ta_s, T1_s, height_mm,
                 width_mm, self_weight_kN_m2, gamma_a, q_a, dr_mm,
                 storey_height_mm, nu, category, bolt_diameter_mm,
                 installation_allowance_mm=0.0, load_shares=None):
    """Evaluate the illustrative facade, leaving bracket demand blocked if unset.

    This function deliberately returns no overall design pass. The drift pass
    is only the selected inequality. No ETA anchor capacity is assumed or
    checked and panel/bracket eccentricity is outside this simplified model.
    """
    sa = seismic_coefficient(alpha, soil_factor, z_m, H_m, Ta_s, T1_s)
    weight = panel_weight_kN(height_mm, width_mm, self_weight_kN_m2)
    fa = seismic_force_kN(sa, weight, gamma_a, facade_behaviour_factor(q_a))
    return {
        "Sa": sa,
        "weight_kN": weight,
        "Fa_kN": fa,
        "bracket_forces_kN": None if load_shares is None else bracket_forces(fa, load_shares),
        "bracket_status": "REQUIRED: justified bracket load shares" if load_shares is None else "DEMAND ONLY: supplied load shares",
        "anchor_status": "REQUIRED: project-specific manufacturer ETA capacity; no default",
        "drift": drift_check(dr_mm, storey_height_mm, nu, category),
        "slot": slot_length_mm(dr_mm, bolt_diameter_mm, installation_allowance_mm),
    }


_OPERATIONS = {
    "seismic_coefficient": seismic_coefficient,
    "seismic_force_kN": seismic_force_kN,
    "facade_behaviour_factor": facade_behaviour_factor,
    "panel_weight_kN": panel_weight_kN,
    "recommended_nu": recommended_nu,
    "drift_check": drift_check,
    "bracket_forces": bracket_forces,
    "slot_length_mm": slot_length_mm,
    "case_summary": case_summary,
}


def evaluate(operation, inputs):
    """JSON-compatible public dispatcher shared with web/seismic.js."""
    if operation not in _OPERATIONS:
        raise ValueError(f"Unknown seismic operation: {operation}")
    if not isinstance(inputs, dict):
        raise ValueError("inputs must be a dictionary")
    return _OPERATIONS[operation](**inputs)


def parity_cases():
    """Return reproducible, full-precision Python values for Node comparison."""
    summary = dict(alpha=0.2, soil_factor=1.15, z_m=12.0, H_m=15.0,
                   Ta_s=0.05, T1_s=0.5, height_mm=2700.0, width_mm=1250.0,
                   self_weight_kN_m2=0.60, gamma_a=1.0, q_a=2.0, dr_mm=15.0,
                   storey_height_mm=3000.0, nu=0.5, category="brittle_attached",
                   bolt_diameter_mm=12.0, installation_allowance_mm=0.0,
                   load_shares=None)
    specifications = [
        ("case_summary", summary),
        ("case_summary", dict(summary, load_shares=[0.5, 0.3, 0.2])),
        ("seismic_coefficient", dict(alpha=0.2, soil_factor=1.15, z_m=0.0, H_m=15.0, Ta_s=10.0, T1_s=0.5)),
        ("seismic_coefficient", dict(alpha=0.2, soil_factor=1.15, z_m=15.0, H_m=15.0, Ta_s=0.5, T1_s=0.5)),
        ("seismic_force_kN", dict(Sa=0.5, weight_kN=2.0, gamma_a=1.5, q_a=1.0)),
        ("panel_weight_kN", dict(height_mm=2700.0, width_mm=1250.0, self_weight_kN_m2=0.6)),
        ("facade_behaviour_factor", dict(q_a=2.0)),
        ("recommended_nu", dict(importance_class="II")),
        ("recommended_nu", dict(importance_class="IV")),
        ("drift_check", dict(dr_mm=31.0, storey_height_mm=3000.0, nu=0.5, category="brittle_attached")),
        ("drift_check", dict(dr_mm=15.0, storey_height_mm=3000.0, nu=0.4, category="ductile")),
        ("drift_check", dict(dr_mm=15.0, storey_height_mm=3000.0, nu=0.5, category="non_interfering")),
        ("bracket_forces", dict(force_kN=0.578, load_shares=[0.5, 0.3, 0.2])),
        ("slot_length_mm", dict(dr_mm=15.0, bolt_diameter_mm=12.0, installation_allowance_mm=2.0)),
        ("slot_length_mm", dict(dr_mm=15.0, bolt_diameter_mm=12.0, installation_allowance_mm=2.0, centred=False)),
    ]
    cases = [{"operation": op, "inputs": values, "expected": evaluate(op, values)} for op, values in specifications]
    # A supplied importance factor must not reduce the ordinary-element action.
    cases.append({"operation": "seismic_force_kN",
                  "inputs": dict(Sa=0.5, weight_kN=2.0, gamma_a=0.5, q_a=2.0),
                  "expectedError": True})
    return cases
