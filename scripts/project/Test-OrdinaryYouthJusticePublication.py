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
    stage = StageSnapshot('ordinary-youth-justice-publication')
    review = stage.load_json(PREFIX + 'review.json')
    html = (Path(args.rendered_root) / 'public-works/city-facilities/index.html').read_text(encoding='utf-8')
    class Anchors(HTMLParser):
        def __init__(self):
            super().__init__()
            self.ids = set()

        def handle_starttag(self, tag, attrs):
            self.ids.update(value for name, value in attrs if name == 'id')

    anchors = Anchors()
    anchors.feed(html)
    if stage.end:
        # Historical positive checks above remain pinned to the sealed stage.
        # The current rendering implements the owner's later exclusion.
        assert 'historical-county-youth-justice-facility-projects' not in anchors.ids
        for entry in review['entries']:
            assert entry['final_url'] not in html
        assert 'selected County public-service facilities' not in html
    else:
        assert 'historical-county-youth-justice-facility-projects' in anchors.ids
        for entry in review['entries']:
            assert html.count(entry['final_url']) == 1
        assert '3,276-square-foot' in html and '$1.6 million' in html and '$1.2 million' in html
        assert 'rather than establish current project status or completed work' in html
print('PASS: sealed youth-justice publication/source history; current rendered page follows owner exclusion when the publication stage is sealed.')
