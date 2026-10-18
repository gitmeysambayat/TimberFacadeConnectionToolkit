"""Build the dated, offline worked-joint page from reproducible case results."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def build():
    from .joint_case import PREFIX, default_inputs, evaluate
    # The prose and diagram describe a fixed M12 reference. A custom exported
    # calculation must never silently acquire those canonical labels.
    input_path = ROOT / (PREFIX + 'JointCaseInputs.json')
    result_path = ROOT / (PREFIX + 'JointCaseResults.json')
    case = json.loads(input_path.read_text(encoding='utf-8'))
    if case != default_inputs():
        raise ValueError('Worked-case page requires the canonical M12 reference inputs; custom cases must use the scenario explorer or calculation JSON.')
    result = evaluate(case)
    exported = json.loads(result_path.read_text(encoding='utf-8'))
    if exported != result:
        raise ValueError('Saved worked-case results do not match the reference inputs. Re-run python -m timberkit.joint_case before building the page.')
    template = (ROOT/'web/joint_case_page.html').read_text(encoding='utf-8')
    assets = '\n'.join((ROOT/'web'/n).read_text(encoding='utf-8') for n in
                       ['connections.js', 'materials_fire_racking.js', 'joint_case.mjs'])
    katex = (ROOT/'web/20261018_v1_KaTeX.min.js').read_text(encoding='utf-8')
    css = (ROOT/'web/20261018_v1_KaTeXInline.css').read_text(encoding='utf-8')
    licence = (ROOT/'web/20261018_v1_KaTeX_LICENSE.txt').read_text(encoding='utf-8')
    page = template.replace('__KATEX_CSS__', css).replace('__KATEX_JS__', katex)
    page = page.replace('__CALC_JS__', assets).replace('__BASE_INPUTS__', json.dumps(case))
    page = page.replace('__BASE_RESULTS__', json.dumps(result)).replace('__KATEX_LICENCE__', licence)
    target = ROOT/(PREFIX+'TimberJointCase.html')
    target.write_text(page, encoding='utf-8', newline='\r\n')
    print(target.name)


if __name__ == '__main__':
    build()
