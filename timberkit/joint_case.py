"""One-station symmetric timber lap-joint study, AI-assisted 18 October 2026.

This is a source-bounded component study, never an overall design approval.
The central member carries N and each identical outer member carries N/2.
The two shear planes therefore act in parallel, not in series. There is only
one bolt station: this is not a two-station butt splice. All load is parallel
to grain, member centrelines are aligned, and rope effect is neglected.

First-generation EN 1995-1-1 equations are used with EN 338:2016 reference
C24 properties. No current national-standard or National Annex compliance
is established. Inputs describe an educational detail, not a product.
Run ``python -m timberkit.joint_case`` for dated JSON/CSV calculations.
"""
from __future__ import annotations

from copy import deepcopy
import argparse
import csv
import json
import math
import os
from pathlib import Path
import re

from . import connections, materials

def checked_prefix(value):
    """Keep a release prefix a filename component, never a path."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{8}_v[1-9][0-9]*_", value):
        raise ValueError("TFK_OUTPUT_PREFIX must look like YYYYMMDD_vN_")
    return value


PREFIX = checked_prefix(os.environ.get("TFK_OUTPUT_PREFIX", "20261018_v5_"))

STATUS = "EDUCATIONAL_COMPONENT_RESULTS_NO_OVERALL_DESIGN_PASS"
SOURCES = {
    "SW2_2022_UK": {
        "title": "Swedish Wood/TDUK, Design of timber structures, UK Volume 2, 1:2022",
        "url": materials.SOURCE_URL,
        "pages": "7-10, 22, 33, 36-38, 44-45",
        "opened": "2026-10-18",
    },
    "EC5_PUBLIC_2004_A1": {
        "title": "Public copy of BS EN 1995-1-1:2004+A1:2008",
        "url": "https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.1.2004.pdf",
        "clauses": "5.1(2), 6.1.2, 7.1/Table 7.1, 8.2.2, 8.5.1.1/Table 8.4, 10.4.3",
        "opened": "2026-10-18",
        "limitation": "Historical publicly hosted cross-check, not a current standard service.",
    },
    "SW1_2022": {
        "title": "Swedish Wood, Design of timber structures, Volume 1, 3:2022",
        "url": "https://www.swedishwood.com/siteassets/5-publikationer/pdfer/sw-design-of-timber-structures-vol1-2022.pdf",
        "pages": "157-159, Table5.4 and Equation5.86",
        "opened": "2026-10-18",
    },
}
DEFAULT_INPUTS = {
    "centre_thickness_mm": 100.0,
    "side_thickness_mm": 50.0,
    "width_mm": 200.0,
    "overlap_mm": 200.0,
    "end_distance_mm": 100.0,
    "diameter_mm": 12.0,
    "hole_diameter_mm": 13.0,
    "washer_diameter_mm": 40.0,
    "washer_thickness_mm": 4.0,
    "Gk_N": 3000.0,
    "Qk_N": 2000.0,
    "gamma_G": 1.35,
    "gamma_Q": 1.5,
    "kmod": 0.8,
    "gamma_M": 1.3,
    "additional_freeplay_mm": 0.0,
    "study_slip_budget_mm": 2.0,
    "psi2": 0.3,
}
FIXED_ASSUMPTIONS = {
    "material_grade": "C24",
    "bolt_grade": "8.8 (specified study assumption; product certification not verified)",
    "bolt_fu_k_MPa": 800.0,
    "service_class": 2,
    "load_duration": "medium baseline; kmod overrides are numerical scenarios",
    "load_to_grain_angle_deg": 0.0,
    "number_of_fasteners": 1,
    "shear_planes": 2,
    "size_factor_kh": 1.0,
    "rope_effect_N": 0.0,
    "washer_locations": "One washer under the head and one under the nut",
    "action_basis": "Selected illustrative 1.35Gk + 1.5Qk; Nser = Gk + Qk. Not a verified project combination.",
    "slip_basis": "Post-seating instantaneous elastic increment; two identical shear-plane springs in parallel.",
    "freeplay_basis": "Additional total assembly movement is an explicit scenario input, not inferred from hole diameter.",
    "study_budget_basis": "Chosen 2 mm study budget is not a Eurocode limit or product acceptance criterion.",
    "final_slip_basis": "First-generation action-wise creep estimate, identical SC2 timbers: connection kdef = 2 x member kdef. psi2 is a selected scenario, not a verified occupancy category.",
    "duration_envelope_basis": "Combined action uses the explicit kmod input; permanent-only action is separately checked with first-generation SC2 kmod = 0.6.",
}
UNRESOLVED_CHECKS = [
    "Applicable current standard edition, National Annex and project action combinations",
    "Product and timber grading declarations; bolt yield moment and shank/thread position",
    "Bolt steel resistance, washer bearing resistance and full bearing in the assembled detail",
    "Brittle splitting, row shear and end tear-out; minimum distances alone are not verification",
    "Restraint against rotation: a single bolt has no established moment-resisting function",
    "Fabrication tolerances, seating/freeplay, tightening, moisture movement, corrosion and durability",
    "Applicability and physical validation of the long-term creep estimate; reversals, cyclic degradation and repeated assembly",
    "Fire resistance of the connection and the complete timber/envelope assembly",
    "Physical prototype testing, model calibration and manufacturing/assembly trials",
]


def default_inputs():
    """A fresh dictionary so one caller cannot alter later study runs."""
    return deepcopy(DEFAULT_INPUTS)


def _number(value, name, allow_zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite real number")
    if value < 0 if allow_zero else value <= 0:
        raise ValueError(f"{name} must be {'non-negative' if allow_zero else 'positive'}")
    return float(value)


def _finite_result(value):
    """Reject overflow even when every supplied input was individually finite."""
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Case calculation overflowed the finite numerical range")
    if isinstance(value, dict):
        for item in value.values():
            _finite_result(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _finite_result(item)
    return value


def _checked_inputs(overrides):
    if overrides is not None and not isinstance(overrides, dict):
        raise ValueError("Case inputs must be an object")
    args = default_inputs()
    unknown = set(overrides or {}) - set(args)
    if unknown:
        raise ValueError("Unsupported case inputs: " + ", ".join(sorted(unknown)))
    args.update(overrides or {})
    for name, value in args.items():
        args[name] = _number(value, name, name in ("Gk_N", "Qk_N", "additional_freeplay_mm", "psi2"))
    if not 6 <= args["diameter_mm"] <= 30:
        raise ValueError("Selected educational bolt scope is 6 <= diameter_mm <= 30")
    if args["hole_diameter_mm"] < args["diameter_mm"]:
        raise ValueError("hole_diameter_mm must not be smaller than diameter_mm")
    if args["hole_diameter_mm"] >= args["width_mm"]:
        raise ValueError("Hole must leave a positive timber net width")
    if args["end_distance_mm"] >= args["overlap_mm"]:
        raise ValueError("Bolt must lie inside the overlap")
    if args["gamma_G"] < 1 or args["gamma_Q"] < 1 or args["gamma_M"] < 1:
        raise ValueError("Selected adverse-action/material partial factors must be at least 1")
    if args["kmod"] > 1.1:
        raise ValueError("Selected solid-timber kmod study scope is 0 < kmod <= 1.1")
    if args["psi2"] > 1:
        raise ValueError("Selected psi2 study scope is 0 <= psi2 <= 1")
    return args


def _geometry(p):
    d = p["diameter_mm"]
    minimum = connections.minimum_spacings(d, "bolt", 0)["minimum_mm"]
    left, right, edge = p["end_distance_mm"], p["overlap_mm"] - p["end_distance_mm"], p["width_mm"] / 2
    # Opposite force directions make opposite ends loaded in centre/outer
    # members. Check both overlap ends conservatively against the loaded-end
    # minimum. One centred bolt has no inter-fastener a1/a2 spacing.
    checks = {}

    def add(name, actual, required, clause, direction="minimum"):
        if direction == "minimum":
            satisfies = actual + 1e-10 >= required
        elif direction == "strictly_greater":
            satisfies = actual > required
        else:
            satisfies = actual <= required + 1e-10
        checks[name] = dict(actual_mm=actual, required_mm=required, comparison=direction,
                            status="PASS" if satisfies else "FAIL", clause=clause)

    table = "EN1995-1-1 8.5.1.1 Table8.4, parallel grain; SW2 p45"
    add("left_loaded_end", left, minimum["a3_t"], table)
    add("right_loaded_end", right, minimum["a3_t"], table)
    add("both_centred_edges", edge, max(minimum["a4_t"], minimum["a4_c"]), table)
    detail = "EN1995-1-1 10.4.3(1)-(2)"
    add("timber_hole_diameter", p["hole_diameter_mm"], d + 1, detail, "maximum")
    add("washer_diameter", p["washer_diameter_mm"], 3 * d, detail)
    add("washer_thickness", p["washer_thickness_mm"], 0.3 * d, detail)
    # Full circular washer footprint must fit on the face. This is only a
    # geometric prerequisite, not verification of bearing resistance.
    add("washer_face_footprint", p["washer_diameter_mm"] / 2, min(left, right, edge),
        "Elementary footprint geometry; full bearing resistance remains unverified", "maximum")
    add("washer_outer_diameter_exceeds_hole", p["washer_diameter_mm"], p["hole_diameter_mm"],
        "Elementary ring geometry; washer hole/product geometry remains unverified", "strictly_greater")
    return dict(status="FAIL" if any(c["status"] == "FAIL" for c in checks.values()) else "PASS_IN_SCOPE",
                checks=checks, opposite_end_mm=right, centred_edge_mm=edge,
                inter_fastener_spacing="NOT_APPLICABLE_SINGLE_BOLT",
                bearing_resistance_status="UNVERIFIED")


def _calculate_case(inputs=None):
    """Return component results and unresolved checks, without overall pass."""
    p = _checked_inputs(inputs)
    material = materials.get_material("C24")
    d = p["diameter_mm"]
    ned = p["gamma_G"] * p["Gk_N"] + p["gamma_Q"] * p["Qk_N"]
    nser = p["Gk_N"] + p["Qk_N"]
    fh = connections.embedment_strength(material["rho_k_kg_m3"], d, "bolt", 0)
    my = connections.yield_moment(d, FIXED_ASSUMPTIONS["bolt_fu_k_MPa"], "bolt")
    johansen = connections.timber_to_timber_modes(d, p["side_thickness_mm"], p["centre_thickness_mm"],
        fh["fh_k"], fh["fh_k"], my["My_Rk"], "double", "bolt", 0)
    capacity = connections.design_capacity(johansen["Fv_Rk_N"], p["kmod"], p["gamma_M"], 1, 2)
    resistance = capacity["group_design_capacity_N"]
    capacity.update(utilisation=ned / resistance,
                    status="PASS_IN_SCOPE" if ned <= resistance + 1e-10 else "FAIL")
    geometry = _geometry(p)
    ft_d = materials.design_strength(material["ft_0_k_MPa"], p["kmod"], p["gamma_M"])

    def net(thickness, demand):
        area = (p["width_mm"] - p["hole_diameter_mm"]) * thickness
        rd = area * ft_d
        return dict(net_area_mm2=area, demand_N=demand, stress_MPa=demand / area,
                    design_resistance_N=rd, utilisation=demand / rd,
                    status="PASS_IN_SCOPE" if demand <= rd + 1e-10 else "FAIL")

    nets = dict(centre=net(p["centre_thickness_mm"], ned), one_side=net(p["side_thickness_mm"], ned / 2),
                ft_0_k_MPa=material["ft_0_k_MPa"], ft_0_d_MPa=ft_d, size_factor_kh=1.0,
                clause="EN1995-1-1 5.1(2), 6.1.2; SW2 p22. Net area at one hole, no favourable size increase.")
    permanent_ned = p["gamma_G"] * p["Gk_N"]
    permanent_kmod = materials.kmod("permanent", 2, "solid_timber")
    permanent_rd = connections.design_capacity(johansen["Fv_Rk_N"], permanent_kmod, p["gamma_M"], 1, 2)["group_design_capacity_N"]
    permanent_ft_d = materials.design_strength(material["ft_0_k_MPa"], permanent_kmod, p["gamma_M"])
    permanent_centre_u = permanent_ned / (nets["centre"]["net_area_mm2"] * permanent_ft_d)
    permanent_side_u = (permanent_ned / 2) / (nets["one_side"]["net_area_mm2"] * permanent_ft_d)
    combined_max = max(capacity["utilisation"], nets["centre"]["utilisation"], nets["one_side"]["utilisation"])
    permanent_max = max(permanent_ned / permanent_rd, permanent_centre_u, permanent_side_u)
    # Reuse each component's stated numerical comparison. A strict ratio > 1
    # would otherwise contradict a component that is within its 1e-10 N
    # floating-point comparison tolerance at the exact resistance boundary.
    combined_failed = capacity["status"] == "FAIL" or any(
        nets[member]["status"] == "FAIL" for member in ("centre", "one_side"))
    permanent_failed = permanent_max > 1
    duration_checks = dict(
        combined=dict(NEd_N=ned, kmod=p["kmod"], Rd_N=resistance, utilisation=capacity["utilisation"],
            net_tension_utilisation=max(nets["centre"]["utilisation"], nets["one_side"]["utilisation"]),
            centre_net_tension_utilisation=nets["centre"]["utilisation"], one_side_net_tension_utilisation=nets["one_side"]["utilisation"],
            status="FAIL" if combined_failed else "PASS_IN_SCOPE"),
        permanent_only=dict(NEd_N=permanent_ned, kmod=permanent_kmod, Rd_N=permanent_rd,
            utilisation=permanent_ned / permanent_rd, ft_0_d_MPa=permanent_ft_d,
            net_tension_utilisation=max(permanent_centre_u, permanent_side_u),
            centre_net_tension_utilisation=permanent_centre_u, one_side_net_tension_utilisation=permanent_side_u,
            status="FAIL" if permanent_failed else "PASS_IN_SCOPE"),
        governing_case="permanent_only" if permanent_max > combined_max else "combined",
        status="FAIL" if combined_failed or permanent_failed else "PASS_IN_SCOPE",
        clause="EN1995-1-1 3.1.3/Table3.1; SW2 pp7-8. Selected illustrative G and G+Q envelope, not a complete project combination set.")
    per_plane = connections.slip_modulus(material["rho_mean_kg_m3"], d, "bolt", steel_factor=1)
    kjoint = 2 * per_plane["Kser_N_per_mm"]
    elastic = nser / kjoint
    total = elastic + p["additional_freeplay_mm"]
    member_kdef = materials.kdef(2, "solid_timber")
    connection_kdef = 2 * member_kdef
    final_g = p["Gk_N"] * (1 + connection_kdef) / kjoint
    final_q = p["Qk_N"] * (1 + p["psi2"] * connection_kdef) / kjoint
    final_elastic = final_g + final_q
    final_total = final_elastic + p["additional_freeplay_mm"]
    slip = dict(Kser_per_plane_N_per_mm=per_plane["Kser_N_per_mm"], Kjoint_N_per_mm=kjoint,
        postseating_elastic_mm=elastic, additional_freeplay_mm=p["additional_freeplay_mm"],
        illustrative_total_mm=total, study_budget_mm=p["study_slip_budget_mm"],
        study_budget_utilisation=total / p["study_slip_budget_mm"],
        study_budget_status="WITHIN_CHOSEN_STUDY_BUDGET" if total <= p["study_slip_budget_mm"] else "EXCEEDS_CHOSEN_STUDY_BUDGET",
        clearance_model_status="NOT_MODELLED_INPUT_SCENARIO_ONLY",
        member_kdef=member_kdef, connection_kdef=connection_kdef, psi2=p["psi2"],
        final_G_component_mm=final_g, final_Q_component_mm=final_q,
        final_elastic_mm=final_elastic, final_total_mm=final_total,
        final_budget_utilisation=final_total / p["study_slip_budget_mm"],
        final_budget_status="WITHIN_CHOSEN_STUDY_BUDGET" if final_total <= p["study_slip_budget_mm"] else "EXCEEDS_CHOSEN_STUDY_BUDGET",
        final_deformation_status="FIRST_GENERATION_CREEP_ESTIMATE_NOT_TEST_VALIDATED",
        clause="EN1995-1-1 7.1 Table7.1, 2.3.2.2(3), 2.2.3(5); SW2 p33, SW1 pp157-159 Table5.4/Eq5.86. Parallel-spring equilibrium.")
    failed = []
    if capacity["status"] == "FAIL":
        failed.append("johansen_design_resistance")
    if duration_checks["permanent_only"]["utilisation"] > 1:
        failed.append("permanent_only_johansen_design_resistance")
    if duration_checks["permanent_only"]["net_tension_utilisation"] > 1:
        failed.append("permanent_only_net_tension")
    if geometry["status"] == "FAIL":
        failed.append("detail_geometry")
    for member in ("centre", "one_side"):
        if nets[member]["status"] == "FAIL":
            failed.append("net_tension_" + member)
    return _finite_result(dict(status=STATUS, inputs=p, assumptions=deepcopy(FIXED_ASSUMPTIONS), material=material,
        actions=dict(NEd_N=ned, Nser_N=nser, per_plane_design_N=ned / 2, per_plane_service_N=nser / 2,
                     centre_design_N=ned, one_side_design_N=ned / 2),
        embedment=fh, yield_moment=my, johansen=johansen, design_capacity=capacity,
        geometry=geometry, net_tension=nets, load_duration_checks=duration_checks, slip=slip,
        component_resistance_and_geometry_status="FAIL_IN_SCOPE" if failed else "NO_FAILURE_IN_CHECKED_COMPONENTS",
        failed_component_checks=failed, unresolved_checks=deepcopy(UNRESOLVED_CHECKS),
        source_ids=["SW2_2022_UK", "EC5_PUBLIC_2004_A1", "SW1_2022"]))


def calculate_case(inputs=None):
    try:
        return _calculate_case(inputs)
    except ArithmeticError as error:
        raise ValueError("Case inputs exceeded the finite numerical range") from error


def sensitivity_cases():
    """Controlled alternatives. Changed hole/washer geometry is explicit."""
    cases = []
    for d in (8.0, 10.0, 12.0, 14.0, 16.0, 20.0):
        p = default_inputs()
        p.update(diameter_mm=d, hole_diameter_mm=d + 1,
                 washer_diameter_mm=max(40, 3 * d), washer_thickness_mm=max(4, 0.3 * d))
        cases.append(dict(id="diameter_" + str(int(d)), changed_inputs=["diameter_mm", "hole_diameter_mm", "washer_diameter_mm", "washer_thickness_mm"],
                          result=calculate_case(p)))
    for freeplay in (0.0, 0.5, 1.0, 2.0):
        cases.append(dict(id="freeplay_" + str(freeplay), changed_inputs=["additional_freeplay_mm"],
                          result=calculate_case(dict(additional_freeplay_mm=freeplay))))
    for kmod in (0.6, 0.8, 0.9):
        cases.append(dict(id="kmod_" + str(kmod), changed_inputs=["kmod"],
                          result=calculate_case(dict(kmod=kmod))))
    for psi2 in (0.0, 0.3, 1.0):
        cases.append(dict(id="psi2_" + str(psi2), changed_inputs=["psi2"],
                          result=calculate_case(dict(psi2=psi2))))
    cases.append(dict(id="permanent_only", changed_inputs=["Qk_N", "kmod"],
                      result=calculate_case(dict(Qk_N=0, kmod=0.6))))
    return cases


def evaluate(operation=None, inputs=None):
    if isinstance(operation, dict) or operation is None:
        if inputs is not None:
            raise ValueError("Pass either a case object or an operation and inputs")
        return calculate_case(operation)
    if operation != "case":
        raise ValueError("Unknown joint-case operation")
    return calculate_case(inputs)


def parity_cases(baseline_inputs=None):
    baseline = _checked_inputs(baseline_inputs)
    cases = [dict(operation="case", inputs=baseline, expected=calculate_case(baseline))]
    cases.extend(dict(operation="case", inputs=c["result"]["inputs"], expected=c["result"])
                 for c in sensitivity_cases())
    reference_rd = calculate_case()["design_capacity"]["group_design_capacity_N"]
    for relative_increment in (1e-15, 1e-12):
        args = dict(Gk_N=0, Qk_N=reference_rd / 1.5 * (1 + relative_increment))
        cases.append(dict(operation="case", inputs=args, expected=calculate_case(args)))
    for args in (dict(end_distance_mm=50), dict(hole_diameter_mm=14), dict(washer_thickness_mm=2),
                 dict(Qk_N=20000), dict(width_mm=40, hole_diameter_mm=13),
                 dict(diameter_mm=16, hole_diameter_mm=17), dict(Gk_N=0, Qk_N=0),
                 dict(Gk_N=5000, Qk_N=0), dict(Gk_N=0, Qk_N=5000), dict(psi2=0)):
        cases.append(dict(operation="case", inputs=args, expected=calculate_case(args)))
    for args in (dict(diameter_mm=0), dict(Gk_N=-1), dict(gamma_M=0.5), dict(diameter_mm=True),
                 dict(hole_diameter_mm=11), dict(width_mm=13), dict(end_distance_mm=200),
                 dict(load_angle_deg=90), dict(kmod=1.2), dict(Gk_N="3000"), dict(psi2=-1), dict(psi2=1.1)):
        cases.append(dict(operation="case", inputs=args, expectedError=True))
    return cases


def export_case(root, *, prefix=PREFIX, input_path=None):
    """Export a validated baseline and canonical sensitivity study.

    An existing dated input file is the baseline source unless an explicit
    source is supplied. All input parsing and calculations finish before any
    artefact is written, so invalid input cannot replace earlier results.
    Sensitivities remain the defined canonical study, with their complete
    input records, rather than silently changing the published comparison.
    """
    root = Path(root)
    prefix = checked_prefix(prefix)
    source = Path(input_path) if input_path is not None else root / (prefix + "JointCaseInputs.json")
    has_source = input_path is not None or source.exists()
    if has_source:
        try:
            supplied = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(f"Cannot read case input JSON: {source}") from error
        inputs = _checked_inputs(supplied)
    else:
        inputs = default_inputs()
    result = calculate_case(inputs)
    alternatives = sensitivity_cases()
    for suffix, data in (("JointCaseInputs.json", inputs), ("JointCaseResults.json", result),
                         ("JointCaseSensitivity.json", alternatives), ("JointCaseParityVectors.json", parity_cases(inputs))):
        (root / (prefix + suffix)).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    rows = []
    for case in alternatives:
        r = case["result"]
        rows.append(dict(case=case["id"], diameter_mm=r["inputs"]["diameter_mm"],
            mode=r["johansen"]["governing_mode"], resistance_N=r["design_capacity"]["group_design_capacity_N"],
            utilisation=r["design_capacity"]["utilisation"], elastic_slip_mm=r["slip"]["postseating_elastic_mm"],
            freeplay_mm=r["inputs"]["additional_freeplay_mm"], total_scenario_slip_mm=r["slip"]["illustrative_total_mm"],
            final_elastic_slip_mm=r["slip"]["final_elastic_mm"], final_total_scenario_mm=r["slip"]["final_total_mm"],
            governing_duration_case=r["load_duration_checks"]["governing_case"],
            geometry_status=r["geometry"]["status"], component_status=r["component_resistance_and_geometry_status"]))
    with (root / (prefix + "JointCaseSensitivity.csv")).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return dict(status=result["status"], governing_mode=result["johansen"]["governing_mode"],
        design_resistance_N=result["design_capacity"]["group_design_capacity_N"],
        postseating_elastic_mm=result["slip"]["postseating_elastic_mm"], alternatives=len(alternatives),
        baseline_source=source.name if has_source else "canonical defaults",
        sensitivity_basis="Canonical default study; each scenario includes its own inputs")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path,
        help="Input JSON path; otherwise use the existing dated input file, or canonical defaults if absent")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(export_case(root, input_path=args.inputs), indent=2))


if __name__ == "__main__":
    main()
