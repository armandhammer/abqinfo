"""Render the frozen saved HTML witnesses offline; no live browser session or fetch."""
import hashlib
import io
import json
import tarfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PREFIX = ROOT / 'project-state/governance/ordinary-youth-justice-publication-2026-09-30'


def main():
    population = json.loads((PREFIX / 'population.json').read_text(encoding='utf-8'))
    manifest = json.loads((ROOT / 'project-state/discovery/human-review-reassessment-2026-09-26/retrievals.json').read_text(encoding='utf-8'))
    records = []
    with tarfile.open(PREFIX / 'source-evidence.tar.gz', 'w:gz') as bundle, sync_playwright() as renderer:
        browser = renderer.chromium.launch(headless=True)
        context = browser.new_context(java_script_enabled=False, viewport={'width': 1280, 'height': 1000})
        context.route('**/*', lambda route: route.abort())
        for rid in population['candidate_ids']:
            original = next(r for r in manifest['records'] if r.get('id') == rid and r.get('http_status') == 200)
            body = (ROOT / original['saved_source']).read_bytes()
            assert len(body) == original['size_bytes']
            assert hashlib.sha256(body).hexdigest() == original['sha256']
            member = rid + '.html'
            info = tarfile.TarInfo(member)
            info.size = len(body)
            info.mtime = 0
            bundle.addfile(info, io.BytesIO(body))
            page = context.new_page()
            page.set_content(body.decode('utf-8'), wait_until='domcontentloaded')
            content = page.locator('.et_pb_text_inner').filter(has_text='Project Scope')
            assert content.count() == 1
            text = content.inner_text()
            substantive = text.split('Project Contact Information')[0].strip()
            image = PREFIX / (rid + '.png')
            content.screenshot(path=str(image))
            records.append({**{k: original[k] for k in ('id', 'final_url', 'retrieved_at', 'http_status', 'size_bytes', 'sha256', 'content_type', 'saved_source')},
                            'member': member, 'source_text': substantive,
                            'extracted_word_count': len(substantive.split()),
                            'render': image.relative_to(ROOT).as_posix(),
                            'render_sha256': hashlib.sha256(image.read_bytes()).hexdigest()})
            page.close()
        browser.close()
    receipt = {'artifact_type': 'offline_saved_source_rendering', 'records': records,
               'bundle': (PREFIX / 'source-evidence.tar.gz').relative_to(ROOT).as_posix(),
               'bundle_sha256': hashlib.sha256((PREFIX / 'source-evidence.tar.gz').read_bytes()).hexdigest(),
               'render_method': 'Offline Chromium artifact renderer, exact full saved HTML, scripts disabled, external network blocked; crop of substantive project content.',
               'fidelity_limit': 'External styles/fonts/facade photographs are unavailable; the complete project text and inline HTML are rendered. This is saved source evidence, not a fresh source retrieval or current live-site appearance.'}
    (PREFIX / 'source-rendering.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('Rendered and bundled exactly two recorded HTTP 200 HTML witnesses.')


if __name__ == '__main__':
    main()
