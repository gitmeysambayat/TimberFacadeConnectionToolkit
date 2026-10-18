"""Hand checks of the unprotected reduced-section equations and their scope."""
import pytest
from timberkit import fire as f


@pytest.mark.parametrize("minutes,expected",[(0,0.0),(10,11.5),(20,23.0),(30,31.0),(60,55.0)])
def test_brief_effective_depth_hand_values(minutes,expected):
    assert f.effective_char_depth(minutes,0.8) == pytest.approx(expected)


def test_k0_branch_is_continuous_at_twenty_minutes():
    a=f.charring_depths(19.999,0.65,0.8)
    b=f.charring_depths(20.0,0.65,0.8)
    c=f.charring_depths(20.001,0.65,0.8)
    assert a["k0"] == pytest.approx(0.99995)
    assert b["k0"] == c["k0"] == 1.0
    assert a["effective_char_depth_mm"] < b["effective_char_depth_mm"] < c["effective_char_depth_mm"]


def test_one_face_orientation_145_depth_not_45_width():
    s=f.reduced_section_rectangular(45,145,60,0.8,["depth_front"])
    assert s["effective_depth_mm"] == 90.0
    assert s["effective_width_mm"] == 45.0
    assert s["effective_area_mm2"] == 4050.0
    assert s["W_y_mm3"] == 60750.0
    # The char-only residual section is different from the effective section.
    assert s["residual_depth_mm"] == 97.0
    assert s["centroid_shift_depth_mm"] == 27.5


def test_exposing_45_dimension_exhausts_section_without_negative_area():
    s=f.reduced_section_rectangular(45,145,60,0.8,["width_left"])
    assert s["status"] == "SECTION_EXHAUSTED"
    assert s["effective_area_mm2"] == s["W_y_mm3"] == 0.0
    assert s["centroid_shift_width_mm"] is None
    assert s["centroid_shift_depth_mm"] is None


def test_fire_strength_factor_is_verified_and_requires_fire_action():
    p=f.fire_parameters("solid_softwood",350)
    assert p["kfi"] == 1.25
    assert f.fire_parameters("glulam_softwood",385)["kfi"] == 1.15
    s=f.reduced_section_rectangular(45,145,30,0.8,["depth_front"])
    missing=f.check_fire_bending(s,None,24,kfi=1.25,gamma_M_fi=1,kmod_fi=1)
    assert missing["status"] == "REQUIRED_INPUT"
    assert missing["passed"] is None and missing["utilisation"] is None
    # Artificial unit-test demand, not a case-study fire action.
    out=f.check_fire_bending(s,1_000_000,24,kfi=1.25,gamma_M_fi=1,kmod_fi=1)
    assert out["fd_fi_MPa"] == 30.0
    assert out["capacity_Nmm"] == 2_924_100.0
    assert out["utilisation"] == pytest.approx(1_000_000/2_924_100)


def test_protection_and_assemblies_are_not_silently_treated_as_exposed():
    with pytest.raises(ValueError): f.reduced_section_rectangular(45,145,30,0.8,["depth_front"],protected=True)
    with pytest.raises(ValueError): f.reduced_section_rectangular(45,145,30,0.8,["depth_front"],insulated_assembly=True)
    with pytest.raises(ValueError): f.reduced_section_rectangular(45,145,30,0.8,["front"])
    with pytest.raises(ValueError): f.fire_parameters("solid_softwood",280)
    with pytest.raises(ValueError): f.fire_parameters("lvl",420)
    with pytest.raises(ValueError): f.effective_char_depth(-10,0.8)
    with pytest.raises(ValueError): f.charring_depths(10,0.65,0.8,d0_mm=0)


def test_parity_cases_json_safe():
    import json
    json.dumps(f.parity_cases(),allow_nan=False)
