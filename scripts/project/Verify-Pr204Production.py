"""Verify PR #204 merged County roadway content in production and save witnesses."""

import gzip
import hashlib
import json
import runpy
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / 'project-state/governance/pr204-postmerge-closeout-2026-09-29'
MERGE = 'f4507ade4f0a76465843fd7277c636481028d576'
REVIEWED = '6210ec2452c46d63134bee657b42768cb278e4d3'
BASELINE = '7b28ef1120f7faf7480bdda90a8f0df6a3e31f87'
PAGE = 'content/transportation/roadway-projects/_index.md'
ROUTE = '/transportation/roadway-projects/'
PREVIEW = 'https://9c644b72.abqinfo.pages.dev'
ANCHORS = ('additional-county-corridor-and-crossing-projects',
           'county-street-and-crossing-history')
REVIEW = ROOT / 'project-state/governance/ordinary-county-roadway-2026-09-29/review-v4.json'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8').strip()


def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (ABQInfo PR204 closeout)'})
    with urllib.request.urlopen(request, timeout=60) as response:
        assert response.status == 200 and response.url == url, (url, response.status, response.url)
        return response.read()


def save_json(name, value):
    with (TASK / name).open('x', encoding='utf-8', newline='\n') as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write('\n')


def main():
    assert git('rev-parse', MERGE + '^{tree}') == git('rev-parse', REVIEWED + '^{tree}')
    assert git('rev-parse', MERGE + ':content') == git('rev-parse', REVIEWED + ':content')
    assert git('diff', '--name-only', BASELINE, MERGE, '--', 'content') == PAGE
    review = json.loads(REVIEW.read_text(encoding='utf-8'))
    selected = {entry['id'] for entry in review['entries']}
    assert len(selected) == len(review['entries']) == 6
    assert review['preview_verification']['deployment_url'] == PREVIEW + ROUTE
    assert review['preview_verification']['manual_owner_review'] == 'pending'
    merged_page = git('show', MERGE + ':' + PAGE)
    for entry in review['entries']:
        assert merged_page.count(entry['final_url']) == 1, entry['id']
        assert entry['description'] in merged_page, entry['id']

    checks = json.loads(subprocess.check_output([
        'gh', 'api', 'repos/armandhammer/abqinfo/commits/' + MERGE + '/check-runs'], cwd=ROOT))
    runs = [{key: row.get(key) for key in ('name', 'status', 'conclusion', 'head_sha', 'external_id', 'details_url')}
            for row in checks['check_runs'] if row['name'] == 'Cloudflare Pages']
    assert len(runs) == 1
    run, = runs
    assert run['head_sha'] == MERGE and run['status'] == 'completed' and run['conclusion'] == 'success'
    deployment = 'https://' + run['external_id'][:8] + '.abqinfo.pages.dev'

    helper = runpy.run_path(str(ROOT / 'scripts/project/Verify-Pr198Production.py'))
    Article = helper['Article']
    normalize = helper['normalize_cloudflare_email']
    normalize_links = runpy.run_path(str(ROOT / 'scripts/project/Verify-Pr202Production.py'))['normalize_protected_email_links']
    urls = {'production': 'https://abqinfo.com' + ROUTE,
            'merge_deployment': deployment + ROUTE,
            'reviewed_preview': PREVIEW + ROUTE}
    witnesses = []
    raw = {}
    presentations = {}
    for label, url in urls.items():
        body = get(url)
        raw[label] = body
        html, decoded = normalize(body.decode('utf-8'))
        article = Article()
        article.feed(html)
        presentation = normalize_links(article.result())
        presentations[label] = presentation
        semantic = json.dumps(presentation, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        witnesses.append({'label': label, 'url': url, 'http_status': 200,
                          'size_bytes': len(body), 'html_sha256': hashlib.sha256(body).hexdigest(),
                          'article_sha256': hashlib.sha256(semantic).hexdigest(),
                          'cloudflare_email_links_decoded_for_comparison': decoded})
    assert presentations['production'] == presentations['merge_deployment'] == presentations['reviewed_preview']
    assert hashlib.sha256(raw['reviewed_preview']).hexdigest() == review['preview_verification']['page_sha256']
    text, links, anchors = presentations['production']
    assert set(ANCHORS) <= set(anchors)
    assert len({entry['final_url'] for entry in review['entries']}) == 6
    for entry in review['entries']:
        assert links.count(entry['final_url']) == 1, entry['id']
        assert entry['description'] in text, entry['id']
    assert review['archive_objects_added'] == review['archive_bytes_added'] == 0

    pr = json.loads(subprocess.check_output([
        'gh', 'pr', 'view', '204', '--json', 'number,state,mergedAt,mergeCommit,headRefOid,baseRefOid,url'], cwd=ROOT))
    assert pr['state'] == 'MERGED' and pr['mergeCommit']['oid'] == MERGE and pr['headRefOid'] == REVIEWED
    assert pr['baseRefOid'] == BASELINE
    now = datetime.now(timezone.utc).isoformat()
    merge_receipt = {'checked_at_utc': now, 'pr': pr, 'baseline_commit': BASELINE,
                     'merge_commit': MERGE, 'reviewed_head': REVIEWED,
                     'merge_tree': git('rev-parse', MERGE + '^{tree}'),
                     'reviewed_head_tree': git('rev-parse', REVIEWED + '^{tree}'),
                     'merge_tree_matches_reviewed_head': True,
                     'check_runs': runs, 'deployment_url': deployment}
    production_receipt = {'result': 'passed', 'verified_at_utc': now,
                          'merge_commit': MERGE, 'reviewed_head': REVIEWED,
                          'page': PAGE, 'route': ROUTE, 'witnesses': witnesses,
                          'article_identical_across_witnesses': True,
                          'required_anchors': list(ANCHORS),
                          'required_official_source_links': [
                              {'id': entry['id'], 'url': entry['final_url'], 'count': 1}
                              for entry in review['entries']],
                          'governed_record_count': 6,
                          'archive_objects_added_by_publication': 0,
                          'archive_bytes_added_by_publication': 0}
    for label, name in (('production', 'production.html.gz'),
                        ('merge_deployment', 'merge-deployment.html.gz'),
                        ('reviewed_preview', 'reviewed-preview.html.gz')):
        with (TASK / name).open('xb') as output:
            output.write(gzip.compress(raw[label], compresslevel=9, mtime=0))
    save_json('merge-deployment.json', merge_receipt)
    save_json('production-verification.json', production_receipt)
    print('PASS: PR204 merge tree, production, merge deployment and approved preview agree; six governed links and both anchors verified.')


if __name__ == '__main__':
    main()
