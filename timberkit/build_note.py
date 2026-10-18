"""Build the dated, self-contained six-page educational technical note.

Only writes the HTML note. KaTeX renders the embedded TeX in the browser.
Run from the project root: python -m timberkit.build_note
"""

from pathlib import Path
from html import escape
import base64
import json
from .release import PREFIX


ROOT = Path(__file__).resolve().parents[1]


def read_json(name):
    return json.loads((ROOT / (PREFIX + name + ".json")).read_text(encoding="utf-8"))


def number(value, places=3):
    return f"{value:,.{places}f}".rstrip("0").rstrip(".") if places else f"{value:,.0f}"


def math(tex, source="", inline=False):
    tag = "span" if inline else "div"
    cls = "math inline" if inline else "math"
    output = f'<{tag} class="{cls}" data-tex="{escape(tex, quote=True)}"></{tag}>'
    return output + (f'<div class="cite">{source}</div>' if source else "")


def image_data(name):
    return "data:image/png;base64," + base64.b64encode((ROOT / (PREFIX + name + ".png")).read_bytes()).decode("ascii")


def table(headers, rows, cls=""):
    return '<table class="' + cls + '"><thead><tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>' for row in rows) + '</tbody></table>'


def page(index, kicker, title, body):
    return f'''<section class="page" id="page-{index}"><header><div class="kicker">{kicker}</div><h1>{title}</h1></header><div class="page-content">{body}</div><footer><span>Timber façade connection toolkit | Independent educational study | 18 October 2026</span><span>{index} / 6</span></footer></section>'''


