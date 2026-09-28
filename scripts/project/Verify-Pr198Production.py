"""Verify the reviewed PR #198 presentation and exact archive bytes in production."""

import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / 'project-state/governance/pr198-postmerge-closeout-2026-09-27'
MERGE = '2cc6a349193004b41e42370b2554cd263bde1247'
REVIEWED = 'https://7ded2712.abqinfo.pages.dev'
ROUTES = {
    'city-data/capital-spending': (
        '2009-general-obligation-bond-program',
        '2011-published-scope-and-version-records',
        'october-2010-program-scope-and-schedule-records',
    ),
    'city-data/public-safety-data': ('fire-and-emergency-response',),
    'development-land-use/redevelopment-plans': ('historical-capital-programming',),
    'public-works/city-facilities': ('historical-capital-programming',),
    'transportation/transit/abq-ride': ('facilities-and-fleet-planning-history',),
    'transportation/transportation-plans': ('historical-capital-programming',),
}
ARCHIVES = [
    ('city-data/capital-spending/abqinfo-2009-general-obligation-bond-program-historical-master-record.pdf',
     1303860, 'ae2a1567476cf966b87b87c268dfd8795ad5ea6a5bc474ed4e009bc4b42830af'),
    ('city-data/capital-spending/abqinfo-2011-go-bond-october-2010-preliminary-epc-program-record.pdf',
     1031416, '3c5b2bd8eba451ccd30f5d90d7b69bc79dfb42d7563aefcc0139e5278a946de5'),
    ('city-data/capital-spending/abqinfo-2011-go-bond-published-program-record.pdf',
     2313619, '6a62e7a944e3c55ddd08127c7a2bb6e54fe7f08a4d5bb8b6723c9ecea1283015'),
    ('city-data/capital-spending/cabq-2009-senior-family-community-center-community-enhancement-bond-authorization.pdf',
     51609, '35e61882cbe73dc7c4ab0b0ca11ae859ed5073b383cdc0f5d8c8c92eee0448b1'),
]


class Article(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.found = False
        self.text = []
        self.links = []
        self.anchors = []

    def handle_starttag(self, tag, attrs):
        if tag == 'article' and self.depth == 0:
            self.depth = 1
            self.found = True
        elif self.depth and tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img',
                                      'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.depth += 1
        if self.depth:
            values = dict(attrs)
            if tag == 'a' and 'href' in values:
                self.links.append(values['href'])
            if 'id' in values:
                self.anchors.append(values['id'])

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.text.append(data)

    def result(self):
        assert self.found, 'No rendered article'
        return (' '.join(' '.join(self.text).split()), self.links, self.anchors)


def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (ABQInfo production verification)'})
    with urllib.request.urlopen(request, timeout=40) as response:
        assert response.status == 200 and response.url == url, (url, response.status, response.url)
        return response.read()


def normalize_cloudflare_email(html):
    """Undo Cloudflare's runtime email obfuscation for a semantic comparison."""
    pattern = re.compile(
        r'<a href="/cdn-cgi/l/email-protection#[0-9a-f]+"><span class="__cf_email__" '
        r'data-cfemail="([0-9a-f]+)">\[email&#160;protected\]</span></a>')

    def decode(match):
        encoded = bytes.fromhex(match.group(1))
        address = bytes(byte ^ encoded[0] for byte in encoded[1:]).decode('utf-8')
        assert re.fullmatch(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+', address)
        return '<a href="mailto:' + address + '">' + address + '</a>'

    return pattern.subn(decode, html)


def main():
    deployment = json.loads((TASK / 'merge-deployment.json').read_text(encoding='utf-8-sig'))
    assert deployment['merge_commit'] == MERGE and deployment['total_count'] == 1
    check, = deployment['check_runs']
    assert check['head_sha'] == MERGE and check['name'] == 'Cloudflare Pages'
    assert check['status'] == 'completed' and check['conclusion'] == 'success'
    merge_url = 'https://' + check['external_id'][:8] + '.abqinfo.pages.dev'

    pages = []
    for route, required_anchors in ROUTES.items():
        urls = {'production': 'https://abqinfo.com/' + route + '/',
                'merge_deployment': merge_url + '/' + route + '/',
                'reviewed_preview': REVIEWED + '/' + route + '/'}
        witnesses = []
        representations = []
        for label, url in urls.items():
            body = get(url)
            normalized, obfuscated_emails = normalize_cloudflare_email(body.decode('utf-8'))
            parser = Article()
            parser.feed(normalized)
            representation = parser.result()
            representations.append(representation)
            semantic = json.dumps(representation, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            witnesses.append({'label': label, 'url': url, 'http_status': 200,
                              'html_sha256': hashlib.sha256(body).hexdigest(),
                              'article_sha256': hashlib.sha256(semantic).hexdigest(),
                              'cloudflare_email_links_decoded_for_comparison': obfuscated_emails})
        assert representations[0] == representations[1] == representations[2], route
        assert set(required_anchors) <= set(representations[0][2]), route + ': missing changed-section anchor'
        if route == 'city-data/capital-spending':
            text, links, _ = representations[0]
            assert '2009 Senior, Family, Community Center, and Community Enhancement Project Bond Authorization' in text
            assert all('https://files.abqinfo.com/' + key in links for key, _, _ in ARCHIVES)
        pages.append({'route': '/' + route + '/', 'witnesses': witnesses,
                      'required_anchors': list(required_anchors),
                      'article_identical_across_witnesses': True})

    archives = []
    for key, size, expected_hash in ARCHIVES:
        url = 'https://files.abqinfo.com/' + key
        body = get(url)
        actual_hash = hashlib.sha256(body).hexdigest()
        assert len(body) == size and actual_hash == expected_hash, url
        archives.append({'url': url, 'http_status': 200, 'size_bytes': len(body),
                         'sha256': actual_hash, 'exact_public_bytes': True})

    result = {'result': 'passed', 'verified_at': datetime.now(timezone.utc).isoformat(),
              'merge_commit': MERGE, 'merge_deployment_url': merge_url,
              'reviewed_preview_url': REVIEWED, 'production_url': 'https://abqinfo.com',
              'pages': pages, 'archives': archives}
    (TASK / 'production-verification.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS: six production pages match merge deployment and reviewed preview; four exact public PDF downloads verified.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('FAIL:', exc, file=sys.stderr)
        raise
