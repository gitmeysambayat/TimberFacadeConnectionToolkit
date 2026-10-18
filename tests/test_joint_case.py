"""Source-equation, load-path and boundary tests for the one-station study.

The Decimal benchmark independently evaluates the printed equations rather
than asking the existing connection module for its own expected values.
These are implementation checks, not validation against physical tests.
"""
from decimal import Decimal, localcontext
import math
import pytest

from timberkit import joint_case as case


def test_baseline_direct_source_equations_using_independent_decimal_arithmetic():
    # SW2 pp37/44, first-generation EN1995-1-1 Eqs8.7/8.30/8.32.
    # Equal C24 embedment strengths give beta=1, t1=50 and t2=100 mm.
    with localcontext() as context:
        context.prec = 50
        D = Decimal
        d, outer, centre = D(12), D(50), D(100)
        fh = D("0.082") * (1 - D("0.01") * d) * D(350)
        my = D("0.3") * D(800) * d ** D("2.6")
        reference = {
            "g": fh * outer * d,
            "h": D("0.5") * fh * centre * d,
            "j": D("1.05") * fh * outer * d / 3 *
                 ((4 + 12 * my / (fh * d * outer ** 2)).sqrt() - 1),
            "k": D("1.15") * (2 * my * fh * d).sqrt(),
        }
        result = case.calculate_case()
        assert result["embedment"]["fh_k"] == pytest.approx(float(fh), rel=1e-12)
        assert result["yield_moment"]["My_Rk"] == pytest.approx(float(my), rel=1e-12)
        for mode, expected in reference.items():
            assert result["johansen"]["modes"][mode]["Fv_Rk_N"] == pytest.approx(float(expected), rel=1e-12)
        expected_total = 2 * D("0.8") * min(reference.values()) / D("1.3")
        assert result["design_capacity"]["group_design_capacity_N"] == pytest.approx(float(expected_total), rel=1e-12)
    assert result["johansen"]["governing_mode"] == "j"
    assert round(result["design_capacity"]["group_design_capacity_N"] / 1000, 3) == 10.026


def test_load_path_has_two_parallel_planes_and_is_not_multiplied_twice():
    r = case.calculate_case()
    assert r["actions"]["NEd_N"] == 7050
    assert r["actions"]["Nser_N"] == 5000
    assert r["actions"]["one_side_design_N"] == r["actions"]["per_plane_design_N"] == 3525
    rd = r["design_capacity"]
    assert rd["group_design_capacity_N"] == pytest.approx(2 * rd["Fv_Rd_per_plane_N"])
    assert rd["utilisation"] == pytest.approx(0.7031631617, rel=1e-9)


def test_net_tension_reduces_area_by_actual_hole_and_keeps_side_demands_separate():
    r = case.calculate_case()["net_tension"]
    assert r["centre"]["net_area_mm2"] == 18700
    assert r["one_side"]["net_area_mm2"] == 9350
    assert r["ft_0_k_MPa"] == 14.5
    assert r["size_factor_kh"] == 1
    assert round(r["centre"]["design_resistance_N"], 1) == 166861.5
    assert r["centre"]["stress_MPa"] == r["one_side"]["stress_MPa"]
    assert r["centre"]["utilisation"] == r["one_side"]["utilisation"]


def test_instantaneous_slip_matches_source_table_and_parallel_spring_equilibrium():
    r = case.calculate_case()
    # SW2 p33/Table9.2: Kser = rho_mean^1.5*d/23 per plane.
    # Explicit hand-rounded targets, before any seating/freeplay or creep.
    slip = r["slip"]
    assert round(slip["Kser_per_plane_N_per_mm"], 3) == 4490.838
    assert round(slip["Kjoint_N_per_mm"], 3) == 8981.675
    assert round(slip["postseating_elastic_mm"], 6) == 0.556689
    assert slip["postseating_elastic_mm"] * slip["Kser_per_plane_N_per_mm"] == pytest.approx(2500)
    assert slip["final_deformation_status"] == "FIRST_GENERATION_CREEP_ESTIMATE_NOT_TEST_VALIDATED"


def test_final_slip_is_action_wise_with_doubled_connection_creep_factor():
    # First-generation EN2.3.2.2(3),2.2.3(5); SW1 pp157-159/Table5.4/Eq5.86.
    r = case.calculate_case()["slip"]
    assert r["member_kdef"] == .8
    assert r["connection_kdef"] == 1.6
    assert r["psi2"] == .3
    expected = (3000 * 2.6 + 2000 * 1.48) / r["Kjoint_N_per_mm"]
    assert r["final_elastic_mm"] == pytest.approx(expected)
    assert r["final_G_component_mm"] + r["final_Q_component_mm"] == r["final_elastic_mm"]
    assert r["final_elastic_mm"] > r["postseating_elastic_mm"]


