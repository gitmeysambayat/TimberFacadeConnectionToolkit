# Timber connection mechanics

A reproducible study of bolted timber connection mechanics, with a worked timber-to-timber joint and a separate façade component explorer. Inspect the load path, resistance modes, detailing, movement and the assumptions behind each calculation.

**Educational component calculations.** The code and documentation were developed with AI assistance. No physical testing, product qualification or complete connection/façade design approval is reported.

## Explore

| Resource | What it provides |
|---|---|
| [Portfolio homepage](index.html) | An overview of the two studies and their evidence |
| [Worked timber joint](20261018_v5_TimberJointCase.html) | Interactive reference case, component checks, movement and controlled comparisons |
| [Technical report](20261018_v5_TimberJointCase.pdf) | Joint definition, source-linked calculations, sensitivity and proposed laboratory work |
| [Façade component explorer](20261018_v3_Toolkit.html) | Original timber-to-steel fixing illustration, seismic demand, isolated-member fire section loss and conditional panel racking |
| [Current release checks](20261018_v5_ReleaseVerification.json) | Actual check results, counts and outstanding browser review |

The v5 work is a **local review build**. The [existing live site](https://gitmeysambayat.github.io/TimberFacadeConnectionToolkit/) and its v3 deployment record do not establish deployment of v5.

## The worked joint

One bolt transfers parallel-to-grain tension from a central C24 timber member to two identical outer members. Both shear planes act in parallel. The worked calculation retains all double-shear Johansen modes, selected combined/permanent-only action-duration checks, nominal net-section tension, loaded-end and edge distances, hole and washer geometry, and instantaneous/final slip under a stated linear creep model.

The case also defines a **proposed** nine-specimen screening programme. No specimen fabrication, experiment, cyclic calibration or assembly trial has been completed.

Two different diameter comparisons are retained deliberately. The exported engineering sensitivity record scales washer dimensions to maintain the selected washer geometry; the interactive fixed-detail comparison holds the baseline washers and end distances constant to expose incompatible detailing. Each comparison states its basis. Neither is an optimisation algorithm or an experimental dataset.

## Reproduce

Use Python 3.11 or later and Node.js. From this repository root:

```text
python -m venv .venv
```

Activate the environment for your shell, then install the pinned dependencies:

```text
python -m pip install -r requirements.txt
```

Rebuild and check the current joint study and homepage:

```text
python -m timberkit.joint_case
node tests/joint_case_parity.mjs
python -m timberkit.build_joint_case
python -m timberkit.build_home
python -m pytest -q
node tests/joint_case_page.cjs
python -m timberkit.check_release
```

The release checker also replays the legacy parity fixtures, checks local page dependencies and writes the dated verification record. It reports real-browser review as outstanding. A passing numerical or DOM-stub check does not establish browser rendering.

The current joint prefix is `20261018_v5_`. The exporter reads the matching saved input JSON when it exists, or uses canonical defaults if it is absent. To export a different allowed input case:

```text
python -m timberkit.joint_case --inputs path/to/inputs.json
```

The fixed worked report contains a specific reference geometry and method examples. Its builder rejects noncanonical reference inputs rather than combining a changed case with stale printed equations or dimensions. Use the interactive controls for supported parameter studies; a different published worked case requires a corresponding report/template revision. Exported input/result records are engineering data and do not execute code.

A different dated prefix can be selected with the `TFK_OUTPUT_PREFIX` environment variable. Setting the prefix does not duplicate source documents or PDF reports automatically. The original façade study retains its v3 inputs and fixtures. Its page builder writes the dated component-explorer page; `timberkit.build_home` owns `index.html`.

## Verification and interpretation

Current execution counts and results are in the [release record](20261018_v5_ReleaseVerification.json). The checks answer different questions:

- Direct source-equation and rounded-hand/published-example fixtures check selected arithmetic against independent references.
- Automated tests cover numerical behaviour, missing inputs, units, geometry boundaries and invalid data.
- Python/browser parity compares two implementations of the same selected formulae; it is not an independent scientific validation.
- DOM-stub checks exercise page wiring without a real browser. They do not establish layout, keyboard behaviour or KaTeX rendering.
- PDF visual review checks the delivered document. It does not validate the engineering model.

The retained data key `final_elastic_mm` denotes calculated final slip including the selected creep increment and excluding prescribed free play. Public labels use “calculated final slip” to avoid implying a fully elastic response.

Legacy identifiers such as `VERIFIED_FORMULA` and `PASS_IN_SCOPE` describe an implemented expression or bounded subcheck. They do not mean that a product, whole connection, current-code compliance or physical behaviour has been verified.

The original façade release separately records [20 rounded-hand/published-example comparisons](20261018_v3_Verification.csv) and [155 legacy parity vectors](20261018_v3_ParityResults.json). These are not additional physical tests and should not be combined with the joint-case counts without identifying their scope.

## Engineering scope

The method uses explicitly cited first-generation EN 1995/EN 1998 provisions and reference material tables, including the identified amendments and EN 338:2016 C24 properties. It does not implement the second-generation 2025 Eurocode 5 provisions or establish a project's applicable National Annex choices.

The worked joint does **not** establish brittle timber splitting/shear-out/block failure, bolt steel or washer bearing resistance, installation quality, durability, fatigue, repeated assembly, connection fire performance or a complete façade load path. The façade tools retain their separate applicability and missing-input gates. Isolated-member section loss is not an assembly fire rating, and geometric material-volume comparisons are not a life-cycle assessment.

Read the case report and the original [connection source record](20261018_v3_ConnectionSources.md), [seismic source notes](20261018_v3_SeismicSourceNotes.md) and [material/fire/racking register](20261018_v3_MaterialsFireRackingSources.json) for exact clauses, source URLs and limits.

## Repository guide

- `timberkit/`: calculation modules, data exporter, builders and release checker.
- `web/`: page templates, browser calculations and retained mathematical-typography assets.
- `tests/`: independent reference, boundary, parity and page-wiring checks.
- `20261018_v5_*`: current worked-joint inputs, results, report and local release evidence.
- `20261018_v3_*` and `20261018_v4_*`: preserved earlier artifacts; follow the current links above for the review build.
- `index.html`: portfolio landing page for static hosting.

## Provenance and rights

Source PDFs are linked rather than redistributed. Retain the underlying engineering source citation and exact repository revision when reusing a calculation. The report distinguishes prescribed inputs, calculated results and proposed experimental work.

KaTeX 0.19.0 supplies mathematical typography under its [retained MIT licence](web/20261018_v1_KaTeX_LICENSE.txt). That notice is embedded in standalone pages containing KaTeX. No project-wide redistribution licence has been assigned; the KaTeX licence applies to that dependency.
