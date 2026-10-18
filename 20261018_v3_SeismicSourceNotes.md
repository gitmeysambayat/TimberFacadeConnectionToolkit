# Seismic actions and movement sources

Source provisions and implementation checks for non-structural seismic actions, drift and connection movement.

## Primary source actually opened

[BS EN 1998-1:2004, English text of EN 1998-1:2004](https://www.phd.eng.br/wp-content/uploads/2015/02/en.1998.1.2004.pdf). Downloaded and opened locally; printed pages 67, 68, 76 and 77 were extracted, rendered and visually inspected. The 231-page PDF has SHA-256 `9c073425aa311fb5dcd8dc210281b9310de74cb2f3f66b46edd16b65385317e9` and 6,635,962 bytes. Accessed 18 October 2026. The calculations use this 2004 edition; the applicable project edition requires confirmation.

| Implemented quantity | Exact clause/equation | Scope or qualification |
|---|---|---|
| Dimensionless Sa | 4.3.5.2(3), Equation (4.25), printed pp. 67-68 | Lower bound alpha times S; heights share the foundation/rigid-basement datum |
| Horizontal Fa | 4.3.5.2(2), Equation (4.24), printed p. 67 | Centre-of-mass action in the most unfavourable direction |
| gamma-a | 4.3.5.3, printed p. 68 | Mandatory input; ordinary elements may use 1.0, specified life-safety/hazardous cases require at least 1.5 |
| Facade qa ceiling | 4.3.5.4, Table 4.4, printed p. 68 | 2.0 is an upper limit for the listed facade/wall/partition category, not qualification of a bracket detail |
| Reduced drift limits | 4.4.3.2(1), Equations (4.31)-(4.33), printed p. 76 | Category must be justified; limit applies to dr times nu |
| Recommended nu | 4.4.3.2(2) Note, printed pp. 76-77 | I/II: 0.5; III/IV: 0.4. National Annex may differ; explicit caller input |

The simplified action model also requires justification under 4.3.5.1. Particularly important or dangerous elements require a realistic supporting-structure response model. No existing-concrete anchorage capacity is supplied.

## Public corroboration actually opened

- [Soos and Vigh, WCEE 2012, paper 4980](https://www.iitk.ac.in/nicee/wcee/article/WCEE2012_4980.pdf), PDF p. 2, Table 2.1. Confirms the three drift inequalities and importance-class reduction factors. The authors also explain the difficulty of classifying non-structural behaviour. The toolkit therefore does not infer a ductile category from a timber material label.
- [JRC, Eurocode 8 seismic design worked examples](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EC8_Seismic_Design_of_Buildings-Worked_examples.pdf), Section 5.17.4, printed p. 150. Confirms a non-interfering drift example using nu = 0.5 for importance class II.
- The supplied [Eurocode Applied page](https://eurocodeapplied.com/design/en1998/non-structural-elements) was opened. Its input descriptions confirm the height datum and resonance sensitivity. Its overview contains a section-reference inconsistency, so it is not used as the governing formula source.
- The supplied Prota short URL could not be opened. Its [public French version](https://protasoftware.com/fr/support/manuels-techniques/forces-sismiques-sur-les-elements-non-structuraux/) and equation image were opened. One image's example coefficient is inconsistent with direct substitution; no Prota numerical output is adopted as verification.

## Independent arithmetic check

With alpha = 0.20, S = 1.15, z/H = 12/15 and Ta/T1 = 0.05/0.5:

- Sa = 0.23 times (5.4/1.81 minus 0.5) = **0.5711878453038674**.
- Wa = 2.7 times 1.25 times 0.60 = **2.025 kN**. The brief's 2.03 kN is rounded.
- Fa = Sa times 2.025 times 1.0 divided by 2.0 = **0.5783276933701658 kN**. Intermediate values are never rounded.
- For h = 3,000 mm the right-hand-side limits are **15.0, 22.5 and 30.0 mm**. With dr = 15 mm and nu = 0.5, the demand is **7.5 mm**. The corresponding unreduced dr limits are 30, 45 and 60 mm. These are different quantities.
- No force per bracket is returned until justified load shares are entered. Equal distribution is not assumed.
- Under the expressly declared centred sliding model, full reversing drift of plus/minus 15 mm with a 12 mm bolt requires a geometric slot length of **42 mm plus the total added installation allowance**. This does not check resistance, bearing, friction, washers, clearance, edge distances, travel stops or retained out-of-plane support.

## Verification status

Python tests cover the illustrated case, resonance, the lower bound, drift boundaries, required inputs, allocation equilibrium, reversible slot travel and invalid inputs. Fifteen exported Python cases matched the JavaScript implementation at a 0.1% numerical tolerance, with 47 numerical comparisons and exact comparison of labels, null values and Boolean results. This is implementation verification, not experimental validation.

## Required project replacements

Seismic hazard and National Annex, actual building and component periods, mass including all layers and fittings, component importance/category, supported-building design drift, justified bracket load distribution, slot kinematics and tolerances, connection resistance, manufacturer ETA anchorage information, eccentricity/torsion effects and existing-substrate assessment remain project-specific inputs or checks.
