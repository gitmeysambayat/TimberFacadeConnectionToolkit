# Timber façade connection calculation guide

Equations, worked examples and implementation references for timber connections, non-structural seismic actions, member section loss in fire and conditional panel racking. The [proposed test and assembly plan](20261018_v3_TestAndAssemblyPlan.html) describes the measurements needed to investigate the wider connection detail.

## Worked-check workflow

| Calculation step | Record |
|---|---|
| Read README, scope and missing inputs in the case JSON. Identify why this is not a complete façade design. | Three blocked checks and their missing inputs. |
| Draw the 6 mm steel plate, 45 mm timber thickness, M12 bolt and one shear plane. Work Exercise 1 without Python. | Embedment, yield moment and governing-mode calculations. |
| Open `connections.py`; trace the same result through `embedment_strength`, `yield_moment` and `steel_to_timber_modes`. Change the load-to-grain angle to 90°. | A comparison explaining the changed embedment strength. |
| Work Exercise 2. Distinguish force demand, reduced drift and full reversing slot travel. | Three separate answers with units. |
| Work Exercise 3. Draw which face reduces the 145 mm depth. Then consider losing material from the 45 mm width instead. | An annotated cross-section explaining why orientation matters. |
| Read Method A. Calculate the width factor and identify the unverified applicability flags. | The conditions required before interpreting a formula result as wall resistance. |
| Run the tests and Python/JavaScript parity check using README instructions. Open the published-example records and their assumptions. | Command, result and the purpose of each check. |
| Answer the 20 questions and compare with the answer key. | Corrected reasoning for any differences. |
| Explain the governing connection mode, seismic demand and fire scope. | The applicable assumptions and unresolved checks. |

## 1. Read the model in the right order

The panel has an assumed area of 2.7 × 1.25 = 3.375 m². Its assumed weight intensity of 0.60 kN/m² gives 2.025 kN. It is a non-structural renovation element attached to an existing frame. The toolkit treats several component calculations separately. A panel force is not automatically one bolt's force; a Johansen resistance is not automatically one bracket's resistance; a reduced stud section is not a fire rating for an insulated assembly.

The principal source links used below are:

