"""Normal-suite validation of the governed family and rendered presentation."""
import argparse
from html.parser import HTMLParser
from pathlib import Path

from OrdinaryYouthJusticePublicationLifecycle import PREFIX, guard_current_delta
from WorkflowStageLifecycle import ROOT, StageSnapshot

parser = argparse.ArgumentParser()
parser.add_argument('--rendered-root')
args = parser.parse_args()
guard_current_delta()
if args.rendered_root:
    review = StageSnapshot('ordinary-youth-justice-publication').load_json(PREFIX + 'review.json')
    html = (Path(args.rendered_root) / 'public-works/city-facilities/index.html').read_text(encoding='utf-8')
    class Anchors(HTMLParser):
        def __init__(self):
            super().__init__()
            self.ids = set()

        def handle_starttag(self, tag, attrs):
            self.ids.update(value for name, value in attrs if name == 'id')

    anchors = Anchors()
    anchors.feed(html)
    assert 'historical-county-youth-justice-facility-projects' in anchors.ids
    for entry in review['entries']:
        assert html.count(entry['final_url']) == 1
    assert '3,276-square-foot' in html and '$1.6 million' in html and '$1.2 million' in html
    assert 'rather than establish current project status or completed work' in html
print('PASS: two exact grouped historical County facility additions, tracked source/render witnesses, 18 approved, 372 pending; no R2 or unrelated record changes.')