def test_final_slip_permanent_only_variable_only_and_zero_psi2():
    base = case.calculate_case()["slip"]
    g_only = case.calculate_case(dict(Gk_N=5000, Qk_N=0))["slip"]
    q_only = case.calculate_case(dict(Gk_N=0, Qk_N=5000))["slip"]
    no_sustained_q = case.calculate_case(dict(Gk_N=0, Qk_N=5000, psi2=0))["slip"]
    assert g_only["final_elastic_mm"] == pytest.approx(2.6 * base["postseating_elastic_mm"])
    assert q_only["final_elastic_mm"] == pytest.approx(1.48 * base["postseating_elastic_mm"])
    assert no_sustained_q["final_elastic_mm"] == pytest.approx(base["postseating_elastic_mm"])
    assert no_sustained_q["final_G_component_mm"] == 0


def test_freeplay_added_once_and_is_not_amplified_by_creep():
    base = case.calculate_case()["slip"]
    moved = case.calculate_case(dict(additional_freeplay_mm=1))["slip"]
    assert moved["final_elastic_mm"] == base["final_elastic_mm"]
    assert moved["final_total_mm"] - base["final_total_mm"] == pytest.approx(1)
    assert moved["final_budget_status"] == "EXCEEDS_CHOSEN_STUDY_BUDGET"


def test_freeplay_is_separate_scenario_and_study_budget_is_not_code_pass():
    r = case.calculate_case({"additional_freeplay_mm": 2})
    assert r["slip"]["illustrative_total_mm"] == pytest.approx(2.5566890297)
    assert r["slip"]["study_budget_status"] == "EXCEEDS_CHOSEN_STUDY_BUDGET"
    assert r["component_resistance_and_geometry_status"] == "NO_FAILURE_IN_CHECKED_COMPONENTS"
    assert r["status"] == case.STATUS
    assert "not a Eurocode limit" in r["assumptions"]["study_budget_basis"]


def test_hole_clearance_is_not_turned_into_unverified_deterministic_slip():
    r0 = case.calculate_case({"hole_diameter_mm": 12})
    r1 = case.calculate_case({"hole_diameter_mm": 13})
    assert r0["slip"]["illustrative_total_mm"] == r1["slip"]["illustrative_total_mm"]
    assert r0["net_tension"]["centre"]["net_area_mm2"] > r1["net_tension"]["centre"]["net_area_mm2"]
    assert r1["slip"]["clearance_model_status"] == "NOT_MODELLED_INPUT_SCENARIO_ONLY"


@pytest.mark.parametrize("inputs,check", [
    ({"end_distance_mm": 83.9}, "left_loaded_end"),
    ({"overlap_mm": 183.9}, "right_loaded_end"),
    ({"width_mm": 71.9}, "both_centred_edges"),
    ({"hole_diameter_mm": 13.1}, "timber_hole_diameter"),
    ({"washer_diameter_mm": 35.9}, "washer_diameter"),
    ({"washer_thickness_mm": 3.59}, "washer_thickness"),
    ({"washer_diameter_mm": 201}, "washer_face_footprint"),
])
def test_failed_detail_never_becomes_component_success(inputs, check):
    r = case.calculate_case(inputs)
    assert r["geometry"]["checks"][check]["status"] == "FAIL"
    assert r["geometry"]["status"] == "FAIL"
    assert r["component_resistance_and_geometry_status"] == "FAIL_IN_SCOPE"
    assert "detail_geometry" in r["failed_component_checks"]
    assert r["status"] == case.STATUS


def test_detail_boundaries_are_inclusive_where_the_source_states_at_least_or_not_more_than():
    r = case.calculate_case(dict(overlap_mm=168, end_distance_mm=84, width_mm=72,
        washer_diameter_mm=36, washer_thickness_mm=3.6, hole_diameter_mm=13))
    assert r["geometry"]["status"] == "PASS_IN_SCOPE"


def test_diameter_alternatives_report_noncompliant_end_distances():
    alternatives = {c["id"]: c["result"] for c in case.sensitivity_cases()}
    assert alternatives["diameter_14"]["geometry"]["status"] == "PASS_IN_SCOPE"
    assert alternatives["diameter_16"]["geometry"]["status"] == "FAIL"
    assert alternatives["diameter_20"]["geometry"]["status"] == "FAIL"
    assert alternatives["diameter_16"]["inputs"]["washer_diameter_mm"] == 48
    assert alternatives["diameter_16"]["inputs"]["washer_thickness_mm"] == pytest.approx(4.8)
    assert alternatives["diameter_16"]["geometry"]["checks"]["left_loaded_end"]["required_mm"] == 112


