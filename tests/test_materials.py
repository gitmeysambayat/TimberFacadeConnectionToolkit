"""Reference transcription checks, not tests of manufactured material quality."""
import math
import pytest
from timberkit import materials as m


def test_c24_reference_density_and_strength_from_uk_handbook():
    p = m.get_material("C24")
    assert (p["rho_k_kg_m3"], p["rho_mean_kg_m3"]) == (350.0, 420.0)
    assert (p["fm_k_MPa"], p["fc_0_k_MPa"], p["E_0_mean_MPa"]) == (24.0,21.0,11000.0)
    assert p["ft_0_k_MPa"] == 14.5  # UK 2022 EN 338:2016 table, not an older C24 table.


def test_gl24h_is_homogeneous_row_not_gl24c():
    p = m.get_material("GL24h")
    assert (p["rho_k_kg_m3"],p["rho_mean_kg_m3"]) == (385.0,420.0)
    assert (p["ft_0_k_MPa"],p["E_0_mean_MPa"],p["E_0_05_MPa"]) == (19.2,11500.0,9600.0)
    p["rho_k_kg_m3"] = -1
    assert m.get_material("GL24h")["rho_k_kg_m3"] == 385.0


def test_service_and_duration_tables_and_recommended_ndps():
    assert m.kmod("short",2) == 0.9
    assert m.kmod("permanent",3,"glulam") == 0.5
    assert m.kmod("medium",2,"osb3") == 0.55
    assert m.kdef(3,"glulam") == 2.0
    assert m.kdef(2,"osb3") == 2.25
    assert m.recommended_gamma_m("connections") == 1.3
    assert m.design_strength(24.0,0.9,1.3) == pytest.approx(16.615384615384617)


@pytest.mark.parametrize("bad",[None,True,0,-1,float("nan"),float("inf")])
def test_no_nonphysical_strength_input(bad):
    with pytest.raises(ValueError): m.design_strength(bad,0.9,1.3)


def test_unverified_inputs_do_not_get_defaults():
    with pytest.raises(ValueError): m.get_material("C24 ungraded")
    with pytest.raises(ValueError): m.kmod("short",3,"osb3")
    with pytest.raises(ValueError): m.kdef(3,"osb3")
    with pytest.raises(ValueError): m.kmod("wind",2)
    with pytest.raises(ValueError): m.kdef(True)


def test_parity_cases_are_json_safe():
    import json
    json.dumps(m.parity_cases(),allow_nan=False)
