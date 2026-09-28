"""Verify PR #201's merged Capital Spending label and public bytes."""

import hashlib
import json
import runpy
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / 'project-state/governance/pr201-postmerge-closeout-2026-09-28'
MERGE = '25a2fc516c888959dbb97d83829b06a9d8cd62ac'
REVIEWED = '7a3d1fb9708d8a2533793d3c45c3eedd97a87e03'
ROUTE = '/city-data/capital-spending/'
ARCHIVE = 'https://files.abqinfo.com/city-data/capital-spending/cabq-2013-2022-decade-plan-go-bond-program.pdf'
SOURCE = 'https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2013GOBondProgramEPC.pdf'
ARCHIVE_SIZE = 3104041
ARCHIVE_SHA256 = '559f87c5f42affced0a3d52014ed78902770e9e3954cc97930827fe1cef060e4'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8').strip()


def main():
    assert git('rev-parse', MERGE + '^{tree}') == git('rev-parse', REVIEWED + '^{tree}')
    assert git('rev-parse', MERGE + ':content') == git('rev-parse', REVIEWED + ':content')
    assert git('diff', MERGE + '^1', MERGE, '--name-only', '--', 'content', 'layouts', 'assets', 'static', 'hugo.toml') == 'content/city-data/capital-spending.md'
    old = subprocess.check_output(['git', 'show', MERGE + '^1:content/city-data/capital-spending.md'], cwd=ROOT).replace(b'\r\n', b'\n')
    new = subprocess.check_output(['git', 'show', MERGE + ':content/city-data/capital-spending.md'], cwd=ROOT).replace(b'\r\n', b'\n')
    assert old.count(b'EPC-stage book') == 1 and new == old.replace(b'EPC-stage book', b'EPC-Stage Book')

    deployment = json.loads((TASK / 'merge-deployment.json').read_text(encoding='utf-8'))
    check, = deployment['check_runs']
    assert deployment['merge_commit'] == MERGE and check['head_sha'] == MERGE
    assert check['status'] == 'completed' and check['conclusion'] == 'success'
    production_url = 'https://abqinfo.com' + ROUTE
    merge_url = 'https://' + check['external_id'][:8] + '.abqinfo.pages.dev' + ROUTE
    reviewed_url = 'https://codex-capital-spending-title.abqinfo.pages.dev' + ROUTE
    helper = runpy.run_path(str(ROOT / 'scripts/project/Verify-Pr198Production.py'))
    get, Article, normalize = helper['get'], helper['Article'], helper['normalize_cloudflare_email']
    witnesses, presentations = [], []
    for label, url in [('production', production_url), ('merge_deployment', merge_url), ('reviewed_preview', reviewed_url)]:
        body = get(url)
        html, decoded_emails = normalize(body.decode('utf-8'))
        parser = Article()
        parser.feed(html)
        presentation = parser.result()
        presentations.append(presentation)
        witnesses.append({'label': label, 'url': url, 'http_status': 200,
                          'html_sha256': hashlib.sha256(body).hexdigest(),
                          'article_sha256': hashlib.sha256(json.dumps(presentation, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest(),
                          'cloudflare_email_links_decoded_for_comparison': decoded_emails})
    assert presentations[0] == presentations[1] == presentations[2]
    text, links, anchors = presentations[0]
    assert text.count('EPC-Stage Book') == 1 and 'EPC-stage book' not in text
    assert ARCHIVE in links and SOURCE in links
    assert '20132022-epc-program-and-related-summary' in anchors
    archive_body = get(ARCHIVE)
    assert len(archive_body) == ARCHIVE_SIZE and hashlib.sha256(archive_body).hexdigest() == ARCHIVE_SHA256
    result = {'result': 'passed', 'verified_at': datetime.now(timezone.utc).isoformat(),
              'merge_commit': MERGE, 'reviewed_head': REVIEWED,
              'merge_tree_matches_reviewed_head': True, 'only_visible_delta': 'EPC-stage book -> EPC-Stage Book',
              'page': {'route': ROUTE, 'witnesses': witnesses, 'article_identical_across_witnesses': True,
                       'required_anchor': '20132022-epc-program-and-related-summary',
                       'archive_and_source_links_preserved': True},
              'archive': {'url': ARCHIVE, 'http_status': 200, 'size_bytes': ARCHIVE_SIZE,
                          'sha256': ARCHIVE_SHA256, 'exact_public_bytes': True}}
    (TASK / 'production-verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS: production, merge deployment, and reviewed preview show the same corrected article; exact archive bytes verified.')


if __name__ == '__main__':
    main()
