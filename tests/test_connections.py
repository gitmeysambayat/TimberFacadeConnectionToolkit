"""Independent benchmarks, published examples and boundary checks, 2026-10-18.

Educational verification of calculations, not physical/design validation.
"""
import math
import pytest
from timberkit import connections as c


def test_requested_hand_benchmarks_at_their_stated_precision():
    assert round(c.embedment_strength(350,12)["fh0_k"],1)==25.3
    assert round(c.yield_moment(12,400)["My_Rk"]/1000,1)==76.7
    slip=c.slip_modulus(420,12)
    assert round(slip["Kser_N_per_mm"]/1000,2)==4.49
    assert round(slip["Ku_N_per_mm"]/1000,2)==2.99
    assert round(c.effective_number(5,84,12)["n_eff"],2)==3.65


def test_published_example_4_1_all_three_modes_and_total():
    result=c.published_examples()[0]
    # SW3 p21 prints characteristic modes to two decimals in kN.
    assert round(result["modes"]["c"]["Fv_Rk_N"]/1000,2)==9.91
    assert round(result["modes"]["d"]["Fv_Rk_N"]/1000,2)==4.83
    assert round(result["modes"]["e"]["Fv_Rk_N"]/1000,2)==5.26
    assert round(result["toolkit_total_design_N"]/1000,1)==29.0
    assert result["kmod"]==.65 and result["gamma_M"]==1.3


def test_published_example_4_2_nail_yield_and_rope_separately():
    result=c.published_examples()[1]
    # SW3 p23 no-rope capacity1607N; p24 rounded1.70kN and1.05kN.
    assert round(result["toolkit_no_rope_N"])==1607
    assert round(result["toolkit_with_rope_N"]/1000,2)==1.70
    assert round(result["toolkit_design_N"]/1000,2)==1.05
    assert result["modes"]["d"]["rope_N"]==383/4
    assert result["modes"]["c"]["rope_N"]==0
    assert result["kmod"]==.8 and result["gamma_M"]==1.3


def test_embedment_angle_and_wood_type():
    par=c.embedment_strength(350,12)
    perp=c.embedment_strength(350,12,alpha_deg=90)
    assert perp["fh_k"]==pytest.approx(par["fh_k"]/1.53)
    assert c.embedment_strength(350,12,wood_type="hardwood")["k90"]==pytest.approx(1.08)
    assert c.embedment_strength(350,12,wood_type="lvl")["k90"]==pytest.approx(1.48)
    assert c.embedment_strength(350,2.8,"nail_round",alpha_deg=90)["fh_k"]==c.embedment_strength(350,2.8,"nail_round")["fh_k"]


def test_screw_nominal_diameter_selects_rule_not_effective_diameter():
    # SW2 p46: nominal d chooses the 6 mm rule; effective d enters embedment.
    # An 8 mm screw with effective d=5.5 mm still uses the angle-sensitive rule.
    screw=c.embedment_strength(350,5.5,"screw",alpha_deg=90,nominal_d=8)
    assert screw["fh_k"]==pytest.approx(.082*(1-.01*5.5)*350/(1.35+.015*5.5))
    assert screw["k90"] is not None
    small=c.embedment_strength(350,4,"screw",alpha_deg=90,nominal_d=5)
    assert small["fh_k"]==pytest.approx(.082*350*4**(-.3))
    assert small["k90"] is None


@pytest.mark.parametrize("inputs",[
    dict(d=5.5),dict(d=12),dict(d=8,nominal_d=6),dict(d=12,nominal_d=31),
])
def test_screw_embedment_rejects_ambiguous_or_unsupported_diameters(inputs):
    with pytest.raises(ValueError):c.embedment_strength(350,fastener="screw",**inputs)


def test_all_timber_modes_per_plane_and_swap_symmetry():
    one=c.timber_to_timber_modes(12,45,80,25.256,30,76700,Fax_Rk=0)
    swapped=c.timber_to_timber_modes(12,80,45,30,25.256,76700,Fax_Rk=0)
    assert set(one["modes"])==set("abcdef")
    assert one["Fv_Rk_N"]==pytest.approx(swapped["Fv_Rk_N"])
    assert one["modes"]["a"]["Fv_Rk_N"]==pytest.approx(13638.24)
    double=c.timber_to_timber_modes(12,45,80,25.256,30,76700,shear="double",Fax_Rk=0)
    assert set(double["modes"])=={"g","h","j","k"}
    assert double["modes"]["h"]["Fv_Rk_N"]==14400
    assert double["per_fastener_total_N"]==2*double["Fv_Rk_N"]


