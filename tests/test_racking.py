"""Method A geometry, edge factor, applicability and missing-data safeguards."""
import pytest
from timberkit import racking as r


def complete(**changes):
    p=dict(fastener_design_resistance_N=1000.0,sheet_width_mm=1250.0,
           wall_height_mm=2700.0,perimeter_spacing_mm=150.0,tied_down=True,
           no_openings=True,regular_spacing=True,sheet_edge_sufficient=True,
           sheet_fixings_verified=True)
    p.update(changes)
    return r.method_a_panel(**p)


def test_brief_width_factor_independent_fraction():
    g=r.method_a_geometry(1250,2700)
    assert g["b0_mm"] == 1350
    assert g["width_factor_ci"] == pytest.approx(25/27)
    assert round(g["width_factor_ci"],3) == 0.926


def test_width_boundaries():
    assert r.method_a_geometry(675,2700)["width_condition_passed"]
    assert not r.method_a_geometry(674.99,2700)["width_condition_passed"]
    assert r.method_a_geometry(1350,2700)["width_factor_ci"] == 1.0
    assert r.method_a_geometry(2000,2700)["width_factor_ci"] == 1.0


def test_120_percent_edge_capacity_is_applied_once():
    a=complete()
    assert a["edge_fastener_design_resistance_N"] == 1200
    assert a["formula_capacity_N"] == pytest.approx(250000/27)
    b=complete(fastener_design_resistance_N=1200,fastener_capacity_already_edge_enhanced=True)
    assert b["formula_capacity_N"] == pytest.approx(a["formula_capacity_N"])
    assert b["fastener_edge_factor_applied"] == 1.0


def test_missing_detail_or_capacity_cannot_produce_applicable_resistance():
    a=complete(tied_down=None)
    assert a["status"] == "REQUIRED_INPUT" and a["capacity_N"] is None
    assert a["formula_capacity_N"] is not None
    b=complete(fastener_design_resistance_N=None)
    assert b["capacity_N"] is b["formula_capacity_N"] is None
    assert "fastener_design_resistance_N" in b["required_inputs"]


def test_inapplicable_panel_and_no_openings_gate():
    assert complete(no_openings=False)["status"] == "INAPPLICABLE"
    assert complete(sheet_width_mm=600)["capacity_N"] is None
    assert complete(tied_down=False)["capacity_N"] is None
    with pytest.raises(ValueError):complete(regular_spacing="yes")
    with pytest.raises(ValueError):complete(edge_capacity_factor=1.0)
    with pytest.raises(ValueError):r.method_a_geometry(-100,2700)


def test_parity_cases_json_safe():
    import json
    json.dumps(r.parity_cases(),allow_nan=False)
