"""Verify the bounded Open Space map correction and optional rendered pages."""
import argparse
from pathlib import Path
from urllib.request import Request, urlopen
from OpenSpaceMapQualityLifecycle import guard_current_delta
from WorkflowStageLifecycle import ROOT

parser = argparse.ArgumentParser()
parser.add_argument('--rendered-root')
parser.add_argument('--preview')
args = parser.parse_args()
data = guard_current_delta()
assert len(data['target_ids']) == 18 and len(data['changed_pages']) == 2
if args.rendered_root or args.preview:
    for page in data['changed_pages']:
        route = page.removeprefix('content/').removesuffix('.md') + '/'
        if args.preview:
            url = args.preview.rstrip('/') + '/' + route
            body = urlopen(Request(url, headers={'User-Agent': 'ABQInfo review validation'}), timeout=45).read().decode('utf-8')
        else:
            body = (Path(args.rendered_root) / route / 'index.html').read_text(encoding='utf-8')
        assert 'GARTC-Linked Open Space Trailhead Maps' in body
        assert 'Paseo de la Mesa' in body
        assert 'Foothills' in body
        if page.endswith('maps.md'):
            assert 'Archived Open Space Maps and Guides' in body
            assert 'cabq.gov' in body
print('PASS: 18 assessed records, two bounded pages, exact 1517-to-1499 fresh quality delta, preserved originals and historical witness' + (', rendered pages' if args.rendered_root or args.preview else ''))

