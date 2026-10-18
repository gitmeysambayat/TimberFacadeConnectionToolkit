"""Verified educational reference properties, not project product declarations.

Sources opened 18 October 2026: Swedish Wood/TDUK UK edition 1:2022,
Volume 2, Tables 3.1-3.4 and 9.1. Material properties originate in EN 338:2016
and EN 14080:2013, referenced by EN 1995-1-1 clauses 3.2 and 3.3. They are
not invented values or a substitute for the supplied product documentation.
"""
from copy import deepcopy
from math import isfinite
from numbers import Real

SOURCE_URL = "https://www.universityofgalway.ie/media/timberengineeringresearchgroup/Design-of-timber-structures_Volume2_Rules-and-formulas-according-to-Eurocode-5.pdf"
CLAUSES = {
    "C24": "Swedish Wood/TDUK UK Vol.2 1:2022, Table 3.3 p.10; EN 338:2016; EN 1995-1-1 3.2",
    "GL24h": "Swedish Wood/TDUK UK Vol.2 1:2022, Table 3.4 p.12; EN 14080:2013; EN 1995-1-1 3.3",
    "kmod": "EN 1995-1-1:2004 3.1.3/Table 3.1; UK handbook Table 3.2 p.8",
    "kdef": "EN 1995-1-1:2004 3.1.4/Table 3.2; UK handbook Table 9.1 p.32",
    "gamma_m": "EN 1995-1-1:2004 2.4.1/Table 2.3; UK handbook Table 3.1 p.7; recommended NDP",
    "design_strength": "EN 1995-1-1:2004 2.4.1, Equation (2.14); UK handbook 3.1 p.7",
}
_PROPERTIES = {
    "C24": dict(material_type="solid_timber", fm_k_MPa=24.0, ft_0_k_MPa=14.5,
        ft_90_k_MPa=0.4, fc_0_k_MPa=21.0, fc_90_k_MPa=2.5, fv_k_MPa=4.0,
        E_0_mean_MPa=11000.0, E_0_05_MPa=7400.0, E_90_mean_MPa=370.0,
        G_mean_MPa=690.0, rho_k_kg_m3=350.0, rho_mean_kg_m3=420.0),
    "GL24h": dict(material_type="glulam", fm_k_MPa=24.0, ft_0_k_MPa=19.2,
        ft_90_k_MPa=0.5, fc_0_k_MPa=24.0, fc_90_k_MPa=2.5, fv_k_MPa=3.5,
        fr_k_MPa=1.2, E_0_mean_MPa=11500.0, E_0_05_MPa=9600.0,
        E_90_mean_MPa=300.0, E_90_05_MPa=250.0, G_mean_MPa=650.0,
        G_05_MPa=540.0, rho_k_kg_m3=385.0, rho_mean_kg_m3=420.0),
}
_DURATIONS = ("permanent", "long", "medium", "short", "instantaneous")
_KMOD_TIMBER = {1: (0.60, 0.70, 0.80, 0.90, 1.10),
               2: (0.60, 0.70, 0.80, 0.90, 1.10),
               3: (0.50, 0.55, 0.65, 0.70, 0.90)}
_KMOD_OSB3 = {1: (0.40, 0.50, 0.70, 0.90, 1.10),
              2: (0.30, 0.40, 0.55, 0.70, 0.90)}
_GAMMA = {"solid_timber": 1.30, "glulam": 1.25, "osb3": 1.20, "connections": 1.30}


def _positive(name, value):
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return float(value)


def _service_class(service_class):
    if isinstance(service_class, bool) or service_class not in (1, 2, 3):
        raise ValueError("service_class must be explicitly selected as 1, 2 or 3")
    return int(service_class)


