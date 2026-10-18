"""Build the dated, offline worked-joint page from reproducible case results."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PREFIX = '20261018_v4_'


def build():
    from .joint_case import default_inputs, evaluate
    case = default_inputs()
    result = evaluate(case)
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
    target.write_text(page, encoding='utf-8')
    print(target.name)


if __name__ == '__main__':
    build()