@pytest.mark.parametrize("fastener,cap",list(c.ROPE_CAPS.items()))
def test_rope_effect_is_mode_specific_and_capped(fastener,cap):
    r=c.timber_to_timber_modes(12,45,80,25.256,30,76700,fastener=fastener,Fax_Rk=1e9)
    for key,mode in r["modes"].items():
        assert mode["rope_N"]==pytest.approx(cap*mode["johansen_N"] if key in "cdef" else 0)


def test_rope_effect_below_cap_uses_quarter_axial_resistance():
    r=c.steel_to_timber_modes(12,45,25.256,76700,6,Fax_Rk=100)
    assert r["modes"]["b"]["rope_N"]==25
    assert r["modes"]["a"]["rope_N"]==0


def test_exact_steel_thin_thick_and_intermediate_limiting_capacities():
    thin=c.steel_to_timber_modes(12,45,25.256,76700,6,Fax_Rk=0)
    thick=c.steel_to_timber_modes(12,45,25.256,76700,12,Fax_Rk=0,hole_tolerance_mm=.1)
    mid=c.steel_to_timber_modes(12,45,25.256,76700,9,Fax_Rk=0,hole_tolerance_mm=.1)
    assert thin["plate_class"]=="thin" and set(thin["modes"])=={"a","b"}
    assert thick["plate_class"]=="thick" and set(thick["modes"])=={"c","d","e"}
    assert mid["Fv_Rk_N"]==pytest.approx((thin["Fv_Rk_N"]+thick["Fv_Rk_N"])/2)
    assert set(mid["modes"])=={"thin_a","thin_b","thick_c","thick_d","thick_e"}


def test_thick_hole_fit_is_required_and_strict():
    assert c.steel_to_timber_modes(12,45,25,76700,12)["status"]=="UNVERIFIED"
    assert c.steel_to_timber_modes(12,45,25,76700,12,hole_tolerance_mm=1.2)["status"]=="UNVERIFIED"
    assert c.steel_to_timber_modes(12,45,25,76700,12,hole_tolerance_mm=1.19)["applicability_verified"]


def test_double_steel_central_outer_modes_and_per_plane_accounting():
    central=c.steel_to_timber_modes(12,45,25,76700,1,configuration="central",Fax_Rk=0)
    assert set(central["modes"])=={"f","g","h"}
    assert central["shear_planes"]==2
    outer=c.steel_to_timber_modes(12,90,25,76700,6,configuration="outer",Fax_Rk=0)
    assert set(outer["modes"])=={"j","k"}
    assert outer["modes"]["j"]["Fv_Rk_N"]==13500
    thick=c.steel_to_timber_modes(12,90,25,76700,12,configuration="outer",Fax_Rk=0,hole_tolerance_mm=0)
    assert set(thick["modes"])=={"l","m"}


def test_group_number_and_nail_interpolation_boundaries():
    assert c.effective_number(5,84,12,alpha_deg=90)["n_eff"]==5
    assert c.effective_number(1,None,12)["n_eff"]==1
    assert c.nail_kef(7*2.8,2.8)["kef"]==.7
    assert c.nail_kef(8.5*2.8,2.8)["kef"]==pytest.approx(.775)
    assert c.nail_kef(5*2.8,2.8,predrilled=True)["kef"]==.5
    assert c.nail_kef(20*2.8,2.8)["kef"]==1
    assert c.effective_number(5,28,2.8,"nail_round",alpha_deg=45)["status"]=="UNVERIFIED"


def test_spacing_tables_and_partial_unknowns():
    b=c.minimum_spacings(12)["minimum_mm"]
    assert b==dict(a1=60,a2=48,a3_t=84,a3_c=48,a4_t=36,a4_c=36)
    assert c.check_spacings(b,b)["status"]=="PASS"
    assert c.check_spacings(b,dict(a1=84))["status"]=="UNVERIFIED"
    assert c.check_spacings(b,dict(b,a3_t=83.9))["status"]=="FAIL"
    nail=c.minimum_spacings(2.8,"nail_round",rho_k=350)["minimum_mm"]
    steel=c.minimum_spacings(2.8,"nail_round",rho_k=350,connection_type="steel")["minimum_mm"]
    assert steel["a1"]==pytest.approx(.7*nail["a1"])
    assert steel["a3_t"]==nail["a3_t"]  # reductions never applied to end/edge distances


