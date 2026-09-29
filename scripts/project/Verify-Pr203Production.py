"""Verify PR #203's merged Open Space presentation and existing public bytes."""

import hashlib
import json
import runpy
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / 'project-state/governance/pr203-postmerge-closeout-2026-09-28'
REVIEW = ROOT / 'project-state/discovery/open-space-map-quality-2026-09-28'
MERGE = 'c901990afb47902755f6e293f2ea801fbaebc041'
HEAD = '164d955d72300824cd8c561290caeb3fbf4baac6'
PREVIEW = 'https://codex-publication-quality-ar.abqinfo.pages.dev'
ROUTES = {
    'content/maps-data/maps.md': ('maps-data/maps', ('archived-open-space-maps-and-guides', 'gartc-linked-open-space-trailhead-maps')),
    'content/public-works/parks-recreation.md': ('public-works/parks-recreation', ('gartc-linked-open-space-trailhead-maps',)),
}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()


def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (ABQInfo PR203 production verification)'})
    with urllib.request.urlopen(request, timeout=90) as response:
        assert response.status == 200 and response.url == url, (url, response.status, response.url)
        return response.read()


def save_once(name, value):
    with (TASK / name).open('x', encoding='utf-8', newline='\n') as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write('\n')


def archive_check(item):
    data = get(item['public_url'])
    digest = hashlib.sha256(data).hexdigest()
    assert len(data) == item['public_size_bytes'] and digest == item['public_sha256'], item['id']
    return {'id': item['id'], 'url': item['public_url'], 'http_status': 200,
            'size_bytes': len(data), 'sha256': digest, 'matches_reviewed_inventory': True}


def main():
    assert git('rev-parse', MERGE + '^{tree}') == git('rev-parse', HEAD + '^{tree}')
    assert git('rev-parse', MERGE + ':content') == git('rev-parse', HEAD + ':content')
    checks = json.loads(subprocess.check_output([
        'gh', 'api', 'repos/armandhammer/abqinfo/commits/' + MERGE + '/check-runs'], cwd=ROOT))
    runs = [{key: row.get(key) for key in ('name', 'status', 'conclusion', 'head_sha', 'external_id', 'details_url')}
            for row in checks['check_runs'] if row['name'] == 'Cloudflare Pages']
    assert len(runs) == 1
    run, = runs
    assert run['status'] == 'completed' and run['conclusion'] == 'success' and run['head_sha'] == MERGE
    deployment_url = 'https://' + run['external_id'][:8] + '.abqinfo.pages.dev'
    deployment = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'merge_commit': MERGE,
                  'reviewed_head': HEAD, 'merge_tree': git('rev-parse', MERGE + '^{tree}'),
                  'reviewed_head_tree': git('rev-parse', HEAD + '^{tree}'), 'check_runs': runs,
                  'deployment_url': deployment_url}

    helper = runpy.run_path(str(ROOT / 'scripts/project/Verify-Pr198Production.py'))
    Article = helper['Article']
    normalize = helper['normalize_cloudflare_email']
    normalize_links = runpy.run_path(str(ROOT / 'scripts/project/Verify-Pr202Production.py'))['normalize_protected_email_links']
    review = json.loads((REVIEW / 'review.json').read_text(encoding='utf-8'))
    byte_review = json.loads((REVIEW / 'public-byte-measurements.json').read_text(encoding='utf-8'))
    observations = review['record_observations']
    assert len(observations) == len(byte_review['records']) == 18
    pages, productions = [], []
    for path, (route, required_anchors) in ROUTES.items():
        urls = {'production': 'https://abqinfo.com/' + route + '/',
                'merge_deployment': deployment_url + '/' + route + '/',
                'reviewed_preview': PREVIEW + '/' + route + '/'}
        witnesses, presentations = [], []
        for label, url in urls.items():
            body = get(url)
            html, decoded = normalize(body.decode('utf-8'))
            parser = Article()
            parser.feed(html)
            presentation = normalize_links(parser.result())
            presentations.append(presentation)
            semantic = json.dumps(presentation, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            witnesses.append({'label': label, 'url': url, 'http_status': 200,
                              'html_sha256': hashlib.sha256(body).hexdigest(),
                              'article_sha256': hashlib.sha256(semantic).hexdigest(),
                              'cloudflare_email_links_decoded_for_comparison': decoded})
        assert presentations[0] == presentations[1] == presentations[2], route
        assert set(required_anchors) <= set(presentations[0][2]), route
        productions.append(presentations[0])
        pages.append({'file': path, 'route': '/' + route + '/', 'witnesses': witnesses,
                      'required_anchors': list(required_anchors), 'article_identical_across_witnesses': True})
    links = [link for _, page_links, _ in productions for link in page_links]
    for row in observations:
        assert row['source_url'] in links, row['id'] + ': missing official source link'
        if row.get('archive_url'):
            assert row['archive_url'] in links, row['id'] + ': missing archive link'
    production = {'result': 'passed', 'verified_at_utc': datetime.now(timezone.utc).isoformat(),
                  'merge_commit': MERGE, 'reviewed_head': HEAD, 'merge_tree_matches_reviewed_head': True,
                  'deployment_url': deployment_url, 'reviewed_preview_url': PREVIEW,
                  'production_url': 'https://abqinfo.com', 'pages': pages,
                  'family_records_with_official_source_links': 18,
                  'family_records_with_archive_links': 16}

    archived = [row for row in byte_review['records'] if row.get('matches_inventory')]
    supporting = [row for row in byte_review['records'] if row.get('supporting_source_only')]
    assert len(archived) == 16 and len(supporting) == 2
    with ThreadPoolExecutor(max_workers=4) as pool:
        verified = list(pool.map(archive_check, archived))
    public_bytes = {'result': 'passed', 'verified_at_utc': datetime.now(timezone.utc).isoformat(),
                    'controlling_review_receipt': 'project-state/discovery/open-space-map-quality-2026-09-28/public-byte-measurements.json',
                    'verified_archive_count': len(verified),
                    'verified_archive_bytes': sum(row['size_bytes'] for row in verified),
                    'official_html_source_count': len(supporting), 'records': verified}
    save_once('merge-deployment.json', deployment)
    save_once('production-verification.json', production)
    save_once('public-byte-verification.json', public_bytes)
    print('PASS: two production pages match merge deployment and reviewed preview; 18 source links, 16 archive links and exact public bytes verified.')


if __name__ == '__main__':
    main()
