"""Independent arithmetic and edge-case tests for educational Module E."""

import math

import pytest

from timberkit.seismic import (
    bracket_forces, drift_check, evaluate, facade_behaviour_factor, panel_weight_kN,
    parity_cases, recommended_nu, seismic_coefficient, seismic_force_kN, slot_length_mm,
)


def test_brief_case_with_unrounded_weight():
    # Hand: 0.23*(5.4/1.81-0.5)=0.5711878453038674.
    # Weight = 2.7*1.25*0.6=2.025, not the rounded 2.03.
    sa = seismic_coefficient(0.20, 1.15, 12.0, 15.0, 0.05, 0.5)
    weight = panel_weight_kN(2700.0, 1250.0, 0.60)
    fa = seismic_force_kN(sa, weight, 1.0, facade_behaviour_factor(2.0))
    assert sa == pytest.approx(0.5711878453038674, rel=1e-12)
    assert weight == pytest.approx(2.025, rel=1e-12)
    assert fa == pytest.approx(0.5783276933701658, rel=1e-12)
    # Brief values are rounded comparison targets, never calculation inputs.
    assert round(sa, 3) == 0.571
    assert fa == pytest.approx(0.578, abs=0.0005)


def test_minimum_coefficient_even_for_high_period_ratio():
    assert seismic_coefficient(0.2, 1.15, 0, 15, 10, 0.5) == pytest.approx(0.23)


def test_resonant_roof_coefficient():
    # Ta=T1 and z/H=1 give alpha*S*(6-0.5).
    assert seismic_coefficient(0.2, 1.15, 15, 15, 0.5, 0.5) == pytest.approx(1.265)


def test_rigid_base_limit():
    assert seismic_coefficient(0.2, 1.15, 0, 15, 0, 0.5) == pytest.approx(0.23)


@pytest.mark.parametrize("cls,expected", [("I", 0.5), ("II", 0.5), ("III", 0.4), ("IV", 0.4)])
def test_recommended_ndp_not_national_annex(cls, expected):
    assert recommended_nu(cls) == expected


@pytest.mark.parametrize("category,limit", [("brittle_attached", 15.0), ("ductile", 22.5), ("non_interfering", 30.0)])
def test_storey_limits_apply_to_reduced_drift(category, limit):
    result = drift_check(15, 3000, 0.5, category)
    assert result["demand_mm"] == 7.5
    assert result["limit_mm"] == limit
    assert result["dr_limit_mm"] == limit / 0.5
    assert result["passes"]


def test_drift_boundary_and_failure():
    assert drift_check(30, 3000, 0.5, "brittle_attached")["passes"]
    assert not drift_check(30.1, 3000, 0.5, "brittle_attached")["passes"]


def test_bracket_allocation_explicit_and_equilibrated():
    forces = bracket_forces(0.578, [0.5, 0.3, 0.2])
    assert forces == pytest.approx([0.289, 0.1734, 0.1156])
    assert math.fsum(forces) == pytest.approx(0.578)


@pytest.mark.parametrize("shares", [None, [], [0.25, 0.25], [1.1, -0.1], [float("nan")], True])
def test_no_implicit_brackets(shares):
    with pytest.raises(ValueError):
        bracket_forces(1.0, shares)


def test_full_drift_reversing_slot_is_kinematic_only():
    result = slot_length_mm(15.0, 12.0)
    assert result["slot_length_mm"] == 42.0
    assert result["travel_each_direction_mm"] == 15.0
    assert result["reversed_motion_accommodated"]
    assert slot_length_mm(15, 12, 2)["slot_length_mm"] == 44.0
    # One-sided movement is separately labelled and cannot accommodate reversal.
    one_sided = slot_length_mm(15, 12, 2, centred=False)
    assert one_sided["slot_length_mm"] == 29.0
    assert not one_sided["reversed_motion_accommodated"]


def test_explicit_kinematic_factor():
    assert slot_length_mm(15, 12, movement_factor=0.5)["slot_length_mm"] == 27.0


@pytest.mark.parametrize("q", [0.0, 0.9, 2.01, None, float("inf"), True])
def test_facade_qa_upper_bound_and_required_input(q):
    with pytest.raises(ValueError):
        facade_behaviour_factor(q)


@pytest.mark.parametrize("args", [(-0.2, 1.15, 12, 15, 0.05, 0.5), (0.2, 0, 12, 15, 0.05, 0.5),
                                  (0.2, 1.15, 16, 15, 0.05, 0.5), (0.2, 1.15, 12, 15, 0.05, 0),
                                  (0.2, 1.15, 12, 15, -0.05, 0.5)])
def test_invalid_seismic_geometry_and_periods(args):
    with pytest.raises(ValueError):
        seismic_coefficient(*args)


def test_no_unverified_classification_or_missing_nu():
    with pytest.raises(ValueError):
        recommended_nu("V")
    with pytest.raises(ValueError):
        drift_check(15, 3000, None, "ductile")
    with pytest.raises(ValueError):
        drift_check(15, 3000, 0.5, "timber")


def test_nonfinite_force_and_slot_inputs():
    with pytest.raises(ValueError):
        seismic_force_kN(0.5, float("nan"), 1, 2)
    with pytest.raises(ValueError):
        slot_length_mm(15, 12, -1)


def test_importance_factor_cannot_reduce_ordinary_element_action():
    # EN 1998-1 4.3.5.3 supports 1.0 for ordinary elements and >=1.5 for
    # specified life-safety/hazardous cases. Classification remains explicit.
    for gamma_a in (0.5, 0.999999):
        with pytest.raises(ValueError, match="gamma_a must be at least 1.0"):
            seismic_force_kN(0.5, 2.0, gamma_a, 2.0)
    assert seismic_force_kN(0.5, 2.0, 1.0, 2.0) == 0.5
    assert seismic_force_kN(0.5, 2.0, 1.5, 2.0) == 0.75


def test_summary_never_assumes_bracket_count_or_capacity():
    case = parity_cases()[0]
    result = evaluate(case["operation"], case["inputs"])
    assert result["bracket_forces_kN"] is None
    assert result["bracket_status"].startswith("REQUIRED")
    assert result["anchor_status"].startswith("REQUIRED")
    assert result["slot"]["slot_length_mm"] == 42.0
    allocated = evaluate("case_summary", dict(case["inputs"], load_shares=[0.6, 0.4]))
    assert sum(allocated["bracket_forces_kN"]) == pytest.approx(result["Fa_kN"])


def test_dispatch_rejects_unknown_operation():
    with pytest.raises(ValueError):
        evaluate("anchor_capacity", {})