def test_slip_density_choice_and_optional_steel_multiplier():
    plain=c.slip_modulus(420,12)
    steel=c.slip_modulus(420,12,steel_factor=2)
    assert steel["Kser_N_per_mm"]==2*plain["Kser_N_per_mm"]
    assert c.slip_modulus(350,12,rho_m2=504)["rho_m_effective"]==420
    assert steel["Ku_N_per_mm"]==pytest.approx(5987.783404108565)


def test_missing_nail_head_is_not_silently_verified():
    assert c.panel_embedment_strength(2.8,15)["status"]=="UNVERIFIED"
    assert c.panel_embedment_strength(2.8,15,head_d=5.6)["status"]=="VERIFIED_FORMULA"
    assert c.panel_embedment_strength(2.8,15,head_d=5.)["status"]=="UNVERIFIED"


def test_case_does_not_claim_pass_without_geometry_demand_and_anchor():
    r=c.connection_summary(rho_k=350,rho_m=420,d=12,fu_k=400,t1=45,t_steel=6,n=2,a1=84,kmod=.9,gamma_M=1.3)
    assert r["status"]=="UNVERIFIED"
    assert r["modes"]["governing_mode"]=="a"
    assert r["design"]["group_design_capacity_N"]==pytest.approx(6037.166384551405)
    assert r["utilisation"] is None and r["anchor_utilisation"] is None
    assert "design_shear_N" in r["missing_inputs"]
    assert r["excluded_checks"]


def bracket_case(**overrides):
    values=dict(rho_k=350,rho_m=420,d=12,fu_k=400,t1=45,t_steel=6,n=2,a1=84,kmod=.9,gamma_M=1.3)
    return c.connection_summary(**dict(values,**overrides))


@pytest.mark.parametrize("fastener",["screw","nail_round","nail_other"])
def test_bracket_summary_rejects_unimplemented_nail_and_screw_detailing(fastener):
    with pytest.raises(ValueError,match="bolt/dowel brackets only"):
        bracket_case(fastener=fastener)


def test_bracket_summary_rejects_conflicting_group_and_geometry_spacing():
    # Both 84 and 200 mm pass the bolt spacing minimum, but produce different
    # effective counts. They cannot describe the same physical row.
    with pytest.raises(ValueError,match="same row spacing"):
        bracket_case(a1=200,spacing_actual={"a1":84})
    assert bracket_case(spacing_actual={"a1":84})["spacing"]["checks"]["a1"]["actual_mm"]==84


def test_bracket_summary_retains_thick_plate_applicability_block():
    actual=dict(c.minimum_spacings(12)["minimum_mm"],a1=84)
    result=bracket_case(t_steel=12,spacing_actual=actual,design_shear_N=1,anchor_capacity_N=1000)
    assert result["status"]=="UNVERIFIED"
    assert result["missing_inputs"]==[]
    assert result["unverified_components"]==["modes"]


@pytest.mark.parametrize("op,inputs",[
    ("embedment",dict(rho_k=350,d=31)),
    ("embedment",dict(rho_k=501,d=2.8,fastener="nail_round")),
    ("yield_moment",dict(d=4,fu_k=400,fastener="nail_round")),
    ("yield_moment",dict(d=4,fu_k=600,fastener="nail_other")),
    ("effective_number",dict(n=2.5,a1=84,d=12)),
    ("nail_kef",dict(a1=10,d=2.8)),
    ("slip_modulus",dict(rho_m=420,d=12,steel_factor=3)),
    ("embedment",dict(rho_k=math.nan,d=12)),
    ("embedment",dict(rho_k=350,d=-1)),
])
def test_invalid_or_unverified_inputs_are_rejected(op,inputs):
    with pytest.raises(ValueError):c.evaluate(op,inputs)


def test_parity_vectors_cover_every_operation_and_are_finite():
    vectors=c.parity_cases()
    assert len(vectors)>=70
    assert set(v["operation"] for v in vectors)==set(c.OPERATIONS)
    def walk(x):
        if isinstance(x,float):assert math.isfinite(x)
        elif isinstance(x,dict):
            for value in x.values():walk(value)
        elif isinstance(x,list):
            for value in x:walk(value)
    for case in vectors:
        if case.get("expectedError"):
            with pytest.raises(ValueError):c.evaluate(case["operation"],case["inputs"])
        else:walk(case["expected"])