- [S1: Swedish Wood/TDUK, Design of timber structures, Volume 2, UK edition 1:2022](https://www.universityofgalway.ie/media/timberengineeringresearchgroup/Design-of-timber-structures_Volume2_Rules-and-formulas-according-to-Eurocode-5.pdf).
- [S2: BS EN 1995-1-1:2004+A1:2008, public copy](https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.1.2004.pdf). The dowel spacing table adopted from S1 explicitly includes A2:2014. Edition and National Annex choices need project confirmation.
- [S3: EN 1995-1-2:2004, public copy with corrigenda](https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.2.2004.pdf).
- [S4: EN 1998-1:2004, public copy](https://www.phd.eng.br/wp-content/uploads/2015/02/en.1998.1.2004.pdf).
- [S5: Swedish Wood, Design of timber structures, Volume 3, 2022 worked examples](https://www.svenskttra.se/siteassets/5-publikationer/pdfer/sw-design-of-timber-structures-vol3-2022.pdf).

The code embeds clause/source metadata. Use the dated source notes for what was actually opened. These links do not establish current national compliance. Units in connection calculations are N, mm, MPa and kg/m³. The seismic module explicitly uses kN for force. A number without its unit can be misleading by factors of 1,000 or 1,000,000.

## 2. Materials, Module A

| Public function | What it does and how to explain it |
|---|---|
| `get_material(grade)` | Returns an independent copy of the verified reference row for C24 or GL24h. Characteristic strength and density are different from mean stiffness and density. Unknown grades are rejected, not approximated. Reference properties are not a supplier declaration for a particular delivered product. |
| `kmod(load_duration, service_class, material_type)` | Looks up a strength modification factor for the chosen duration and moisture environment. The user must choose the applicable case. It is not a multiplier selected merely to make a check pass. Unsupported OSB/3 service-class combinations are rejected. |
| `kdef(service_class, material_type)` | Returns a creep/deformation factor. It is not a strength factor and is not silently applied to the instantaneous slip modulus. |
| `recommended_gamma_m(material_type)` | Returns the explicitly labelled recommended material partial factor. A project's National Annex may differ. |
| `design_strength(fk_MPa, kmod_value, gamma_M)` | Calculates the design strength from the specified characteristic strength and factors. |

The equation is \(f_d=k_{mod}f_k/\gamma_M\), EN 1995-1-1 2.4.1, Equation (2.14). In words, adjust characteristic strength for duration/environment, then divide by the relevant uncertainty factor. The tables are S1 Tables 3.1-3.4 and 9.1; the underlying C24/GL24h property standards are EN 338:2016 and EN 14080:2013. For the illustrative C24 row, characteristic density is 350 kg/m³ and mean density is 420 kg/m³. Do not interchange them: embedment uses characteristic density, whereas the slip-modulus expression uses mean density.

## 3. Connections, Module B

### Local embedment and fastener bending

For screws, supply both the effective diameter `d` and nominal diameter `nominal_d` to `embedment_strength`. The nominal diameter selects the nail or bolt rule. The bolt/dowel case-summary wrapper rejects other fastener types; individual formula functions have their own declared scope. This restriction avoids mixing nominal and effective diameters across detailing and resistance calculations.

`embedment_strength` calculates the timber's local bearing resistance around a laterally loaded fastener. It is not a tensile splitting check. The implemented nail rules are:

\[
f_{h,k}=0.082\rho_k d^{-0.3}\quad\text{without pre-drilling},\qquad
f_{h,k}=0.082(1-0.01d)\rho_k\quad\text{with pre-drilling}.
\]

For bolts/dowels, first obtain \(f_{h,0,k}=0.082(1-0.01d)\rho_k\), then use

\[
f_{h,\alpha,k}=\frac{f_{h,0,k}}{k_{90}\sin^2\alpha+\cos^2\alpha}.
\]

Here \(k_{90}\) is 1.35 + 0.015d for softwood, 1.30 + 0.015d for LVL, and 0.90 + 0.015d for hardwood. Those are the implemented rows, not universal material constants. Diameter and pre-drilling applicability limits are enforced. See S2 8.3.1.1 and 8.5.1.1; S1 pp. 40-44.

`panel_embedment_strength` handles the separate sheathing-side nail embedment. It uses \(65d^{-0.7}t^{0.1}\) for OSB/particleboard, \(30d^{-0.3}t^{0.6}\) for hardboard, and \(0.11\rho_kd^{-0.3}\) for plywood. A nail head diameter of at least twice the shank diameter is an applicability condition. Missing head information leaves the result unverified. These expressions do not supply nail withdrawal or head pull-through resistance. See S2 8.3.1.3 and S1 p. 41.

`yield_moment` estimates the characteristic fastener yield moment. Round nails and bolts use \(M_{y,Rk}=0.3f_ud^{2.6}\); the stated square/grooved nail formula uses 0.45 instead. The smooth-nail formula's strength condition is checked. Other products need a declared/tested override, and screws require the correct effective diameter. A grooved cross-section formula must not silently change the rope-effect classification of an annular nail. See S2 8.3.1.1(4), 8.5.1.1(1); S1 pp. 40 and 44.

### How the Johansen functions choose a mode

`timber_to_timber_modes` evaluates every implemented mode and returns the smallest resistance. A mode represents a possible combination of timber embedment and fastener yielding. The model assumes ductile local mechanisms; it does not verify that brittle splitting or group failure cannot intervene.

To read the single-shear equations compactly, let \(f_1=f_{h,1,k}\), \(\beta=f_{h,2,k}/f_1\), \(r=t_2/t_1\), and \(M=M_{y,Rk}\). The Johansen parts before rope effect are:

\[
J_a=f_1t_1d,\qquad J_b=\beta f_1t_2d,
\]
\[
J_c=\frac{f_1t_1d}{1+\beta}\left[\sqrt{\beta+2\beta^2(1+r+r^2)+\beta^3r^2}-\beta(1+r)\right],
\]
\[
J_d=\frac{1.05f_1t_1d}{2+\beta}\left[\sqrt{2\beta(1+\beta)+\frac{4\beta(2+\beta)M}{f_1dt_1^2}}-\beta\right],
\]
\[
J_e=\frac{1.05f_1t_2d}{1+2\beta}\left[\sqrt{2\beta^2(1+\beta)+\frac{4\beta(1+2\beta)M}{f_1dt_2^2}}-\beta\right],
\]
\[
J_f=1.15\sqrt{\frac{2\beta}{1+\beta}}\sqrt{2Mf_1d}.
\]

For symmetric double shear, the per-plane candidates are \(J_g=f_1t_1d\), \(J_h=0.5\beta f_1t_2d\), \(J_j=J_d\), and \(J_k=J_f\). In this geometry \(t_1\) is an outer timber member and \(t_2\) is the central member. See S2 8.2.2, Equations (8.6)-(8.7); S1 pp. 36-38. Do not use the same thickness interpretation for a different arrangement.

`steel_to_timber_modes` replaces that geometry with the applicable steel/timber arrangement. Define

\[
E=f_htd,\quad B=f_htd\left[\sqrt{2+\frac{4M}{f_hdt^2}}-1\right],\quad
Y_1=1.15\sqrt{2Mf_hd},\quad Y_2=2.3\sqrt{Mf_hd}.
\]

The per-plane Johansen candidates are:

| Arrangement | Candidate values before rope effect |
|---|---|
| Thin steel plate, single shear | a: 0.4E; b: Y1 |
| Thick steel plate, single shear | c: E; d: B; e: Y2 |
| Central steel plate, double shear | f: E; g: B; h: Y2; t is the smaller timber side thickness |
| Outer thin steel plates, double shear | j: 0.5E; k: Y1; t is the full central timber thickness |
| Outer thick steel plates, double shear | l: 0.5E; m: Y2; t is the full central timber thickness |

A plate at or below 0.5d is thin. A plate at or above d is thick only with the stated hole-fit condition. The primary standard says hole-diameter tolerance **less than** 0.1d. Intermediate thickness interpolates the limiting thin/thick capacities. It does not interpolate an arbitrarily chosen pair of mechanism values. Central steel uses its own expressions regardless of plate thickness; steel strength still needs checking. See S2 8.2.3, Equations (8.9)-(8.13); S1 pp. 38-39.

Rope effect is an additional contribution, not the entire axial resistance. Where the equation allows it, the code adds the smaller of \(F_{ax,Rk}/4\) and a specified fraction of that mode's Johansen part. Caps are 15% round nails, 25% square/grooved nails, 50% other nails, 100% screws, 25% bolts and zero for dowels. No contribution is added to pure embedment modes without the term. The smallest adjusted mode then governs. These caps come from S2 8.2.2(2) and S1 p. 38. Unknown axial resistance is neglected, not invented.

### Groups, geometry and deformation

| Function | Plain-language explanation |
|---|---|
| `nail_kef` | Interpolates the tabulated nail group exponent using spacing divided by diameter. The without-pre-drilling points are 7d: 0.7; 10d: 0.85; 14d: 1.0. With pre-drilling, 5d: 0.5 is also available. Below the verified table range the function refuses a result. S2 Table 8.1; S1 Table 10.1, p. 41. |
| `effective_number` | Accounts for a row not necessarily sharing load as perfectly as n independent fasteners. For bolts/dowels parallel to grain, use the smaller of n and \(n^{0.9}[a_1/(13d)]^{0.25}\). Perpendicular loading uses n; intermediate bolt angles interpolate between these limits. Parallel nail rows use \(n^{k_{ef}}\), subject to the stated staggering/perpendicular exceptions. Intermediate nail-angle interpolation is deliberately unverified. S2 8.3.1.1 and 8.5.1.1(4), Equation (8.34); S1 pp. 41, 45. |
| `minimum_spacings` | Calculates required a1/a2 spacing, a3 loaded/unloaded end distance and a4 loaded/unloaded edge distance for the selected family. It uses the principal load-to-grain angle but maps the opposite end correctly. Nail panel/steel reductions affect spacing only, not every end/edge distance. Nail spacing is subject to national choices. The dowel table explicitly includes A2:2014. S2 Tables 8.2, 8.4, amended 8.5; S1 Tables 10.2, 10.4-10.5. |
| `check_spacings` | Compares actual dimensions with those minima. Missing dimensions stay unverified. A calculated minimum is not evidence that a real drawing provides it. |
| `slip_modulus` | Estimates force/slip stiffness per fastener per shear plane. Table 7.1 uses \(\rho_m^{1.5}d/23\) for the implemented dowel/bolt/screw/pre-drilled-nail categories and \(\rho_m^{1.5}d^{0.8}/30\) for unpredrilled nails. A geometric-mean density may be used for two timber members. The exposed optional steel/concrete factor is 2; \(K_u=2K_{ser}/3\). Bolt clearance slip is additional. S2 7.1, Table 7.1, 7.1(3), 2.2.2(2); S1 p. 33. |
| `design_capacity` | Applies \(k_{mod}/\gamma_M\) to per-plane characteristic resistance, then multiplies by the effective count and the correct number of shear planes. It does not perform the missing geometry, anchorage or steel checks. |
| `connection_summary` | Assembles the selected single-shear bracket subcase, component values and missing inputs. A force-to-capacity ratio exists only if demand is supplied. A scalar anchor capacity does not replace checking its ETA, substrate, group and interaction conditions. |
| `published_examples` | Reproduces the documented resistance subcalculations in S5 Examples 4.1 and 4.2, including effective screw diameter, rope-effect assumptions and each example's kmod/gamma. It does not certify the examples' complete structural details or provide an independent experimental validation. |

For the case M12 bolt at 0°: a1 ≥ 60 mm, a2 ≥ 48 mm, loaded end ≥ 84 mm, unloaded end ≥ 48 mm and both edge distances ≥ 36 mm under the stated table interpretation. Only a1 = 84 mm is supplied. The other actual dimensions remain missing. These six entries are distinct dimensions, not six bolts.

## 4. Seismic demands, Module E

`seismic_coefficient` calculates

\[
S_a=\alpha S\left[\frac{3(1+z/H)}{1+(1-T_a/T_1)^2}-0.5\right],\qquad S_a\geq\alpha S.
\]

The period ratio describes proximity to resonance with the supporting building. Height matters through z/H. The coefficient is dimensionless, so do not supply ag in m/s² where alpha = ag/g is required. z and H share the same reference level. `seismic_force_kN` then calculates \(F_a=S_aW_a\gamma_a/q_a\), acting at the element's centre of mass in the unfavourable horizontal direction. These are S4 4.3.5.2, Equations (4.24)-(4.25), printed pp. 67-68. Particularly important/dangerous elements require a more realistic supporting-structure response model under 4.3.5.1.

| Function | What to understand |
|---|---|
| `panel_weight_kN` | Converts mm² to m² and multiplies by the supplied weight intensity. Include insulation and fittings in mass even if they provide no structural resistance. |
| `facade_behaviour_factor` | Checks an explicitly chosen qa against the study domain and Table 4.4 facade upper limit of 2.0. The upper limit does not demonstrate the behaviour of a particular bracket or anchor. |
| `recommended_nu` | Returns the recommended damage-limitation reduction: I/II 0.5, III/IV 0.4. National Annex values may differ. |
| `drift_check` | Checks \(d_r\nu\leq ch\), with c = 0.005 brittle attached, 0.0075 ductile or 0.010 non-interfering. The result reports both the reduced right-hand-side limit and the equivalent unreduced dr limit. Classification must be justified. See S4 4.4.3.2, Equations (4.31)-(4.33), printed pp. 76-77. |
| `bracket_forces` | Multiplies whole-panel force by each explicitly supplied load share, requiring non-negative shares summing to one. It does not establish equal sharing, eccentricity or torsional distribution. Null shares block per-bracket demand. |
| `slot_length_mm` | Applies a declared geometric model: a centred friction-free sliding bracket needs travel in both directions, so L = bolt diameter + twice full relative movement + total added allowance. Full movement is assumed to equal dr unless the explicit kinematic factor changes it. This is not a Eurocode resistance/detailing rule; nu does not reduce the full-drift slot requirement. |
| `case_summary` | Combines the panel action, selected drift inequality and slot geometry. It preserves the missing bracket-load-share and ETA information and returns no overall design pass. |

## 5. Fire, Module D

This module studies an **isolated, unprotected member** under the standard-fire idealisation. It does not assess the actual insulated renovation assembly, a lining, a cavity, connections or fire separation. Do not call a residual depth at 60 minutes an R60 or EI60 classification.

`fire_parameters` selects only source-confirmed material/density rows. For the illustrative C24 softwood, beta0 = 0.65 mm/min and betan = 0.8 mm/min; the latter represents notional charring, including its stated geometric allowances. Different confirmed rows apply to glulam/LVL. Source conditions must accompany each row. See S3 Table 3.1 and Table 2.1.

`charring_depths` returns

\[
d_{char,0}=\beta_0t,\quad d_{char,n}=\beta_nt,\quad
d_{ef}=d_{char,n}+k_0d_0,\quad d_0=7\text{ mm},\quad k_0=\min(t/20,1).
\]

The additional zero-strength layer accounts for degraded material beyond the notional char line. `effective_char_depth` is a scalar convenience function for the same effective-depth equation. It is not an independent fire model. See S3 3.4.2 and 4.2.2, Equations (3.1)-(3.2), (4.1), Table 4.1.

`reduced_section_rectangular` subtracts this effective loss from the explicitly named exposed faces. `depth_front` reduces depth, whereas `width_left` reduces width. It returns both physical notional-char residual dimensions and effective dimensions. Elementary section formulae are \(A=bh\), \(I_y=bh^3/12\), \(W_y=bh^2/6\), with b and h interchanged for the other axis. One-sided loss shifts the centroid by half the removed depth while material remains. Compression originally acting at the old centroid can therefore become eccentric; the toolkit does not treat it as an automatically concentric compression check. Protected/insulated-assembly options are rejected.

`check_fire_bending` uses \(f_{20}=k_{fi}f_k\), \(f_{d,fi}=k_{mod,fi}f_{20}/\gamma_{M,fi}\) and \(M_{Rd,fi}=f_{d,fi}W_{ef}\). The reduced-section method fixes kmod,fi = 1.0. GammaM,fi = 1.0 is an exposed recommended NDP; the verified solid-timber kfi row is 1.25. See S3 2.3, Equations (2.1), (2.4), Table 2.1, and 4.2.2(5). Demand must be supplied from a justified fire-action combination. A null moment leaves the check blocked. This function checks uniaxial section bending only, not member stability or combined actions.

## 6. Racking, Module C

`method_a_geometry` obtains \(b_0=h/2\), \(c_i=\min(1,b_i/b_0)\), and checks \(b_i\geq h/4\). A narrower sheet reduces the formula resistance; a sheet below the applicability bound cannot be made acceptable by simply reporting a small result.

`method_a_panel` calculates

\[
F_{i,v,Rd}=\frac{F_{f,Rd}b_ic_i}{s}.
\]

The implementation distinguishes Section 8 fastener resistance from the Method A sheet-edge resistance. It applies the 1.2 sheet-edge enhancement in 9.2.4.2(5) once, unless the supplied value already includes it. Tie-downs, openings, regular spacing, sheet-edge detailing and fixing verification must be explicitly confirmed. A formula value may be displayed while applicable capacity remains null. See S2 9.2.4.1-9.2.4.2, Equations (9.21)-(9.23); S1 pp. 49-50. Stud buckling/bearing, sheet buckling, inter-element transfer, serviceability and full anchorage are additional checks. Method A's national acceptance also needs confirmation.

## 7. Dispatch, verification and integration functions

These functions are public because they make the study repeatable. They add no new structural formulae.

| Function | Purpose |
|---|---|
| Each module's `evaluate(operation, inputs)` | Gives a named calculation operation the explicit inputs from a JSON-compatible dictionary. It is the same interface used for Python/JavaScript comparisons. Dispatch does not convert an unknown operation into a guess. |
| Each module's `parity_cases()` | Produces fixed input vectors and full-precision Python outputs for the browser implementation. Agreement detects transcription/implementation drift. Two implementations agreeing does not independently validate the underlying physical model. |
| `study.connection_inputs(case)` | Maps descriptive case JSON fields and nullable dimensions to the connection function's names and units. |
| `study.seismic_inputs(case)` | Maps case fields and converts the short category `brittle` to `brittle_attached`. No new seismic value is inferred. |
| `study.calculate_case(case)` | Runs component calculations, applies the explicit slot options and reports missing inputs. It also computes elementary area times pressure for characteristic wind. It generates no wind design combination and no overall design-pass flag. |
| `study.verification_rows()` | Compares selected outputs with separately stated hand values and published-example results. Tolerance follows the reference's printed rounding. It does not round intermediate calculations to force agreement. |
| `study.plot_data(case)` | Builds the three sensitivity datasets: bolt diameter, element height and fire duration. Fixed geometry in the diameter sweep can change plate class or fail detailing. A higher mathematical resistance does not mean the new bolt fits or is acceptable. |
| `study.figures(data)` | Draws the dated PNG figures from those result datasets. It does not run another solver. |
| `study.main()` | Reads the dated editable JSON, calculates results, verifies comparison rows, writes dated JSON/CSV/figures and exports combined parity vectors. Run it from the repository using `python -m timberkit.study`. |
| `build_web.assets()` | Reads the local mathematical-rendering stylesheet, embedded fonts and JavaScript assets. These format equations; they do not calculate structural resistance. |
| `build_web.build_tool()` | Embeds case data, verification fixtures, calculation code and the local rendering assets into the dated standalone HTML and `index.html`. It assembles the interface without publishing anything. |
| `build_web.main()` | Invokes that local page build and reports its output size. Generating a file is separate from opening, inspecting or publishing it. |

Functions beginning with an underscore validate inputs, map an angle, or assemble status metadata. They are supporting utilities, not additional engineering models. `__version__` records the package version. The browser modules reproduce the corresponding calculation functions and `evaluate` interface; their operation and plots must be checked against the exported vectors rather than visually judged alone.

## 8. Three worked hand exercises

### Exercise 1: one thin-plate bolt subcase

Use rho,k = 350 kg/m³, rho,m = 420 kg/m³, d = 12 mm, fu = 400 MPa, t = 45 mm, steel thickness 6 mm and alpha = 0°. Neglect rope effect. Take the illustrative kmod = 0.9, gammaM = 1.3 and two bolts at a1 = 84 mm in one row. **Do the following arithmetic yourself before opening the answers.**

1. Embedment: 0.082 × (1 − 0.01 × 12) × 350 = **25.256 MPa**.
2. Yield moment: 0.3 × 400 × 12^2.6 = **76,745.4233 N mm**, or 76.7454 kN mm.
3. Thin classification: 6 = 0.5 × 12 mm. Mode a = 0.4 × 25.256 × 45 × 12 = **5,455.296 N**. Mode b = 1.15 × sqrt(2 × 76,745.4233 × 25.256 × 12) = **7,843.5377 N**. Therefore mode a governs at 5.45530 kN per fastener per shear plane.
4. Per-plane design resistance: 0.9 × 5,455.296 / 1.3 = **3,776.7434 N**.
5. Effective count: min(2, 2^0.9 × (84/(13 × 12))^0.25) = **1.59851114**. The calculated group design resistance is **6,037.1664 N**, subject to the unverified detail and excluded failure mechanisms.
6. Base slip modulus: 420^1.5 × 12 / 23 = **4,490.8376 N/mm**. With the explicitly selected optional steel factor 2, it becomes **8,981.6751 N/mm**; corresponding Ku is **5,987.7834 N/mm**. The brief's 4.49 and 2.99 kN/mm values describe the base values without that factor. Neither choice incorporates bolt clearance.

There is no overall connection pass: actual end/edge distances, design demand and ETA anchorage are missing. In particular, the 45 mm timber thickness does not tell you the rail's available edge distance in the drawing. Follow-up: change alpha to 90°. The softwood k90 is 1.53, so embedment becomes 25.256/1.53 = **16.50718954 MPa**. Recalculate both modes and the group count rather than changing only one number. Sources: S2 Section 8, 7.1 and 2.4.1; S1 pp. 33, 36, 38, 44-45.

### Exercise 2: panel force, drift and slot travel

Use the case seismic inputs. First keep every intermediate value unrounded.

1. z/H = 0.8 and Ta/T1 = 0.1. The bracketed spectral expression is 5.4/1.81 − 0.5 = 2.4834254144.
2. Sa = 0.20 × 1.15 × 2.4834254144 = **0.5711878453**. The minimum is 0.23, so it does not govern.
3. Weight = 2.7 × 1.25 × 0.60 = **2.025 kN**. Fa = 0.5711878453 × 2.025 × 1/2 = **0.5783276934 kN**.
4. The case has no verified bracket shares. For an **additional arithmetic exercise only**, explicitly assume two identical translational supports share 0.5 each: each demand is **0.2891638467 kN**. This assumption must not be transferred to the actual case without a load-path justification.
5. With dr = 15 mm, h = 3,000 mm and nu = 0.5, reduced drift demand is **7.5 mm**. Right-hand-side limits are **15.0, 22.5 and 30.0 mm** for the three categories. All three numerical inequalities are satisfied for those assumed inputs, but actual classification is not proved. The equivalent unreduced dr limits are 30, 45 and 60 mm.
6. Slot geometry uses full ±15 mm travel, not ±7.5 mm. A centred 12 mm bolt needs **42 mm** overall slot length before extra installation allowance. The expression proves only the chosen geometry, not bearing, friction, retained support or resistance.

Sources: S4 4.3.5.2, Table 4.4 and 4.4.3.2. Slot geometry and support shares are explicitly declared study assumptions, not sourced Eurocode design rules.

### Exercise 3: one-face unprotected stud

Use width 45 mm and depth 145 mm. Expose `depth_front`, so the 145 mm dimension shrinks. Use betan = 0.8 mm/min and d0 = 7 mm.

| Time | k0 | Notional char depth | Effective loss | Effective section | Wy |
|---|---:|---:|---:|---|---:|
| 10 min | 0.5 | 8 mm | 11.5 mm | 45 × 133.5 mm | 133,666.875 mm³ |
| 30 min | 1.0 | 24 mm | 31 mm | 45 × 114 mm | 97,470 mm³ |
| 60 min | 1.0 | 48 mm | 55 mm | 45 × 90 mm | 60,750 mm³ |

At 30 minutes, A = 45 × 114 = **5,130 mm²**, Iy = 45 × 114^3 / 12 = **5,555,790 mm⁴** and the centroid shift is 31/2 = **15.5 mm**. Physical notional-char residual depth is 121 mm; effective depth is 114 mm. These are not interchangeable.

For an **additional section-arithmetic exercise only**, specify a 1.0 kN m fire moment about y. With fm,k = 24 MPa, kfi = 1.25, kmod,fi = 1 and gammaM,fi = 1, fd,fi = **30 MPa**. Section moment resistance is 30 × 97,470 = **2,924,100 N mm = 2.9241 kN m**. The section-only ratio is approximately **0.342**. The actual case leaves fire moment null because no fire-action analysis has been supplied. Neither the exercise nor the remaining depth gives the façade an R30/R60 rating. Sources: S3 3.4.2, 4.2.2 and 2.3.

## 9. Twenty multiple-choice questions

Choose one answer each before reading the key.

1. Which density enters the bolt embedment expression? A mean density; B characteristic density; C steel density.
2. Which density enters the listed Table 7.1 slip expression? A mean density; B characteristic density; C insulation density.
3. A 6 mm plate and 12 mm bolt are classed as: A thick; B intermediate; C thin.
4. A 12 mm plate alone proves thick-plate applicability for an M12 bolt: A yes; B no, the hole-fit condition also matters; C only if the timber is C24.
5. Johansen double-shear values in this toolkit are initially reported: A per shear plane; B as the total of every fastener; C per metre of wall.
6. A bolt's rope contribution is: A always 25% extra; B its whole axial resistance; C bounded by both Fax/4 and the 25% Johansen cap where applicable.
7. Five bolts at 7d have an effective count about 3.646. This means: A the physical count changes; B row action reduces the count used in resistance; C two bolts can be removed automatically.
8. Missing actual end distance should produce: A automatic pass; B zero required distance; C unverified geometry.
9. The optional steel multiplier 2 applies here to: A slip modulus; B every strength; C panel weight.
10. Which is the exact case weight before rounding? A 2.025 kN; B 2.03 kg; C 0.60 kN.
11. Which period relation maximises the stated Sa expression for fixed height? A Ta = T1; B Ta infinitely large; C periods are irrelevant.
12. The facade Table 4.4 value qa = 2.0 is: A a universal measured ductility; B an upper limit for a listed category; C an anchor ETA.
13. With dr = 15 mm and nu = 0.5, drift demand for the damage-limitation inequality is: A 30 mm; B 15 mm; C 7.5 mm.
14. A centred slot accommodating full reversing ±15 mm movement with a 12 mm bolt and zero added allowance has geometric length: A 27 mm; B 42 mm; C 15 mm.
15. Which loss is used for the effective section in this reduced-section method? A beta0 times t only; B notional char plus the zero-strength allowance; C the zero-strength allowance only.
16. At 10 minutes k0 is: A 0.5; B 1.0; C 7.0.
17. A 60-minute residual depth proves an R60 façade classification: A yes; B yes if insulation is non-structural; C no.
18. Method A's reference width b0 is: A h/2; B h/4; C twice h.
19. A numeric Method A formula value with unknown tie-downs is: A verified whole-wall capacity; B a conditional arithmetic result with applicability blocked; C independent of anchorage.
20. Passing Python/JavaScript parity proves: A that two implementations agree for tested vectors; B experimental validation; C that every source provision applies to an actual connection.

### Answer key with reasons

1 **B**, the embedment formula uses rho,k. 2 **A**, the stiffness formula uses rho,m. 3 **C**, equality at 0.5d belongs to thin. 4 **B**, thickness and fit both enter the stated classification. 5 **A**, multiply by shear planes once only. 6 **C**, neither cap nor axial contribution can be assumed away. 7 **B**, effective number is a calculation model, not a revised drawing. 8 **C**, absence of evidence is not a dimensional pass. 9 **A**, the exposed factor is the specified stiffness option. 10 **A**, area times weight intensity is 2.025 kN. 11 **A**, the squared difference in the denominator vanishes. 12 **B**, the table does not qualify the actual detail. 13 **C**, the inequality compares dr times nu. 14 **B**, 12 + 15 + 15 = 42 mm. 15 **B**, effective loss includes both contributions. 16 **A**, 10/20 = 0.5. 17 **C**, member geometry is not assembly fire classification. 18 **A**, the method defines b0 = h/2; h/4 is a separate applicability bound. 19 **B**, load path and applicability remain required. 20 **A**, parity is implementation agreement, not independent physical validation.

## Record independent calculation checks

The optional `learner_verification_records` array in the case-study JSON can hold a date, equation or function, calculation method and observed difference. These records are separate from the supplied implementation checks. An empty array is metadata, not a calculation input.
