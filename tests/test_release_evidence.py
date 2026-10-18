"""Prevent stale or incomplete review records from becoming release claims."""
import hashlib
import json

import pytest

from timberkit.check_release import apply_browser_review, browser_evidence, deployment_evidence

PREFIX = '20261018_v5_'
PAGES = ['index.html', PREFIX+'TimberJointCase.html', '20261018_v3_Toolkit.html']


@pytest.fixture
def evidence(tmp_path):
    hashes = {}
    for page in PAGES:
        content = ('Review fixture '+page).encode()
        (tmp_path/page).write_bytes(content)
        hashes[page] = hashlib.sha256(content).hexdigest()
    return tmp_path, {
        'revision': PREFIX.rstrip('_'), 'status': 'PASS', 'page_sha256': hashes,
        'checks': [{'name': 'Observed interaction and layout', 'status': 'PASS'}],
        'build_commit': 'a'*40,
    }


def save(evidence, suffix):
    root, record = evidence
    path = root/(PREFIX+suffix)
    path.write_text(json.dumps(record), encoding='utf-8')
    return path


def test_missing_reviews_do_not_claim_completion(tmp_path):
    review = browser_evidence(tmp_path, PREFIX)
    assert review['status'] == 'PENDING'
    previous = {'browser_ui': 'PASS', 'browser_review': {'status': 'PASS'}}
    apply_browser_review(previous, review)
    assert previous['browser_ui'] == 'PENDING'
    assert previous['browser_review'] == review
    assert deployment_evidence(tmp_path, PREFIX)['status'] == 'NOT_PERFORMED'


@pytest.mark.parametrize('suffix,reader', [('BrowserQA.json', browser_evidence), ('Deployment.json', deployment_evidence)])
def test_matching_evidence_is_accepted_and_preserved(evidence, suffix, reader):
    path = save(evidence, suffix)
    original = path.read_bytes()
    review = reader(evidence[0], PREFIX)
    assert review['status'] == 'PASS'
    if reader is browser_evidence:
        previous = {'browser_ui': 'NOT_COMPLETED_LOCAL_FILE_PROTOCOL_BLOCKED_BY_BROWSER_SECURITY_POLICY'}
        apply_browser_review(previous, review)
        assert previous['browser_ui'] == 'PASS'
        assert previous['browser_review'] == review
    assert path.read_bytes() == original


@pytest.mark.parametrize('page', PAGES)
@pytest.mark.parametrize('suffix,reader', [('BrowserQA.json', browser_evidence), ('Deployment.json', deployment_evidence)])
def test_any_changed_reviewed_page_makes_evidence_stale(evidence, page, suffix, reader):
    save(evidence, suffix)
    (evidence[0]/page).write_text('Changed after review', encoding='utf-8')
    result = reader(evidence[0], PREFIX)
    assert result['status'] == 'STALE'
    assert result['pages'] == [page]


@pytest.mark.parametrize('checks', [[], [{'name': 'Failed check', 'status': 'FAIL'}], [{'name': '', 'status': 'PASS'}], [{'name': 'Pending check', 'status': 'PENDING'}]])
def test_incomplete_or_failed_browser_checks_are_not_accepted(evidence, checks):
    evidence[1]['checks'] = checks
    save(evidence, 'BrowserQA.json')
    assert browser_evidence(evidence[0], PREFIX)['status'] == 'PENDING'


def test_wrong_revision_and_missing_hash_are_stale(evidence):
    evidence[1]['revision'] = '20261018_v4'
    save(evidence, 'BrowserQA.json')
    assert browser_evidence(evidence[0], PREFIX)['status'] == 'STALE'
    evidence[1]['revision'] = PREFIX.rstrip('_')
    del evidence[1]['page_sha256'][PAGES[2]]
    save(evidence, 'BrowserQA.json')
    assert browser_evidence(evidence[0], PREFIX)['status'] == 'STALE'


def test_url_alone_cannot_establish_publication(evidence):
    evidence[1]['url'] = 'https://example.invalid/'
    del evidence[1]['build_commit']
    save(evidence, 'Deployment.json')
    assert deployment_evidence(evidence[0], PREFIX)['status'] == 'NOT_PERFORMED'


def test_nonpassing_or_unreadable_records_do_not_pass(evidence):
    evidence[1]['status'] = 'FAIL'
    path = save(evidence, 'BrowserQA.json')
    assert browser_evidence(evidence[0], PREFIX)['status'] == 'PENDING'
    path.write_text('{', encoding='utf-8')
    assert browser_evidence(evidence[0], PREFIX)['status'] == 'PENDING'
