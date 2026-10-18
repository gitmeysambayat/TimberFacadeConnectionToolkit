"""Educational EN 1995-1-1 Method A panel subcheck, not whole-wall approval.

Primary public standard opened 18 October 2026 is the consolidated
2004+A1:2008 copy. The relevant clauses are 9.2.4.1 and 9.2.4.2, Equations
(9.21)-(9.23). UK national choice of method remains for confirmation.
"""
from math import isfinite
from numbers import Real

SOURCE_URL = "https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.1.2004.pdf"
CLAUSE = "EN 1995-1-1:2004+A1:2008 9.2.4.2, Equations (9.21)-(9.22), printed pp.94-96; Swedish Wood/TDUK UK Vol.2 1:2022 pp.49-50"


def _positive(name, value):
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return float(value)


def method_a_geometry(sheet_width_mm, wall_height_mm):
    b = _positive("sheet_width_mm", sheet_width_mm)
    h = _positive("wall_height_mm", wall_height_mm)
    b0 = h/2.0
    return dict(b0_mm=b0, minimum_sheet_width_mm=h/4.0,
                width_factor_ci=min(1.0,b/b0), width_condition_passed=b >= h/4.0,
                source=CLAUSE)


def method_a_panel(fastener_design_resistance_N, sheet_width_mm, wall_height_mm,
                   perimeter_spacing_mm, *, tied_down=None, no_openings=None,
                   regular_spacing=None, sheet_edge_sufficient=None,
                   sheet_fixings_verified=None, fastener_capacity_already_edge_enhanced=False,
                   edge_capacity_factor=1.2):
    """Return equation result separately from unverified applicability.

    Section 8 fastener design capacity is enhanced by 1.2 at sheet edges,
    9.2.4.2(5). Set already_edge_enhanced=True only when the supplied Ff,Rd
    already includes that factor. Missing tie-down/detail checks block the
    applicable capacity. Sheet shear buckling, stud buckling/bearing, inter-
    element transfer, serviceability and full anchor design remain outside
    this panel subcheck even when its listed conditions are confirmed.
    """
    g = method_a_geometry(sheet_width_mm, wall_height_mm)
    s = _positive("perimeter_spacing_mm", perimeter_spacing_mm)
    ef = _positive("edge_capacity_factor", edge_capacity_factor)
    if ef != 1.2:
        raise ValueError("Verified Method A edge-capacity enhancement is 1.2")
    if not isinstance(fastener_capacity_already_edge_enhanced, bool):
        raise ValueError("fastener_capacity_already_edge_enhanced must be Boolean")
    flags = dict(tied_down=tied_down, no_openings=no_openings, regular_spacing=regular_spacing,
                 sheet_edge_sufficient=sheet_edge_sufficient, sheet_fixings_verified=sheet_fixings_verified)
    if any(v is not None and not isinstance(v,bool) for v in flags.values()):
        raise ValueError("Applicability flags must be explicitly True, False or None")
    required = [name for name,value in flags.items() if value is None]
    failures = [name for name,value in flags.items() if value is False]
    if not g["width_condition_passed"]:
        failures.append("sheet_width_below_h_over_4")
    if fastener_design_resistance_N is None:
        required.append("fastener_design_resistance_N")
        fedge = formula = None
    else:
        f = _positive("fastener_design_resistance_N", fastener_design_resistance_N)
        fedge = f*(1.0 if fastener_capacity_already_edge_enhanced else ef)
        formula = fedge*sheet_width_mm*g["width_factor_ci"]/s
    status = "INAPPLICABLE" if failures else "REQUIRED_INPUT" if required else "CONDITIONAL_PANEL_SUBCHECK"
    return dict(**g, status=status, required_inputs=required, failed_conditions=failures,
        fastener_edge_factor_applied=1.0 if fastener_capacity_already_edge_enhanced else ef,
        edge_fastener_design_resistance_N=fedge, formula_capacity_N=formula,
        capacity_N=formula if status == "CONDITIONAL_PANEL_SUBCHECK" else None,
        edge_factor_source="EN 1995-1-1 9.2.4.2(5), 1.2 sheet-edge enhancement relative to Section 8",
        limitations=["Not a complete wall or façade resistance check", "Method A national choice not verified", "Stud buckling/bearing, sheet shear buckling, central fixings, inter-element transfer, anchorage and serviceability remain to be verified"])


def evaluate(operation, inputs):
    if operation == "geometry":
        return method_a_geometry(inputs["sheet_width_mm"], inputs["wall_height_mm"])
    if operation == "panel":
        return method_a_panel(inputs.get("fastener_design_resistance_N"), inputs["sheet_width_mm"], inputs["wall_height_mm"], inputs["perimeter_spacing_mm"],
            **{name: inputs.get(name) for name in ("tied_down","no_openings","regular_spacing","sheet_edge_sufficient","sheet_fixings_verified")},
            fastener_capacity_already_edge_enhanced=inputs.get("fastener_capacity_already_edge_enhanced",False), edge_capacity_factor=inputs.get("edge_capacity_factor",1.2))
    raise ValueError("Unknown racking operation")


def parity_cases():
    specs=[("geometry",dict(sheet_width_mm=b,wall_height_mm=2700.0)) for b in (1250.0,675.0,674.9,1350.0)]
    base=dict(fastener_design_resistance_N=1000.0,sheet_width_mm=1250.0,wall_height_mm=2700.0,perimeter_spacing_mm=150.0,
              tied_down=True,no_openings=True,regular_spacing=True,sheet_edge_sufficient=True,sheet_fixings_verified=True)
    specs += [("panel",base),("panel",dict(base,tied_down=None)),("panel",dict(base,no_openings=False)),
              ("panel",dict(base,fastener_design_resistance_N=None)),("panel",dict(base,fastener_design_resistance_N=1200.0,fastener_capacity_already_edge_enhanced=True))]
    return [{"operation": op,"inputs":args,"expected":evaluate(op,args)} for op,args in specs]
