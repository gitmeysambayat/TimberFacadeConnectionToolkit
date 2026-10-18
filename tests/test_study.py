"""Integration guards for missing information, separate from module benchmarks."""
import copy
import json
import pytest
from pathlib import Path
from timberkit.study import calculate_case
from timberkit.release import PREFIX

ROOT=Path(__file__).resolve().parents[1]


def case():
    return json.loads((ROOT/(PREFIX+'CaseStudyInputs.json')).read_text(encoding='utf-8'))


def test_illustrative_case_never_claims_overall_design_pass():
    r=calculate_case(case())
    assert r['connection']['status']=='UNVERIFIED'
    assert r['seismic']['bracket_forces_kN'] is None
    assert r['racking']['capacity_N'] is None
    assert all(f['bending']['passed'] is None for f in r['fire'])
    assert r['learner_verification_records']==[]


def test_unequal_supplied_bracket_shares_preserve_force():
    c=case();c['seismic']['bracket_load_shares']=[.5,.3,.2]
    r=calculate_case(c)['seismic']
    assert abs(sum(r['bracket_forces_kN'])-r['Fa_kN'])<1e-12
    assert r['bracket_forces_kN'][0]>r['bracket_forces_kN'][1]>r['bracket_forces_kN'][2]


def test_fa_uses_weight_not_wind_resultant():
    c=case();a=calculate_case(c);c['panel']['characteristic_wind_kN_m2']=99.
    b=calculate_case(c)
    assert b['seismic']['Fa_kN']==a['seismic']['Fa_kN']
    assert b['characteristic_wind_resultant_kN']>a['characteristic_wind_resultant_kN']


def test_one_sided_slot_explicitly_changes_kinematics():
    c=case();c['seismic']['slot_centred']=False
    assert calculate_case(c)['seismic']['slot']['slot_length_mm']==27.


def test_fire_face_orientation_changes_exhaustion():
    c=case();c['fire']['exposed_faces']=['width_left']
    sections=calculate_case(c)['fire']
    assert sections[-1]['section']['status']=='SECTION_EXHAUSTED'
    assert sections[-1]['section']['effective_area_mm2']==0


def test_racking_false_condition_blocks_formula_result():
    c=case();c['racking'].update(fastener_design_resistance_N=1000.,tied_down=False,
        no_openings=True,regular_spacing=True,sheet_edge_sufficient=True,sheet_fixings_verified=True)
    r=calculate_case(c)['racking']
    assert r['formula_capacity_N']>0
    assert r['capacity_N'] is None and r['status']=='INAPPLICABLE'


@pytest.mark.parametrize('reference',[None,'','   ',123,False])
def test_anchor_reference_requires_a_nonempty_string(reference):
    c=case();c['connection'].update(loaded_end_mm=100.,unloaded_end_mm=100.,
        loaded_edge_mm=100.,unloaded_edge_mm=100.,spacing_perpendicular_mm=100.,
        design_shear_demand_N=100.,anchor_design_capacity_N=10000.,anchor_ETA_reference=reference)
    assert calculate_case(c)['connection']['status']=='UNVERIFIED'