def test_fixed_washers_do_not_silently_scale_when_diameter_changes():
    r = case.calculate_case(dict(diameter_mm=16, hole_diameter_mm=17))
    assert r["geometry"]["checks"]["washer_diameter"]["status"] == "FAIL"
    assert r["geometry"]["checks"]["washer_thickness"]["status"] == "FAIL"


def test_overload_is_reported_without_suppressing_limitations():
    r = case.calculate_case(dict(Qk_N=20000))
    assert r["design_capacity"]["status"] == "FAIL"
    assert "johansen_design_resistance" in r["failed_component_checks"]
    assert r["component_resistance_and_geometry_status"] == "FAIL_IN_SCOPE"
    assert len(r["unresolved_checks"]) >= 8
    assert r["status"] == case.STATUS


def test_zero_actions_and_factor_sensitivity_remain_finite():
    zero = case.calculate_case(dict(Gk_N=0, Qk_N=0))
    assert zero["design_capacity"]["utilisation"] == zero["slip"]["postseating_elastic_mm"] == 0
    permanent_factor = case.calculate_case(dict(kmod=0.6))
    base = case.calculate_case()
    assert permanent_factor["design_capacity"]["group_design_capacity_N"] == pytest.approx(.75 * base["design_capacity"]["group_design_capacity_N"])


def test_baseline_checks_combined_and_permanent_only_action_durations():
    r = case.calculate_case()["load_duration_checks"]
    assert r["permanent_only"]["NEd_N"] == pytest.approx(4050)
    assert r["permanent_only"]["kmod"] == .6
    assert r["permanent_only"]["Rd_N"] == pytest.approx(7519.591878541517)
    assert r["permanent_only"]["utilisation"] == pytest.approx(0.5385930532)
    assert r["governing_case"] == "combined"
    assert r["status"] == "PASS_IN_SCOPE"


def test_permanent_only_can_govern_when_combined_reference_remains_below_capacity():
    r = case.calculate_case(dict(Gk_N=6000, Qk_N=0))
    assert r["design_capacity"]["status"] == "PASS_IN_SCOPE"
    assert r["load_duration_checks"]["governing_case"] == "permanent_only"
    assert r["load_duration_checks"]["permanent_only"]["status"] == "FAIL"
    assert "permanent_only_johansen_design_resistance" in r["failed_component_checks"]
    assert r["component_resistance_and_geometry_status"] == "FAIL_IN_SCOPE"


def test_permanent_only_net_tension_uses_its_own_strength_factor():
    # Narrow section is intentionally geometrically unsuitable, but still
    # exposes whether the permanent net-section subcheck uses kmod=.6.
    r = case.calculate_case(dict(width_mm=14, Gk_N=600, Qk_N=0))
    durations = r["load_duration_checks"]
    assert durations["combined"]["net_tension_utilisation"] < 1
    assert durations["permanent_only"]["net_tension_utilisation"] > 1
    assert durations["permanent_only"]["centre_net_tension_utilisation"] == pytest.approx(
        810 / (100 * 14.5 * .6 / 1.3))
    assert "permanent_only_net_tension" in r["failed_component_checks"]


@pytest.mark.parametrize("inputs", [
    dict(diameter_mm=0), dict(diameter_mm=31), dict(diameter_mm=True),
    dict(Gk_N=-1), dict(Gk_N="3000"), dict(Qk_N=math.nan), dict(Qk_N=math.inf),
    dict(centre_thickness_mm=None), dict(side_thickness_mm=False), dict(gamma_M=.5),
    dict(gamma_G=.9), dict(gamma_Q=.9), dict(kmod=1.2), dict(study_slip_budget_mm=0),
    dict(hole_diameter_mm=11), dict(width_mm=13), dict(end_distance_mm=200),
    dict(load_angle_deg=90), dict(Gk_N=1e308), dict(side_thickness_mm=1e-300),
    dict(psi2=-1), dict(psi2=1.1),
])
def test_invalid_or_unrepresentable_inputs_rejected(inputs):
    with pytest.raises(ValueError):
        case.calculate_case(inputs)


def test_default_data_and_outputs_do_not_share_mutable_state():
    p = case.default_inputs()
    p["diameter_mm"] = 20
    r = case.calculate_case()
    r["unresolved_checks"].clear()
    assert case.calculate_case()["inputs"]["diameter_mm"] == 12
    assert len(case.calculate_case()["unresolved_checks"]) >= 8


def test_public_evaluate_accepts_case_object_and_operation_form():
    assert case.evaluate({}) == case.evaluate("case", {}) == case.calculate_case()
