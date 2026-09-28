"""Verify PR #202 production, merge deployment, and reviewed preview."""

import hashlib
import json
import re
import runpy
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / 'project-state/governance/pr202-postmerge-closeout-2026-09-28'
MERGE = 'b6f25b238e5bbdfe9a6c31fc9197a4530a6c0e03'
REVIEWED = '5d8c5cdc1bf0d43c4d5b49d26e3774d354e43137'
PREVIEW = 'https://bee536ea.abqinfo.pages.dev'
ROUTES = {
    'content/transportation/roadway-projects/_index.md': (
        'transportation/roadway-projects',
        ('recent-projects-20212026', 'past-projects-2020-and-earlier'),
    ),
    'content/transportation/bicycling/projects/_index.md': (
        'transportation/bicycling/projects',
        ('recent-projects-20212026', 'past-projects-2020-and-earlier'),
    ),
    'content/transportation/transit/abq-ride.md': (
        'transportation/transit/abq-ride', ('valley-bus-shelter-history',),
    ),
    'content/transportation/transit/rail-runner.md': (
        'transportation/transit/rail-runner', ('current-rider-information',),
    ),
}
PROTECTED_EMAIL = re.compile(r'^/cdn-cgi/l/email-protection#([0-9a-f]+)$')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8').strip()


def normalize_protected_email_links(presentation):
    text, links, anchors = presentation
    normalized = []
    for link in links:
        match = PROTECTED_EMAIL.fullmatch(link)
        if match:
            encoded = bytes.fromhex(match.group(1))
            address = bytes(value ^ encoded[0] for value in encoded[1:]).decode('utf-8')
            assert re.fullmatch(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+', address)
            link = 'mailto:' + address
        normalized.append(link)
    return text, normalized, anchors


def main():
    assert git('rev-parse', MERGE + '^{tree}') == git('rev-parse', REVIEWED + '^{tree}')
    assert git('rev-parse', MERGE + ':content') == git('rev-parse', REVIEWED + ':content')
    deployment = json.loads((TASK / 'merge-deployment.json').read_text(encoding='utf-8'))
    assert deployment['merge_tree'] == git('rev-parse', MERGE + '^{tree}')
    assert deployment['reviewed_head_tree'] == deployment['merge_tree']
    assert deployment['merge_commit'] == MERGE and deployment['reviewed_head'] == REVIEWED
    check, = deployment['check_runs']
    assert check['head_sha'] == MERGE and check['status'] == 'completed' and check['conclusion'] == 'success'
    merge_url = 'https://' + check['external_id'][:8] + '.abqinfo.pages.dev'
    helper = runpy.run_path(str(ROOT / 'scripts/project/Verify-Pr198Production.py'))
    get, Article, normalize = helper['get'], helper['Article'], helper['normalize_cloudflare_email']
    review = json.loads((ROOT / 'project-state/governance/ordinary-transport-projects-2026-09-28/review.json').read_text(encoding='utf-8'))
    entries = review['entries']
    pages = []
    for page, (route, required_anchors) in ROUTES.items():
        urls = {
            'production': 'https://abqinfo.com/' + route + '/',
            'merge_deployment': merge_url + '/' + route + '/',
            'reviewed_preview': PREVIEW + '/' + route + '/',
        }
        witnesses, presentations = [], []
        for label, url in urls.items():
            body = get(url)
            html, decoded = normalize(body.decode('utf-8'))
            parser = Article()
            parser.feed(html)
            presentation = normalize_protected_email_links(parser.result())
            presentations.append(presentation)
            semantic = json.dumps(presentation, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            witnesses.append({
                'label': label, 'url': url, 'http_status': 200,
                'html_sha256': hashlib.sha256(body).hexdigest(),
                'article_sha256': hashlib.sha256(semantic).hexdigest(),
                'cloudflare_email_links_decoded_for_comparison': decoded,
            })
        assert presentations[0] == presentations[1] == presentations[2], route
        text, links, anchors = presentations[0]
        assert set(required_anchors) <= set(anchors), route + ': missing required anchor'
        selected = [row for row in entries if row['page'] == page]
        for row in selected:
            assert links.count(row['source_url']) == 1, row['id'] + ': source link count'
            assert row['label'] in text, row['id'] + ': visible title missing'
        if page in ('content/transportation/roadway-projects/_index.md',
                    'content/transportation/bicycling/projects/_index.md'):
            assert 'Recent Projects (2021–2026)' in text
            assert 'Current Projects (2021–2026)' not in text
            assert 'Past Projects (2020 and Earlier)' in text
        pages.append({
            'route': '/' + route + '/', 'witnesses': witnesses,
            'required_anchors': list(required_anchors),
            'added_source_links_verified': len(selected),
            'article_identical_across_witnesses': True,
        })
    assert sum(page['added_source_links_verified'] for page in pages) == 21
    result = {
        'result': 'passed', 'verified_at': datetime.now(timezone.utc).isoformat(),
        'merge_commit': MERGE, 'reviewed_head': REVIEWED,
        'merge_tree_matches_reviewed_head': True,
        'merge_deployment_url': merge_url, 'reviewed_preview_url': PREVIEW,
        'production_url': 'https://abqinfo.com', 'pages': pages,
    }
    (TASK / 'production-verification.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS: four production pages match the merge deployment and reviewed preview; 21 source links and required anchors verified.')


if __name__ == '__main__':
    main()
