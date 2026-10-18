"""Build the research landing page from the current dated case snapshot."""
from pathlib import Path
import json
import re
from html import escape
from .joint_case import PREFIX

ROOT = Path(__file__).resolve().parents[1]


def build():
    result = json.loads((ROOT/(PREFIX+'JointCaseResults.json')).read_text(encoding='utf-8'))
    gc = result['load_duration_checks'][result['load_duration_checks']['governing_case']]
    template = (ROOT/'web/home_page.html').read_text(encoding='utf-8')
    replacements = {
        '__PREFIX__': PREFIX,
        '__DIAMETER__': f"{result['inputs']['diameter_mm']:g}",
        '__DEMAND__': f"{gc['NEd_N']/1000:.2f}",
        '__RESISTANCE__': f"{gc['Rd_N']/1000:.2f}",
        '__SLIP_INSTANT__': f"{result['slip']['postseating_elastic_mm']:.3f}",
        '__SLIP_FINAL__': f"{result['slip']['final_elastic_mm']:.3f}",
        '__UTILISATION__': f"{gc['utilisation']:.3f}",
    }
    for token, value in replacements.items():
        template = template.replace(token, escape(value))
    if re.search(r'__[A-Z][A-Z0-9_]*__', template):
        raise ValueError('Unreplaced landing-page template token')
    for target in [ROOT/'index.html', ROOT/(PREFIX+'Portfolio.html')]:
        target.write_text(template, encoding='utf-8', newline='\n')
    print(PREFIX+'Portfolio.html and index.html')


if __name__ == '__main__':
    build()
