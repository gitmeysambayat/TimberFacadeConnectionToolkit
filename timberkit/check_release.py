"""Replay calculation/build checks and report remaining review requirements.

This command does not publish and does not automate a browser. A DOM-stub
check is recorded separately from real-browser verification.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

from .joint_case import PREFIX

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.title = False
        self.main = False
        self.lang = None
        self.svg_without_name = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'html':
            self.lang = a.get('lang')
        if tag == 'title':
            self.title = True
        if tag == 'main':
            self.main = True
        if tag == 'svg' and not (a.get('aria-label') or a.get('aria-labelledby') or a.get('aria-hidden') == 'true'):
            self.svg_without_name += 1
        for k in ('href', 'src'):
            if k in a:
                self.links.append(a[k])


def static_checks():
    checked = []
    for name in ['index.html', PREFIX+'Portfolio.html', PREFIX+'TimberJointCase.html']:
        path = ROOT/name
        source = path.read_text(encoding='utf-8')
        page = Page()
        page.feed(source)
        duplicates = sorted({s for s in page.ids if page.ids.count(s) > 1})
        if duplicates:
            raise ValueError(name+': duplicate IDs '+str(duplicates))
        if page.lang != 'en-GB' or not page.title or not page.main:
            raise ValueError(name+': missing page language/title/main landmark')
        if page.svg_without_name:
            raise ValueError(name+': unnamed information graphic')
        if '\u2014' in source:
            raise ValueError(name+': em dash found')
        if re.search(r'__[A-Z][A-Z0-9_]*__', source):
            raise ValueError(name+': unresolved template token')
        for link in page.links:
            u = urlsplit(link)
            if u.scheme or u.netloc:
                continue
            if u.path:
                target = (path.parent/unquote(u.path)).resolve()
                if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
                    raise ValueError(name+': missing or out-of-repository dependency '+link)
            elif u.fragment and unquote(u.fragment) not in page.ids:
                raise ValueError(name+': missing fragment '+link)
        checked.append({'page': name, 'local_links': len(page.links), 'status': 'PASS'})
    for suffix in ['TimberJointCase.pdf', 'JointCaseInputs.json', 'JointCaseResults.json']:
        if not (ROOT/(PREFIX+suffix)).is_file():
            raise ValueError('Missing current artifact '+PREFIX+suffix)
    if not (ROOT/(PREFIX+'TimberJointCase.pdf')).read_bytes().startswith(b'%PDF-'):
        raise ValueError('Invalid PDF header')
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', default=shutil.which('node'), help='Node.js executable path')
    args = parser.parse_args()
    if not args.node:
        parser.error('Node.js was not found; pass --node PATH')
    env = dict(os.environ, TFK_OUTPUT_PREFIX=PREFIX)
    commands = []

    def run(label, argv, run_env=env):
        result = subprocess.run(argv, cwd=ROOT, env=run_env, capture_output=True, text=True, encoding='utf-8', errors='replace')
        entry = {'check': label, 'status': 'PASS' if result.returncode == 0 else 'FAIL', 'exit_code': result.returncode}
        if label == 'Python tests':
            found = re.search(r'(\d+) passed', result.stdout)
            entry['passed'] = int(found.group(1)) if found else None
        commands.append(entry)
        print(label+': '+entry['status'])
        if result.returncode:
            raise RuntimeError(label+' failed:\n'+result.stdout[-4000:]+result.stderr[-4000:])

    # A release record exists before the homepage dependency scan, even if a
    # later check fails. It is never represented as a completed browser review.
    record_path = ROOT/(PREFIX+'ReleaseVerification.json')
    record_path.write_text(json.dumps({'status': 'CHECKS_RUNNING', 'publication': 'NOT_PERFORMED'}, indent=2)+'\n', encoding='utf-8')
    try:
        run('Joint export from saved inputs', [sys.executable, '-m', 'timberkit.joint_case'])
        # The complete suite contains fixed v3 façade fixtures and v5 joint
        # fixtures. Let each family use its own default instead of pointing
        # the legacy tests at a non-existent v5 façade input file.
        test_env = dict(os.environ)
        test_env.pop('TFK_OUTPUT_PREFIX', None)
        run('Python tests', [sys.executable, '-m', 'pytest', '-q'], test_env)
        run('Joint calculation parity', [args.node, 'tests/joint_case_parity.mjs'])
        legacy_env = dict(os.environ, TFK_OUTPUT_PREFIX='20261018_v3_')
        run('Legacy calculation parity', [args.node, 'tests/parity.cjs'], legacy_env)
        run('Worked-case page build', [sys.executable, '-m', 'timberkit.build_joint_case'])
        run('Portfolio page build', [sys.executable, '-m', 'timberkit.build_home'])
        run('Page-wiring tests with DOM stub', [args.node, 'tests/joint_case_page.cjs'])
        pages = static_checks()
        joint = json.loads((ROOT/(PREFIX+'JointCaseParityResults.json')).read_text())
        legacy = json.loads((ROOT/'20261018_v3_ParityResults.json').read_text())
        wiring = json.loads((ROOT/(PREFIX+'JointCasePageChecks.json')).read_text())
        pdf_review = json.loads((ROOT/(PREFIX+'CasePDF_QA.json')).read_text())
        case_record_path = ROOT/(PREFIX+'JointCaseVerification.json')
        case_record = json.loads(case_record_path.read_text())
        case_record.update({
            'status': 'LOCAL_CHECKS_PASSED_BROWSER_REVIEW_REQUIRED',
            'python_tests': next(c for c in commands if c['check'] == 'Python tests'),
            'new_case_parity': joint,
            'page_wiring': wiring,
            'pdf_review': pdf_review,
            'static_pages': pages,
            'publication': 'NOT_PERFORMED',
        })
        case_record_path.write_text(json.dumps(case_record, indent=2)+'\n', encoding='utf-8')
        result = {
            'revision': PREFIX.rstrip('_'),
            'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'status': 'LOCAL_CHECKS_PASSED_BROWSER_REVIEW_REQUIRED',
            'publication': 'NOT_PERFORMED',
            'commands': commands,
            'joint_calculation_parity': joint,
            'legacy_calculation_parity': legacy,
            'page_wiring': wiring,
            'pdf_review': pdf_review,
            'selected_colour_contrast': json.loads((ROOT/(PREFIX+'ContrastChecks.json')).read_text()),
            'static_pages': pages,
            'browser_review': {'status': 'NOT_COMPLETED', 'reason': 'Local file URL was rejected by browser security policy; no alternate browser route attempted', 'required': ['Desktop and narrow-screen visual review', 'Keyboard/focus operation', 'Representative interactions and invalid-input recovery', 'KaTeX rendering and browser console']},
            'interpretation': 'Numerical agreement, static checks and DOM-stub tests are distinct from physical validation and real-browser review.',
            'artifact_sha256': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['index.html', PREFIX+'TimberJointCase.html', PREFIX+'TimberJointCase.pdf', PREFIX+'JointCaseResults.json']},
        }
        record_path.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
        print(result['status'])
    except Exception as error:
        record_path.write_text(json.dumps({'status': 'FAIL', 'commands': commands, 'error': str(error), 'publication': 'NOT_PERFORMED'}, indent=2)+'\n', encoding='utf-8')
        raise


if __name__ == '__main__':
    main()