def build():
    inputs = read_json("CaseStudyInputs")
    results = read_json("CaseStudyResults")
    verification = read_json("Verification")
    parity = read_json("ParityResults")
    p, c, s, f = (inputs[x] for x in ("panel", "connection", "seismic", "fire"))
    cr, sr, rr = (results[x] for x in ("connection", "seismic", "racking"))
    mode_rows = [[k, number(v["johansen_N"] / 1000), "0 (neglected)", number(v["Fv_Rk_N"] / 1000)] for k, v in cr["modes"]["modes"].items()]
    fire_rows = []
    for item in results["fire"]:
        q = item["section"]
        fire_rows.append([number(q["time_min"]), number(q["dchar_n_mm"]), number(q["k0"]), number(q["effective_char_depth_mm"]), number(q["effective_depth_mm"]), number(q["W_y_mm3"], 1)])
    materials = results["materials"]
    material_rows = []
    for label, key, unit in [("Bending strength", "fm_k_MPa", "MPa"), ("Tension parallel", "ft_0_k_MPa", "MPa"), ("Compression parallel", "fc_0_k_MPa", "MPa"), ("Shear strength", "fv_k_MPa", "MPa"), ("Mean parallel modulus", "E_0_mean_MPa", "MPa"), ("Characteristic density", "rho_k_kg_m3", "kg/m³"), ("Mean density", "rho_mean_kg_m3", "kg/m³")]:
        material_rows.append([label, number(materials["C24"][key]), number(materials["GL24h"][key]), unit])

    schematic = '''<svg class="schematic" viewBox="0 0 680 285" role="img" aria-label="Generic timber panel load path and bracket schematic, not a fabrication drawing">
    <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#2260c9"/></marker></defs>
    <rect x="110" y="24" width="196" height="215" fill="#f1f6fd" stroke="#255eaa" stroke-width="2"/>
    <g fill="#d9e7f7" stroke="#255eaa" stroke-width="2"><rect x="113" y="27" width="12" height="209"/><rect x="202" y="27" width="12" height="209"/><rect x="291" y="27" width="12" height="209"/><rect x="113" y="27" width="190" height="12"/><rect x="113" y="224" width="190" height="12"/></g>
    <g fill="#fff" stroke="#255eaa"><circle cx="119" cy="69" r="2"/><circle cx="119" cy="112" r="2"/><circle cx="119" cy="155" r="2"/><circle cx="119" cy="198" r="2"/><circle cx="297" cy="69" r="2"/><circle cx="297" cy="112" r="2"/><circle cx="297" cy="155" r="2"/><circle cx="297" cy="198" r="2"/></g>
    <g stroke="#2260c9" stroke-width="2" marker-end="url(#arrow)"><path d="M45 85H100"/><path d="M45 131H100"/><path d="M45 177H100"/><path d="M248 96V160"/><path d="M309 223H390"/></g>
    <g font-family="Arial,sans-serif" font-size="12" fill="#111"><text x="15" y="59">Wind / inertia</text><text x="232" y="86">Gravity</text><text x="145" y="258">OSB/3 + timber frame</text><text x="128" y="277">Generic load path only</text></g>
    <rect x="399" y="177" width="103" height="20" fill="#d9e7f7" stroke="#255eaa"/><path d="M416 175V226H540" fill="none" stroke="#5d6675" stroke-width="7"/>
    <circle cx="447" cy="186" r="5" fill="white" stroke="#111"/><circle cx="482" cy="186" r="5" fill="white" stroke="#111"/><rect x="545" y="173" width="42" height="79" fill="#e5e7ea" stroke="#777"/>
    <path d="M520 226H569" stroke="#777" stroke-width="3" stroke-dasharray="4 3"/>
    <g font-family="Arial,sans-serif" font-size="12" fill="#111"><text x="408" y="145">Illustrative two-bolt rail subcase</text><text x="404" y="163">Steel bracket geometry unverified</text><text x="546" y="269">Existing support</text><text x="394" y="62">Panel → frame / sheathing → bracket</text><text x="394" y="83">→ anchors → existing structure</text><text x="394" y="110">Anchor specification and load shares</text><text x="394" y="127">are REQUIRED inputs.</text></g></svg>'''

    page1 = page(1, "01 | Problem, assumptions and load path", "Timber façade connection study", f'''
    <p class="lead">An independent calculation toolkit for learning how timber connection mechanics, non-structural seismic demand, section loss in fire and panel racking interact.</p>
    <div class="notice"><b>Educational component calculations. No overall design pass.</b> Prepared with AI assistance. Development checks assess the implementation of the stated equations; no physical validation, laboratory testing or product approval is represented.</div>
    <h2>Illustrative case</h2>
    <p>A {number(p['height_mm'])} × {number(p['width_mm'])} mm panel has {p['material']} {number(p['stud_width_mm'])} × {number(p['stud_depth_mm'])} mm studs and rails at {number(p['stud_centres_mm'])} mm centres, with {number(p['sheathing_thickness_mm'])} mm {p['sheathing']} on one face. Illustrative smooth round {number(p['nail_diameter_mm'])} mm nails are spaced at {number(p['nail_edge_spacing_mm'])} mm at sheet edges. Insulation contributes no structural resistance.</p>
    {table(['Assumed characteristic input', 'Whole-panel result'], [[f'Self-weight {number(p["self_weight_kN_m2"])} kN/m²', f'{number(sr["weight_kN"])} kN over {number(results["panel_area_m2"])} m²'], [f'Wind pressure {number(p["characteristic_wind_kN_m2"])} kN/m²', f'{number(results["characteristic_wind_resultant_kN"])} kN resultant']])}
    <p class="small">These assumed actions are not a factored design combination. Panel-to-bracket load distribution, gravity bearing, out-of-plane behaviour and anchor design have not been established.</p>
    {schematic}
    <div class="two-col"><div><h2>What is calculated</h2><p>Source-linked fastener formulae, an explicitly simplified two-bolt subcase, elastic slip, EC8 component demand and drift, isolated-stud effective section loss, and a gated Method A racking subcheck.</p></div><div><h2>What remains required</h2><p>Product declarations; complete dimensions and bracket geometry; design actions and load shares; an applicable anchor ETA; fire actions and assembly behaviour; tie-down and sheet fixing details.</p></div></div>
    <p class="edition"><b>Standards scope.</b> Calculations follow the cited first-generation EN 1995/EN 1998 provisions. [S2] is EN 1995-1-1:2004+A1:2008 with its corrigendum; [S1] reproduces specified A2:2014 details, including dowel spacing. [S3] is EN 1995-1-2:2004 with the cited corrigenda; [S4] is EN 1998-1:2004. This is not a current UK National Annex compliance statement. Source legend and URLs are on page 6.</p>
    ''')

    page2 = page(2, "02 | A. Materials and B. Connection mechanics", "The thin-plate bolt subcase", f'''
    <p>M{number(c['diameter_mm'])} bolts, {number(c['steel_plate_thickness_mm'])} mm plate, {number(c['timber_thickness_mm'])} mm assumed timber penetration, {number(c['load_angle_deg'])}° to grain, {number(c['fu_MPa'])} MPa ultimate strength. The plate is thin at the boundary {math(r't_s=0.5d', inline=True)}. The product grade and actual load direction remain unverified.</p>
    <div class="two-col eq-columns"><div><h2>Embedment and fastener yield</h2>
    {math(r'f_{h,0,k}=0.082(1-0.01d)\rho_k', '[S1] p.44; [S2] 8.5.1.1, Eq. (8.32). d in mm; density in kg/m³; strength in MPa.')}
    {math(r'f_{h,\alpha,k}=\frac{f_{h,0,k}}{k_{90}\sin^2\alpha+\cos^2\alpha},\quad k_{90}=1.35+0.015d', '[S1] p.44; [S2] Eqs (8.31), (8.33), softwood coefficient.')}
    {math(r'M_{y,Rk}=0.3 f_{u,k}d^{2.6}', '[S1] p.44; [S2] Eq. (8.30), bolt yield moment in N mm.')}
    <p>Case: <b>{number(cr['embedment']['fh_k'])} MPa</b> embedment; <b>{number(cr['yield_moment']['My_Rk']/1000)} kN mm</b> yield moment.</p>
    <h2>Thin steel, single shear</h2>
    {math(r'F_{a,Rk}=0.4 f_{h,k}t_1d', '[S1] p.38; [S2] 8.2.3, Eq. (8.9), mode a.')}
    {math(r'F_{b,Rk}=1.15\sqrt{2M_{y,Rk}f_{h,k}d}+F_{\mathrm{rope}}', '[S1] p.38; [S2] Eq. (8.9), mode b. The permitted rope limit also applies.')}
    {table(['Mode', 'Johansen, kN', 'Rope, kN', 'Total, kN'], mode_rows, 'compact')}
    <p class="small"><b>Mode {cr['modes']['governing_mode']} governs.</b> Axial resistance is not established, so the case deliberately neglects rope effect. This does not establish zero product axial capacity.</p>
    </div><div><h2>Group effect and design resistance</h2>
    {math(r'n_{\mathrm{eff}}=\min\!\left[n,\ n^{0.9}\left(\frac{a_1}{13d}\right)^{0.25}\right]', '[S1] p.45; [S2] 8.5.1.1, Eq. (8.34), row parallel to grain.')}
    {math(r'F_{v,Rd}=\frac{k_{\mathrm{mod}}F_{v,Rk}}{\gamma_M},\quad F_{\mathrm{row},Rd}=n_{\mathrm{eff}}F_{v,Rd}', '[S1] pp.7-8, 36; [S2] 2.4.1 and 8.1. Assumed service class 2, short-term action: kmod=0.9; recommended connection γM=1.3.')}
    <p>Two bolts at {number(c['spacing_parallel_mm'])} mm (7d): effective number <b>{number(cr['effective_number']['n_eff'],4)}</b>; conditional row result <b>{number(cr['design']['group_design_capacity_N']/1000)} kN</b>. No design demand or utilisation is supplied.</p>
    <h2>Slip, per fastener and shear plane</h2>
    {math(r'K_{\mathrm{ser,base}}=\frac{\rho_m^{1.5}d}{23},\quad K_u=\frac{2}{3}K_{\mathrm{ser}}', '[S1] p.33; [S2] Table 7.1 and 2.2.2(2). Optional steel multiplier 2: 7.1(3).')}
    <p class="small">Base Kser = {number(cr['slip']['Kser_base_N_per_mm']/1000)} kN/mm. Selected optional steel factor 2 gives Kser = {number(cr['slip']['Kser_N_per_mm']/1000)} and Ku = {number(cr['slip']['Ku_N_per_mm']/1000)} kN/mm. Add bolt-hole clearance slip separately.</p>
    <h2>Detailing controls the interpretation</h2>
    <p class="small">At 0°: a₁ ≥ 60, a₂ ≥ 48, loaded/unloaded end ≥ 84/48, loaded/unloaded edge ≥ 36/36 mm. Only a₁ = 84 mm is supplied; every other dimension is <b>UNVERIFIED</b>. [S1] p.45 Table 10.4 / [S2] Table 8.4.</p>
    </div></div>
    <div class="notice small"><b>No bracket capacity claim.</b> Steel resistance, splitting, block/plug shear, net section, combined axial/lateral loading, eccentricity, bracket bending/prying and concrete anchors remain unchecked. The toolkit implements other Johansen families and rope caps, but this note illustrates only the specified thin-plate case. Full formula/source records accompany the code.</div>
    ''')

    page3 = page(3, "03 | Non-structural seismic demand and movement", "Demand is a load-path question", f'''
    <p>Illustrative inputs: α = {number(s['alpha'])}, S = {number(s['soil_factor'])}, H = {number(s['building_height_m'])} m, z = {number(s['element_height_m'])} m, T₁ = {number(s['fundamental_period_s'])} s, Tₐ = {number(s['element_period_s'])} s, γₐ = {number(s['gamma_a'])}, qₐ = {number(s['q_a'])}. Here α is design ground acceleration divided by gravity; γₐ and qₐ require the applicable element category and detail justification.</p>
    {math(r'S_a=\max\!\left\{\alpha S,\ \alpha S\left[\frac{3\left(1+\frac{z}{H}\right)}{1+\left(1-\frac{T_a}{T_1}\right)^2}-0.5\right]\right\}', '[S4] 4.3.5.2(3), Eq. (4.25), including the lower bound αS.')}
    {math(r'F_a=\frac{S_a W_a\gamma_a}{q_a}', '[S4] 4.3.5.2(2), Eq. (4.24). γa: 4.3.5.3; qa upper values: 4.3.5.4, Table 4.4. Fa acts at the element centre of mass.')}
    <div class="result-strip"><span>Sa <b>{number(sr['Sa'],6)}</b></span><span>Wa <b>{number(sr['weight_kN'])} kN</b></span><span>Whole-panel Fa <b>{number(sr['Fa_kN'],6)} kN</b></span></div>
    <img class="plot" src="{image_data('SeismicHeight')}" alt="Calculated whole-panel seismic force against normalised installation height for the stated illustrative inputs"/>
    <p class="caption">Height study with all other case inputs fixed. These are whole-panel forces. Per-bracket forces and anchor utilisation remain <b>REQUIRED</b> until justified load shares and an applicable anchor ETA are supplied.</p>
    <h2>Damage-limitation drift and a separate slot illustration</h2>
    {math(r'd_r\nu\leq\left\{\begin{array}{ll}0.005h&\text{brittle attached elements}\\0.0075h&\text{ductile elements}\\0.010h&\text{non-interfering elements}\end{array}\right.', '[S4] 4.4.3.2, Eqs (4.31)-(4.33). Recommended NDP ν=0.5 for importance I/II; 0.4 for III/IV, subject to the applicable National Annex.')}
    <p>For the assumed brittle attached category, h = {number(s['storey_height_mm'])} mm and dr = {number(s['design_interstorey_drift_mm'])} mm: drν = <b>{number(sr['drift']['demand_mm'])} mm</b> ≤ {number(sr['drift']['limit_mm'])} mm, ratio {number(sr['drift']['ratio'])}. This verifies this inequality only.</p>
    {math(r'\ell_{\mathrm{slot}}=d_{\mathrm{bolt}}+2\Delta+\delta_{\mathrm{installation}}=12+2(15)+0=42\ \mathrm{mm}', 'Declared geometric illustration, not a Eurocode slot-design rule. Δ uses the full assumed design drift, not the reduced damage-limitation quantity drν.')}
    <p class="small">The {number(sr['slot']['slot_length_mm'])} mm centred, friction-free slot allows ±{number(sr['slot']['travel_each_direction_mm'])} mm shank-centre travel under the stated idealisation. Actual clearance, end/edge distances, bearing, friction, fatigue, gravity support, fire detailing and multi-axis movement remain unverified.</p>
    ''')

    page4 = page(4, "04 | Fire: isolated unprotected member only", "Keep the exposed axis explicit", f'''
    <p>The section is <b>{number(f['width_mm'])} mm wide × {number(f['depth_mm'])} mm deep</b>. One exposed <b>depth-front</b> face reduces the 145 mm depth. This is an isolated unprotected solid-softwood stud under a standard-fire idealisation. It is not the insulated façade assembly.</p>
    <div class="two-col"><div>
    {math(r'd_{\mathrm{char},0}=\beta_0t,\quad d_{\mathrm{char},n}=\beta_nt', '[S3] 3.4.2, Eqs (3.1)-(3.2), Table 3.1: β0=0.65 and βn=0.8 mm/min for qualifying solid softwood (ρk ≥ 290 kg/m³).')}
    {math(r'd_{\mathrm{ef}}=d_{\mathrm{char},n}+k_0d_0,\quad k_0=\min\!\left(\frac{t}{20},1\right)', '[S3] 4.2.2, Eq. (4.1), Table 4.1: d0=7 mm; t in minutes. Unprotected surfaces only.')}
    </div><div>
    {math(r'h_{\mathrm{ef}}=h-d_{\mathrm{ef}},\quad W_{y,\mathrm{ef}}=\frac{b h_{\mathrm{ef}}^2}{6}', 'Rectangular-section geometry. The notional βn reduction, not β0, is used for the case section.')}
    {math(r'f_{d,\mathrm{fi}}=\frac{k_{\mathrm{mod,fi}}k_{\mathrm{fi}}f_k}{\gamma_{M,\mathrm{fi}}}', '[S3] 2.3, Eqs (2.1), (2.4), Table 2.1: kfi=1.25 solid timber (1.15 glulam); 4.2.2(5): kmod,fi=1. Recommended γM,fi=1, subject to National Annex.')}
    </div></div>
    {table(['t, min', 'dchar,n, mm', 'k₀', 'def, mm', 'hef, mm', 'Wy,ef, mm³'], fire_rows, 'compact fire-table')}
    <img class="plot" src="{image_data('FireDepth')}" alt="Effective and notional char-only residual section depths for the isolated stud with one depth face exposed"/>
    <p class="caption">The solid curve includes the zero-strength layer. The dashed curve is the notional char-only residual depth, before that layer. β0 is reported as a reference rate, but its one-dimensional/corner conditions are not automatically satisfied by a 45 mm narrow member.</p>
    <div class="notice"><b>Section loss only.</b> With supplied strength factors, the reference fire bending strength is {math(r'\frac{1\times1.25\times24}{1}=30\ \mathrm{MPa}', inline=True)}. Applied fire moment and axial compression are missing. The toolkit returns <b>REQUIRED INPUT</b>, without capacity approval or a fire-resistance time rating.</div>
    <p class="small">One-sided loss shifts the centroid by 5.75, 15.5 and 27.5 mm at 10, 30 and 60 min. Eccentric compression, instability, connections, protection fall-off, insulation, cavities and the separating function are outside this subcheck. Exposing a face that reduces the 45 mm width is a different case and can exhaust that dimension; it must not be interchanged with this illustration.</p>
    ''')

    page5 = page(5, "05 | Panel racking and reference material properties", "Applicability comes before capacity", f'''
    <h2>Method A: one sheathed panel, conditional subcheck</h2>
    {math(r'F_{i,v,Rd}=\frac{F_{\mathrm{edge},Rd}b_i c_i}{s},\quad c_i=\min\!\left(1,\frac{b_i}{b_0}\right),\quad b_0=\frac{h}{2}', '[S2] 9.2.4.2, Eqs (9.21)-(9.22); [S1] pp.49-50. Here Fedge,Rd is a sheet-edge fastener design resistance.')}
    {math(r'F_{\mathrm{edge},Rd}=1.2F_{f,Rd}\quad\text{only when the input is not already enhanced}', '[S2] 9.2.4.2(5): sheet-edge enhancement relative to Section 8. Apply the factor once, not twice.')}
    <p>For bi = 1250 mm, h = 2700 mm, s = 150 mm: b₀ = <b>{number(rr['b0_mm'])} mm</b>, cᵢ = <b>{number(rr['width_factor_ci'],6)}</b>. The sheet width exceeds h/4 = {number(rr['minimum_sheet_width_mm'])} mm. This verifies geometry only.</p>
    <div class="two-col"><div><h2>Required method conditions</h2><ul><li>End directly tied to the construction below.</li><li>No openings and constant perimeter fixing spacing.</li><li>Sufficient sheet-edge distances and verified fixings.</li><li>Applicable design nail resistance and nationally permitted method.</li></ul></div><div><h2>Current result: REQUIRED INPUT</h2><p>Tie-down, openings, sheet-edge and fixing verification, and nail design resistance are missing. No racking resistance is reported. The assumed 2.8 mm nails do not establish their capacity in this OSB/3 product.</p></div></div>
    <p class="small">Stud buckling/bearing, sheet shear buckling, central fixings, inter-element force transfer, anchorage and serviceability remain to be checked. The expression does not assess out-of-plane wind resistance or the complete façade. [S2] 9.2.4.2; [S1] pp.49-50.</p>
    <h2>Reference properties, not product verification</h2>
    {table(['Property', 'C24', 'GL24h', 'Unit'], material_rows, 'compact material-table')}
    <p class="cite">[S1] Table 3.3 p.10 (C24, citing EN 338:2016), Table 3.4 p.12 (GL24h, citing EN 14080:2013). Product declarations and grading remain required. Sheathing and fastener resistance are not inferred from these timber tables.</p>
    {math(r'f_d=\frac{k_{\mathrm{mod}}f_k}{\gamma_M}', '[S2] 2.4.1, Eq. (2.14). [S1] Tables 3.1-3.2 pp.7-8: recommended γM=1.3 solid timber/connections, 1.25 glulam, 1.2 OSB; select applicable National Annex.')}
    <p class="small"><b>Moisture and duration matter.</b> For solid timber/glulam, short-term kmod is 0.9 in service classes 1/2 and 0.7 in class 3. Base kdef is 0.6/0.8/2.0 in classes 1/2/3. For OSB/3, short-term kmod is 0.9/0.7 and kdef is 1.5/2.25 in classes 1/2; no class-3 table value is supplied. [S1] Tables 3.2 and 9.1; [S2] Tables 3.1-3.2. Wet-installation provisions are not automatically added.</p>
    ''')

    short_names = ["Bolt embedment, MPa", "M12 yield moment, kN mm", "Base Kser, kN/mm", "Base Ku, kN/mm", "5 bolts at 7d: effective count", "10 min effective loss, mm", "30 min effective loss, mm", "60 min effective loss, mm", "Seismic Sa, dimensionless", "Whole-panel weight, kN", "Whole-panel Fa, kN", "Brittle drift RHS, mm", "Ductile drift RHS, mm", "Non-interfering drift RHS, mm", "Sheet factor ci, dimensionless", "Vol.3 Ex.4.1 characteristic, N", "Vol.3 Ex.4.1 group design, N", "Vol.3 Ex.4.2 no rope, N", "Vol.3 Ex.4.2 with rope, N", "Vol.3 Ex.4.2 design, N"]
    check_rows = []
    for i, q in enumerate(verification["checks"]):
        kind = "P" if q["source"].startswith("Published") else "H"
        check_rows.append([f'{i+1}. {short_names[i]}', f'{kind}: {number(q["reference_value"],6)}', number(q["toolkit_value"],6), f'{q["difference"]:+.6g}', 'PASS' if q['passed'] else 'FAIL'])
    source_rows = [
        ("S1", "Swedish Wood / TDUK, Design of timber structures, UK Vol.2, edition 1:2022. Tables and clauses stated on pages 2-5.", "https://www.universityofgalway.ie/media/timberengineeringresearchgroup/Design-of-timber-structures_Volume2_Rules-and-formulas-according-to-Eurocode-5.pdf"),
        ("S2", "EN 1995-1-1:2004+A1:2008, public consolidated text with 2006 corrigendum. A2-specific handbook tables are identified separately.", "https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.1.2004.pdf"),
        ("S3", "EN 1995-1-2:2004 with 2006/2009 corrigenda. Fire clauses 2.3, 3.4.2 and 4.2.2.", "https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.2.2004.pdf"),
        ("S4", "EN 1998-1:2004, clauses 4.3.5.2-4.3.5.4 and 4.4.3.2.", "https://www.phd.eng.br/wp-content/uploads/2015/02/en.1998.1.2004.pdf"),
        ("S5", "Swedish Wood, Design of timber structures, Vol.3, edition 3:2022. Examples 4.1-4.2, pp.20-24.", "https://www.svenskttra.se/siteassets/5-publikationer/pdfer/sw-design-of-timber-structures-vol3-2022.pdf"),
    ]
    source_html = ''.join(f'<div class="source"><b>[{sid}]</b> {escape(label)} <a href="{url}">{url}</a></div>' for sid, label, url in source_rows)
    page6 = page(6, "06 | Verification, sources and boundaries", "Reproducible checks, limited claims", f'''
    <p class="small">All 20 stored comparisons pass their stated tolerances. H = rounded hand reference; P = published example [S5]. Δ = toolkit minus reference, in the quantity's stated unit. Agreement with rounded examples verifies implementation, not an actual connection or physical performance.</p>
    {table(['Quantity and unit', 'Hand / published', 'Toolkit', 'Δ', 'Check'], check_rows, 'verification')}
    <p class="tiny">The full <a href="20261018_v1_Verification.csv">verification CSV</a> and JSON record tolerances and clause mappings. Published Example 4.1 assumes 12 screws with 8 mm effective diameter, thick steel and no rope; Example 4.2 uses annular nails with supplied rounded axial resistance 383 N. Their respective kmod = 0.65 and 0.8 follow their own conditions, not the illustrative bolt case. Python/browser parity: <b>{parity.get('vectors', parity.get('vector_count', 136))} vectors PASS</b>; this is a cross-language consistency check, not independent physical validation.</p>
    <h2>Opened source register</h2><div class="sources">{source_html}</div>
    <p class="tiny"><b>Application scope:</b> confirm the standard edition, National Annex, products, complete geometry, actions, anchor ETA and load shares before project-specific assessment. Cyclic behaviour, complete racking and fire-assembly performance remain outside this study. No physical validation, calibrated finite-element model or current UK compliance is claimed. AI-assisted development. Typography: <a href="web/20261018_v1_KaTeX_LICENSE.txt">KaTeX, MIT licence</a>.</p>
    ''')

    css = '''
    :root{--blue:#225da9;--light:#eef4fc;--line:#c9d8ed;--muted:#344254}*{box-sizing:border-box}html,body{margin:0;padding:0}body{background:#e8edf4;color:#111;font-family:Arial,Helvetica,sans-serif;font-size:11pt;line-height:1.31}.page{width:210mm;height:297mm;padding:12mm 14mm 9mm;margin:5mm auto;background:#fff;display:flex;flex-direction:column;box-shadow:0 1mm 4mm #0002;break-after:page;page-break-after:always}.page:last-child{break-after:auto;page-break-after:auto}header{border-bottom:2.1mm solid var(--blue);padding-bottom:3mm;margin-bottom:3mm}h1{font-size:23pt;line-height:1.1;color:var(--blue);margin:1.5mm 0 0;font-weight:700;letter-spacing:-.3pt}.kicker{font-size:8.8pt;color:var(--blue);text-transform:uppercase;font-weight:700;letter-spacing:.6pt}.page-content{flex:1;min-height:0}h2{font-size:12pt;color:var(--blue);line-height:1.2;margin:3.1mm 0 1.6mm}p{margin:0 0 2.6mm}.lead{font-size:13pt;line-height:1.32}.small{font-size:9.8pt;line-height:1.3}.tiny{font-size:8.1pt;line-height:1.23}.notice{background:var(--light);border-left:1.1mm solid var(--blue);padding:2.5mm 3mm;margin:2.5mm 0 3mm}.edition{font-size:9pt;line-height:1.3;border-top:.3mm solid var(--line);padding-top:2.5mm;margin-top:3mm}.two-col{display:grid;grid-template-columns:1fr 1fr;gap:5mm}.two-col>div{min-width:0}table{border-collapse:collapse;width:100%;font-size:10pt;line-height:1.25;margin:2mm 0 3mm}th{background:var(--blue);color:#fff;font-weight:700;text-align:left}td,th{padding:1.7mm 2mm;border-bottom:.25mm solid var(--line);vertical-align:top}tbody tr:nth-child(even){background:#f5f8fc}.compact{font-size:9.1pt}.compact td,.compact th{padding:1.25mm 1.5mm}.math{font-size:10.8pt;margin:1.8mm 0 .8mm;text-align:left}.math .katex-display{margin:.4em 0;text-align:left}.math .katex-display>.katex{text-align:left}.math.inline{font-size:1em;display:inline;margin:0}.cite{font-size:9.2pt;line-height:1.25;color:var(--muted);margin-bottom:2.1mm}.eq-columns .math{font-size:9.7pt}.eq-columns p{font-size:9.8pt}.schematic{display:block;width:100%;height:70mm;margin:1mm 0}.plot{display:block;width:100%;height:69mm;object-fit:contain;margin:1.7mm 0}.caption{font-size:8.8pt;line-height:1.26;color:var(--muted);margin:1mm 0 2mm}.result-strip{display:flex;justify-content:space-between;gap:3mm;background:var(--light);padding:2mm 3mm;margin:2mm 0;font-size:10.5pt}.result-strip b{color:var(--blue)}ul{margin:1mm 0 3mm;padding-left:4mm;font-size:10pt}li{margin:0 0 1.5mm}footer{display:flex;justify-content:space-between;gap:3mm;font-size:7.4pt;line-height:1.2;border-top:.3mm solid var(--line);padding-top:2mm;margin-top:2mm;flex-shrink:0;color:var(--muted)}a{color:var(--blue);text-decoration:underline}.verification{font-size:10pt;line-height:1.12;margin:1.5mm 0 2mm}.verification td,.verification th{padding:1mm 1.4mm}.verification td:nth-child(n+2){white-space:nowrap;text-align:right}.verification td:last-child{color:#1c633a;font-weight:bold}.verification th:nth-child(n+2){text-align:right}#page-6 h2{font-size:10.5pt;margin:2mm 0 1.2mm}.sources{font-size:9.2pt;line-height:1.18;margin-bottom:2mm}.source{margin-bottom:1.25mm}.source a{display:block;font-size:8.5pt;overflow-wrap:anywhere}.material-table{font-size:9.4pt}#page-4 .math{font-size:10.2pt}#page-4 .plot{height:65mm}#page-3 .plot{height:66mm}@page{size:A4;margin:0}@media print{html,body{background:#fff}body{-webkit-print-color-adjust:exact;print-color-adjust:exact}.page{margin:0;box-shadow:none}a{color:inherit}.page{break-inside:avoid}}'''
    katex_css = (ROOT / "web" / "20261018_v1_KaTeXInline.css").read_text(encoding="utf-8")
    katex_js = (ROOT / "web" / "20261018_v1_KaTeX.min.js").read_text(encoding="utf-8")
    content = f'''<!doctype html><html lang="en-GB"><head><link rel="icon" href="data:,"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="AI-assisted independent educational timber façade component study, without an overall design pass"><title>Timber façade connection toolkit | Technical note | 18 October 2026</title><style>{katex_css}</style><style>{css}</style></head><body>{page1}{page2}{page3}{page4}{page5}{page6}<script>{katex_js}</script><script>document.querySelectorAll('.math').forEach(function(el){{katex.render(el.dataset.tex,el,{{displayMode:!el.classList.contains('inline'),throwOnError:false,strict:'warn'}});}});document.fonts.ready.then(function(){{document.documentElement.dataset.mathReady='true';}});</script></body></html>'''
    content = content.replace('20261018_v1_Verification.csv', PREFIX+'Verification.csv')
    notice = (ROOT / 'web' / '20261018_v1_KaTeX_LICENSE.txt').read_text(encoding='utf-8')
    content = content.replace('</html>', '<!-- KaTeX third-party licence\n' + notice + '\n--></html>')
    if "\u2014" in content:
        raise ValueError("An em dash entered the note")
    output = ROOT / (PREFIX + "TechnicalNote.html")
    output.write_text(content, encoding="utf-8")
    print(json.dumps({"output": str(output), "pages": 6, "verification_rows": len(check_rows), "bytes": output.stat().st_size}))


if __name__ == "__main__":
    build()
