# Timber façade connection toolkit

A browser calculator and reproducible Python study of connection mechanics for an illustrative timber-frame façade renovation element. Explore local fastener resistance, non-structural seismic demand, isolated-member section loss in fire and a conditional panel-racking subcheck.

**Educational component calculations, not for design, approval or certification.** The calculator reports required inputs and component limitations, without an overall façade design pass. The code and documentation were developed with AI assistance.

## Explore the study

- [Live browser tool](https://gitmeysambayat.github.io/TimberFacadeConnectionToolkit/).
- [Source repository](https://github.com/gitmeysambayat/TimberFacadeConnectionToolkit).
- [Technical note and calculation verification](20261018_v3_TechnicalNote.html).
- [Worked learning guide](20261018_v3_LearningGuide.md).
- [Proposed test and assembly plan](20261018_v3_TestAndAssemblyPlan.html).

## Worked timber joint, version 4

The [complete worked component study](20261018_v4_TimberJointCase.html) defines one symmetric, single-bolt double-shear timber lap joint. It adds a traceable load path, all Johansen modes, nominal net-section tension, explicit end/edge and hole/washer geometry, instantaneous and selected final slip with connection creep, and controlled parameter comparisons. The page includes a proposed nine-specimen screening programme and manufacturing/disassembly evidence plan. It is self-contained and works offline.

These are calculated component results and proposed work. No physical timber experiment, prototype, calibrated FE model, connection fire qualification or life-cycle assessment has been completed. Read the unresolved checks beside the results. The original v3 deployment record does not establish deployment of this new case.

Reproduce the new case from this checkout with:

```text
python -m timberkit.joint_case
python -m pytest -q
node tests/joint_case_parity.mjs
python -m timberkit.build_joint_case
```

The new dated files use `20261018_v4_`; the original façade study retains its v3 prefix. See the [case verification record](20261018_v4_JointCaseVerification.json) for the checks actually performed.

Open `index.html` locally for the same self-contained calculator. Calculations, plots and mathematical typography run in the browser without a server, external computation or telemetry. Source links require an internet connection when selected. Browser input changes remain in memory until downloaded as JSON.

The [live deployment check](20261018_v3_Deployment.json) records the 18 October 2026 HTTP, content-identity and selected browser checks, including input changes, invalid-input handling, reset, JSON download and the six-page technical note.

## Engineering scope

| Component | Implemented study | Principal boundary |
|---|---|---|
| Timber connections | Embedment, fastener yield, implemented Johansen configurations, bounded rope effects, effective fastener count, spacing and slip modulus | Component expressions do not establish bracket, timber brittle-failure, steel or concrete-anchor resistance |
| Seismic demand | Non-structural element force, damage-limitation drift inequality and a separate sliding-slot geometry illustration | Actual classification, periods, bracket load shares and load paths are required |
| Fire | Reduced cross-section of an isolated unprotected rectangular timber member, with explicit exposed faces | Protected/insulated assemblies, member stability, connections and fire classification remain outside scope |
| Racking | Simplified Method A sheathed-panel expression, gated by explicit applicability inputs | Complete wall, hold-down, stud, sheathing and out-of-plane assessment is separate |
| Reference materials | Source-labelled C24 and GL24h properties, modification/deformation factors and recommended partial factors | Reference tables do not replace product declarations or applicable National Annex choices |

The illustrative panel is 2,700 × 1,250 mm. Its two-bolt subcase uses M12 bolts, a 6 mm steel plate and 45 mm assumed timber penetration. These are study inputs, not a fabrication drawing, measurements or verified site data. Gravity, in-plane and out-of-plane force transfer need a justified three-dimensional load path. Missing end/edge geometry, factored actions, load distribution, anchor ETA information, fire actions and racking prerequisites remain required.

The method follows explicitly cited first-generation EN 1995/EN 1998 provisions, including identified amendments where used. It does not implement the 2025 Eurocode 5 editions or assert current UK National Annex compliance. Confirm the standards framework for the actual project. Source scope, exact clauses and observed limitations are recorded in the [connection sources](20261018_v3_ConnectionSources.md), [seismic notes](20261018_v3_SeismicSourceNotes.md) and [materials/fire/racking source register](20261018_v3_MaterialsFireRackingSources.json).

## Reproduce the calculations

Use Python 3.11 or later with the pinned dependencies in `requirements.txt`. Node.js is required only for the browser-module parity comparison.

```text
python -m venv .venv
```

Activate the environment using the appropriate command for your shell, then run:

```text
python -m pip install -r requirements.txt
python -m pytest -q
python -m timberkit.study
node tests/parity.cjs
python -m timberkit.build_web
python -m timberkit.build_note
```

Run commands from the repository root. The study exports full-precision results, parameter sweeps, plots, benchmark comparisons and Python fixtures. The parity command compares those fixtures with the actual browser calculation modules before both page builders embed the current results.

The current prefix is `20261018_v3_`. For a new dated revision, set `TFK_OUTPUT_PREFIX` to a value such as `YYYYMMDD_vN_` and copy the reviewed case inputs to the matching prefix before regenerating. Reusing a prefix regenerates that revision; it does not create a new version automatically. Static page builders preserve the stated equations and scope text, so review that text when changing a study beyond its documented illustrative case.

The editable source case is [20261018_v3_CaseStudyInputs.json](20261018_v3_CaseStudyInputs.json). The browser embeds its release snapshot. Metadata schema version 2 uses `learner_verification_records` for optional independent learning records. That array does not change any engineering calculation.

## Verification and interpretation

This release passed **117 Python tests, 20 rounded-hand/published-example comparisons and 155 Python/browser parity vectors**. The [verification summary](20261018_v3_VerificationSummary.json) distinguishes these checks; the [benchmark CSV](20261018_v3_Verification.csv) records reference values, differences, tolerances and source clauses.

The parity run compared 973 numeric quantities, 33 Boolean values and 231 classification strings. Its relative tolerance is 0.1 per cent, with a 10⁻⁹ absolute tolerance for numerical zero. The largest observed relative difference was approximately 3.56 × 10⁻¹⁶. Parity establishes agreement between the implementations for those fixtures. Hand arithmetic and published examples provide separate reference comparisons.

No physical testing, experimental validation, calibrated cyclic model, prototype assembly or product approval is reported. The [test and assembly plan](20261018_v3_TestAndAssemblyPlan.html) describes proposed work only. Reference calculations and automated tests do not qualify the illustrative detail for construction.

## Repository contents

- `timberkit/`: Python component calculations, study exporter and static page builders.
- `web/`: browser calculation modules, interface code and retained KaTeX distribution records.
- `tests/`: numerical, boundary and missing-input tests, plus cross-language parity runner.
- `20261018_v3_*`: current inputs, calculated results, figures, source records, guides and standalone HTML.
- `index.html`: the same calculator as the dated toolkit page, suitable for static hosting.

## Provenance and rights

Sources are cited by title, edition, clause or table and URL. The material/fire/racking register also retains inspected-source SHA-256 fingerprints. Public source PDFs are linked, rather than redistributed as repository assets. Published-example reproductions retain the original geometry, property and rounding assumptions; they are separate from the illustrative façade subcase.

KaTeX 0.19.0 supplies browser-only mathematical typography under its [retained MIT licence](web/20261018_v1_KaTeX_LICENSE.txt). Its [distribution manifest](web/20261018_v1_KaTeXManifest.json) records source URLs and integrity checks. The notice is also embedded in each standalone HTML file that includes KaTeX. KaTeX asset filenames retain the original acquisition version for traceability.

No project-wide redistribution licence has been assigned. The third-party KaTeX licence applies to that dependency. Cite the repository and exact release/commit when referring to this educational study, and cite the underlying engineering sources for the provisions used.
