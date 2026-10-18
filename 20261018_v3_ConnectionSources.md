# Connection module sources and verification

18 October 2026, public version 3. Connection module source record. Educational calculations, not for design. The Python and JavaScript were developed with AI assistance. The source-inspection record below distinguishes opened sources, arithmetic benchmarks and implementation checks. It does not report physical testing.

## Sources actually opened

| Source ID | Exact public source | Extent inspected and use |
|---|---|---|
| SW2_2022_UK | [Swedish Wood, Design of timber structures, Volume 2, UK edition 1:2022](https://www.universityofgalway.ie/media/timberengineeringresearchgroup/Design-of-timber-structures_Volume2_Rules-and-formulas-according-to-Eurocode-5.pdf) | Opened as a 60-page PDF, downloaded, text-extracted, and relevant equation pages rendered. Printed pp33, 36-45 were visually inspected. Used for connection equations, mode diagrams, rope caps, embedment, yield moment, effective number, spacing and slip. |
| SW3_2022 | [Swedish Wood, Design of timber structures, Volume 3, edition 3:2022](https://www.svenskttra.se/siteassets/5-publikationer/pdfer/sw-design-of-timber-structures-vol3-2022.pdf) | Opened as a 60-page PDF, downloaded and rendered. Examples 4.1 and 4.2, printed pp20-24, were read, with numerical equations on pp21, 23 and 24 visually inspected. |
| EC5_PUBLIC_2004_A1 | [Public copy of BS EN 1995-1-1:2004+A1:2008](https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.1.2004.pdf) | Opened as a 123-page public copy of the original standard. Used to cross-check clause/equation references, the optional steel multiplier in 7.1(3), ultimate slip modulus in 2.2.2(2), plate classification and the distinction between nail spacings and end/edge distances. This host is not an official current standards subscription. |

The public copy includes A1:2008. The UK handbook's dowel-spacing table specifically cites A2:2014. The implementation follows the requested EN 1995-1-1:2004 framework with those source amendments explicitly identified. It does not verify a current national adoption, a complete National Annex, a product ETA or a later Eurocode edition. The UK handbook itself explains that it is an educational publication and that original standards are required for practical design.

Source PDFs are linked rather than redistributed. The formula sources remain accessible through the links above.

## Formula and clause map

| Implementation | Reference and inspected source | Scope and coefficient handling |
|---|---|---|
| Nail timber embedment, pre-drilled and not pre-drilled | EN 1995-1-1 8.3.1.1; SW2 p41 | Diameter up to 8 mm. Requires pre-drilling above the source's density/diameter thresholds. These are side-grain formulae, not an end-grain approval. |
| Bolt/dowel embedment and angle correction | EN 1995-1-1 8.5.1.1(2)-(3), Eqs8.31-8.33; SW2 p44 | Diameter up to 30 mm. Softwood, LVL and hardwood have distinct input-selected correction factors. Material density is an explicit input. |
| Panel nail embedment | EN 1995-1-1 8.3.1.3; SW2 p41 | OSB/particleboard, hardboard and plywood branches. Nail-head diameter at least twice nominal diameter is an applicability condition. Missing/insufficient head size is UNVERIFIED, even though a conditional numerical embedment estimate is shown. |
| Nail yield moment | EN 1995-1-1 8.3.1.1(4); SW2 p40 | Round coefficient 0.3 and square/grooved coefficient 0.45 after substituting the source's tensile-strength scaling. The source's smooth-nail rule requires tensile strength at least 600 MPa. Other/proprietary nails require declared yield moment. |
| Bolt/dowel yield moment | EN 1995-1-1 8.5.1.1(1), Eq8.30; SW2 p44 | Tensile strength and diameter are explicit inputs. Screw callers supply the applicable effective diameter under 8.7.1 and the nominal diameter used to select the 6 mm rule; the program does not infer thread dimensions or manufacturer properties. The combined bracket summary is restricted to bolts and dowels. |
| Timber-to-timber single shear | EN 1995-1-1 8.2.2, Eq8.6, modes a to f; SW2 p36 | All six modes reported. Different embedment strengths enter through their ratio. |
| Timber-to-timber double shear | EN 1995-1-1 8.2.2, Eq8.7, modes g, h, j and k; SW2 p37 | Equivalent outer members assumed. Controlling outer thickness/penetration is t1; central timber thickness is t2. Capacity is per shear plane. Unequal independent outer-member material/geometry combinations are not verified. |
| Steel single shear | EN 1995-1-1 8.2.3, Eq8.9 thin a/b and Eq8.10 thick c/d/e; SW2 p38 | Thin at plate thickness no more than half the fastener diameter; thick at thickness at least diameter with the required hole fit. |
| Steel central member, double shear | EN 1995-1-1 8.2.3, Eq8.11, f/g/h; SW2 p38 | Any central steel thickness in the stated idealisation; controlling timber side thickness is t1. Steel resistance remains a separate check. |
| Steel outer members, double shear | EN 1995-1-1 8.2.3, Eqs8.12 and 8.13, j/k and l/m; SW2 p39 | API t1 is explicitly the full central timber thickness, corresponding to the standard's t2 in this configuration. Capacity is per shear plane. |
| Intermediate steel thickness | EN 1995-1-1 8.2.3(1); SW2 p39 | Linearly interpolates the limiting thin and thick capacities. It does not take the minimum of all limiting modes as an intermediate capacity, or invent a paired intermediate failure mode. Both limiting mode sets are reported. |
| Rope effect | EN 1995-1-1 8.2.2(2), 8.2.3(4); SW2 p38 | Only the identified yielding modes receive the smaller of one-quarter supplied axial resistance and the applicable percentage of that mode's Johansen term. No addition to pure-embedment modes. Zero/unknown axial input is explicitly neglected, not declared physically zero. |
| Bolt/dowel effective number | EN 1995-1-1 8.5.1.1(4), Eq8.34; SW2 p45 | One row. Parallel expression, perpendicular count and permitted linear interpolation in principal angle. One fastener has no group reduction. The input count is an integer. |
| Nail effective number | EN 1995-1-1 8.3.1.1, Table8.1; SW2 p41 Table10.1 | Linear interpolation of the supplied spacing table, not extrapolation below its minimum. Intermediate-angle nail grouping is UNVERIFIED rather than borrowing the bolt interpolation. |
| Nail spacing/end/edge distances | EN 1995-1-1 8.3.1.2 Table8.2, 8.3.1.3 and 8.3.1.4; SW2 p42 | Density and pre-drilling branches. Panel/steel factors reduce spacings a1/a2 only; end and edge distances remain unchanged. The handbook marks the table as NDP, so the output explicitly records applicable National Annex choices as UNVERIFIED. Confirmed minima can be supplied directly to check_spacings. |
| Bolt spacing/end/edge distances | EN 1995-1-1 8.5.1.1 Table8.4; SW2 p45 Table10.4 | Principal input angle from zero to 90 degrees; unloaded-end branch evaluated with the corresponding angle 180 degrees minus that input. |
| Dowel spacing/end/edge distances | EN 1995-1-1 8.6, amended table; SW2 p45 Table10.5 citing A2:2014 | Scope limited to diameter 6 to 30 mm. The unloaded-end branch uses the table's piecewise expressions. |
| Slip modulus | EN 1995-1-1 7.1/Table7.1, 7.1(3); SW2 p33 Table9.2 | Per shear plane and fastener. Timber-to-timber mixed density uses the geometric mean of the two mean densities. Steel factor is explicitly 1 or 2 because the original clause permits, rather than universally mandates, multiplying by 2. |
| Ultimate slip modulus | EN 1995-1-1 2.2.2(2), Eq2.1; opened public copy printed pp19-20 | Two-thirds of the selected service slip modulus. Bolt-hole-clearance slip is additional. |
| Design resistance | EN 1995-1-1 2.4.1/Section8; SW2 p36 | Modification factor and material partial factor are explicit inputs. The program does not silently choose a National Annex. Recommended factors must remain labelled as such by the caller. |

All reported Johansen values are **per fastener per shear plane**. The separate `per_fastener_total_N` value multiplies by the number of shear planes. A double-shear result must not be multiplied by two at both stages.

The thick-plate condition in the opened original English standard is hole-diameter tolerance **less than** 0.1 times diameter. The handbook's condensed wording uses an inclusive sign. The code adopts the original strict condition, treating the exact boundary as UNVERIFIED. A small numerical guard prevents binary rounding from accidentally admitting the exact boundary. This is a classification condition, not proof of steel plate/fastener resistance.

## Published reproductions and rounding

| Published example and quantity | Published value | Unrounded toolkit result | Comparison |
|---|---:|---:|---|
| SW3 Example4.1, mode c | 9.91 kN | 9.910434 kN | Agrees at printed precision |
| Example4.1, mode d and governing characteristic resistance | 4.83 kN | 4.831703 kN | Agrees at printed precision |
| Example4.1, mode e | 5.26 kN | 5.257049 kN | Agrees at printed precision |
| Example4.1, total design resistance for 12 screws | 29.0 kN | 28.990220 kN | Agrees at printed precision |
| SW3 Example4.2, governing Johansen resistance before rope | 1,607 N | 1,606.949 N | Agrees at printed precision |
| Example4.2, resistance including supplied axial term | 1.70 kN | 1.702699 kN | Agrees at printed precision |
| Example4.2, design resistance per nail | 1.05 kN | 1.047815 kN | Agrees at printed precision |

**Example4.1 inputs and scope:** glulam characteristic density 390 kg/m³; screw effective diameter assumed equal to 8 mm by the book; tensile strength 410 MPa; timber penetration 52 mm; steel thickness 8 mm; angle 45 degrees; 12 screws. Rope is neglected as in the book. Hole fit is assumed for reproducing its thick-plate idealisation. The total multiplication by 12 follows the published example and does not add an independent verification of its row layout, splitting, screw withdrawal, group effects or plate strength.

**Example4.2 inputs and scope:** annular ring-shanked nail diameter 4 mm, tensile strength 600 MPa, penetration 35 mm, steel thickness 5 mm and timber density 390 kg/m³. The book explicitly simplifies the yield moment using its grooved-nail equation. That simplification is preserved and disclosed for reproduction only. The rope category is other nails with its 50% cap, independently of the yield-moment cross-section assumption. The limiting published rounded axial resistance 383 N is supplied, giving an addition 95.75 N. Product-declared yield and axial properties are still required in actual work. No full Gerber, steel, perpendicular-to-grain or splitting design is claimed.

**National parameters:** both reproductions use material partial factor 1.3 for connections. Example4.1 uses modification factor 0.65 for medium-duration loading/service class3, and Example4.2 uses 0.8 for medium-duration loading/service class2. These match the corresponding recommended values in the opened handbook. No different National Annex factor has been invented. They differ from the illustrative case-study short-term factor 0.9 because the stated duration/service classes differ, not because the toolkit silently changes national choices.

## Requested hand values and illustrative bracket

For characteristic density 350 kg/m³, mean density 420 kg/m³, diameter 12 mm and tensile strength 400 MPa, the unrounded results are:

- Parallel embedment 25.256 MPa, which rounds to the requested 25.3 MPa.
- Yield moment 76,745.423 N mm, which rounds to 76.7 kN mm.
- Base service slip modulus 4,490.838 N/mm, which rounds to 4.49 kN/mm. Base ultimate modulus is 2,993.892 N/mm, which rounds to 2.99 kN/mm.
- Five bolts at spacing seven diameters give effective number 3.646378, which rounds to 3.65.

For the illustrative steel bracket, the optional steel multiplier of 2 gives service slip modulus 8,981.675 N/mm and ultimate modulus 5,987.783 N/mm. The base 4.49 kN/mm benchmark and doubled steel value must not be conflated.

With 45 mm assumed timber penetration, 6 mm plate, two bolts in one grain-parallel row at 84 mm centres, modification factor 0.9, material factor 1.3 and neglected rope, the thin-plate mode a gives 5,455.296 N and mode b gives 7,843.538 N per bolt/shear plane. Mode a governs. Effective number is 1.598511, and the calculated Johansen group design resistance is 6,037.166 N. This is a conditional calculation, not the complete bracket capacity. End/edge distances, other required layout dimensions, the true load path, design demand and manufacturer ETA anchor resistance are not inferred. The summary therefore remains UNVERIFIED.

## Software verification and interface

`timberkit/connections.py` and `web/connections.js` implement matching `evaluate(operation, inputs)` dispatchers. JavaScript exposes `globalThis.TFKConnections`. Python `parity_cases()` supplies operation/input/expected dictionaries for root integration. The operations are embedment, panel_embedment, yield_moment, timber_modes, steel_modes, effective_number, nail_kef, minimum_spacings, check_spacings, slip_modulus, design_capacity and connection_summary. `published_examples()` supplies the two reproduction records for the shared verification table.

The release verification summary records the current integrated tests, published-example comparisons and Python/JavaScript parity. These checks cover numerical implementation and stated input boundaries; they do not establish physical performance.

## Unverified or excluded matters

- Actual bracket force direction, eccentricity, distribution between fixings and out-of-plane behaviour.
- Concrete anchor product/ETA, substrate condition, edge/group effects and applicable resistance.
- Actual end/edge distances and any omitted row geometry. With one row, a caller may need to identify genuinely inapplicable between-row checks rather than invent a distance.
- Steel plate/fastener steel resistance, bearing, block/plug shear, timber splitting/net section and prying.
- Actual nail/screw product yield and axial properties, required head dimensions and effective diameters.
- Applicable National Annex choices, with the nail-spacing NDP flag retained.
- Intermediate-angle nail group interpolation, independent unequal outer-member double-shear details and end-grain connection rules.
- Cyclic behaviour, installation quality, deterioration, moisture history, creep and connection fire resistance.

No physical test, product calibration, installation, approval or finite-element analysis is represented by this module.