def get_material(grade):
    """Return a fresh reference-data dictionary; unknown grades are not guessed."""
    if grade not in _PROPERTIES:
        raise ValueError("UNVERIFIED material grade; verified choices are C24 and GL24h")
    return dict(grade=grade, **deepcopy(_PROPERTIES[grade]), source=CLAUSES[grade],
                source_url=SOURCE_URL, status="REFERENCE_PROPERTIES_NOT_PRODUCT_VERIFIED")


def kmod(load_duration, service_class, material_type="solid_timber"):
    """Table lookup. Service class and load duration require deliberate inputs."""
    sc = _service_class(service_class)
    if load_duration not in _DURATIONS:
        raise ValueError("load_duration must be permanent, long, medium, short or instantaneous")
    if material_type in ("solid_timber", "glulam"):
        row = _KMOD_TIMBER[sc]
    elif material_type == "osb3":
        if sc not in _KMOD_OSB3:
            raise ValueError("UNVERIFIED/unsupported OSB/3 use in service class 3")
        row = _KMOD_OSB3[sc]
    else:
        raise ValueError("UNVERIFIED material type for kmod")
    return row[_DURATIONS.index(load_duration)]


def kdef(service_class, material_type="solid_timber"):
    """EN 1995-1-1 3.1.4/Table 3.2; UK handbook Table 9.1 p.32."""
    sc = _service_class(service_class)
    if material_type in ("solid_timber", "glulam"):
        return (0.60, 0.80, 2.00)[sc - 1]
    if material_type == "osb3" and sc in (1, 2):
        return (1.50, 2.25)[sc - 1]
    raise ValueError("UNVERIFIED/unsupported material and service-class combination for kdef")


def recommended_gamma_m(material_type):
    """Recommended NDP values, exposed to callers, not a checked UK NA choice."""
    if material_type not in _GAMMA:
        raise ValueError("UNVERIFIED material type for gamma_M")
    return _GAMMA[material_type]


def design_strength(fk_MPa, kmod_value, gamma_M):
    """fd = kmod*fk/gamma_M, EN 1995-1-1 2.4.1, Equation (2.14)."""
    return _positive("fk_MPa", fk_MPa) * _positive("kmod_value", kmod_value) / _positive("gamma_M", gamma_M)


def evaluate(operation, inputs):
    """JSON-safe dispatch used by the browser parity tests."""
    if operation == "material":
        return get_material(inputs["grade"])
    if operation == "kmod":
        return {"value": kmod(inputs["load_duration"], inputs["service_class"], inputs.get("material_type", "solid_timber")), "source": CLAUSES["kmod"]}
    if operation == "kdef":
        return {"value": kdef(inputs["service_class"], inputs.get("material_type", "solid_timber")), "source": CLAUSES["kdef"]}
    if operation == "gamma_m":
        return {"value": recommended_gamma_m(inputs["material_type"]), "status": "RECOMMENDED_NDP_NOT_NATIONAL_ANNEX_VERIFIED", "source": CLAUSES["gamma_m"]}
    if operation == "design_strength":
        return {"fd_MPa": design_strength(inputs["fk_MPa"], inputs["kmod_value"], inputs["gamma_M"]), "source": CLAUSES["design_strength"]}
    raise ValueError("Unknown materials operation")


def parity_cases():
    specs = [("material", {"grade": g}) for g in ("C24", "GL24h")]
    specs += [("kmod", {"load_duration": d, "service_class": sc, "material_type": m})
              for m, sc, d in [("solid_timber", 2, "short"), ("glulam", 3, "permanent"), ("osb3", 2, "instantaneous")]]
    specs += [("kdef", {"service_class": s, "material_type": m}) for m, s in [("solid_timber", 1), ("glulam", 3), ("osb3", 2)]]
    specs += [("gamma_m", {"material_type": m}) for m in _GAMMA]
    specs += [("design_strength", {"fk_MPa": 24.0, "kmod_value": 0.9, "gamma_M": 1.3})]
    return [{"operation": op, "inputs": args, "expected": evaluate(op, args)} for op, args in specs]
