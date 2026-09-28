"""Local-only preparation of the settled PR198 masters; no inventory/R2 edits."""
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts/project'))
import TaskGovernance as G

BASE = Path('project-state/governance/pr198-resume-2026-09-27')
OUTPUT = Path('output/pdf/pr198-resume')


def verified(path, size, checksum):
    return path.is_file() and path.stat().st_size == size and hashlib.sha256(path.read_bytes()).hexdigest() == checksum


def main():
    G.active_check('mutation', 'consolidation')
    decision = G.load('project-state/discovery/2009-capital-spending-consolidation-decision-2026-09-18.json')
    manifest2011 = G.load('project-state/discovery/2011-capital-spending-consolidation-manifest-2026-09-18.json')
    ids = {s['candidate_id'] for s in decision['proposed_compilation']['components']}
    ids.update(s['candidate_id'] for c in manifest2011['compilations'] for s in c['sources'])
    records = {r['id']: r for r in G.load('project-state/master-inventory.json')['candidates'] if r['id'] in ids}
    spec = importlib.util.spec_from_file_location('historical_builder', G.ROOT / 'scripts/project/Build-HistoricalCompilationPdf.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    sources = []
    for s in decision['proposed_compilation']['components']:
        r = records[s['candidate_id']]
        checksum = s['checksum_sha256'] or s['saved_research_checksum_sha256']
        assert checksum == r['checksum_sha256'] and s['size_bytes'] == r['size_bytes']
        path = Path(r['local_path'])
        if not verified(path, s['size_bytes'], checksum):
            candidates = list(Path('research/staging').rglob(s['candidate_id'] + '*.pdf'))
            candidates += list(Path('tmp/pr198-resume-sources').glob(s['candidate_id'] + '*.pdf'))
            path = next(p for p in candidates if verified(p, s['size_bytes'], checksum))
        sources.append({
            'candidate_id': s['candidate_id'], 'title': r['title'], 'date': '2009',
            'source_url': s['official_source_url'], 'archive_url': r['r2_url'],
            'archive_status': 'verified_public_r2', 'size_bytes': s['size_bytes'],
            'checksum_sha256': checksum, 'local_path': path.as_posix(),
        })
    # Implement the explicitly settled source chronology using its saved hashes.
    # The historical proposal's last two array positions reverse that chronology.
    streets = {s['candidate_id']: s for s in sources[-2:]}
    assert set(streets) == {'src-5066c9f642369e9b', 'src-5cea73d2df70dabb'}
    sources[-2:] = [streets['src-5066c9f642369e9b'], streets['src-5cea73d2df70dabb']]
    sources[-2]['date'] = 'Created December 16, 2008'
    sources[-1]['date'] = 'Created June 2, 2009'
    manifest = {
        'title': decision['proposed_compilation']['title'],
        'short_title': '2009 General Obligation Bond Program',
        'record_label': 'Program / component', 'source_record_label': 'Original City program component',
        'date_label': 'Record date', 'contents_page_row_counts': [6, 9, 9],
        'coverage_note': 'Funding allocation and totals followed by program groups, with scopes before schedules and both distinct Streets schedule editions in established source chronology.',
        'editorial_note': 'Source order supports historical navigation and carries no final or adopted precedence. The three bond authorizations and enacted priorities resolution remain separate independent instruments.',
        'provenance_note': 'The 24 complete City originals follow individual provenance sheets. Senior Affairs and Family and Community Services remain distinct components. Each original retains its individual archive and official source links.',
        'preservation_notice': 'An ABQInfo historical compilation of 24 complete City documents, separate from the City-issued originals. Each original remains individually preserved with its source link, exact byte size and SHA-256.',
        'sources': sources,
    }
    G.write_once((BASE / '2009-build-manifest.json').as_posix(), manifest)
    builder.build(BASE / '2009-build-manifest.json', OUTPUT / decision['proposed_compilation']['filename'], BASE / '2009-build-validation.json')
    prepared = []
    for c in manifest2011['compilations']:
        for s in c['sources']:
            r = records[s['candidate_id']]
            assert r['size_bytes'] == s['size_bytes'] and r['checksum_sha256'] == s['checksum_sha256']
            assert verified(Path(s['local_path']), s['size_bytes'], s['checksum_sha256'])
            s['archive_url'] = r['r2_url']
            s['archive_status'] = 'verified_public_r2'
            s['archive_label'] = 'Byte-identical archived original'
            s['preservation_note'] = 'The complete original document follows. It remains separately available at its individual archive URL.'
        prefix = '2011-preliminary' if len(c['sources']) == 21 else '2011-published'
        keys = ('title', 'short_title', 'record_label', 'source_record_label', 'date_label', 'coverage_note', 'editorial_note', 'provenance_note', 'preservation_notice', 'contents_page_row_counts', 'sources')
        manifest = {k: c[k] for k in keys}
        if prefix == '2011-published':
            manifest['provenance_note'] = 'All 46 selected City originals remain separately archived with their official source links, exact byte sizes and SHA-256 checksums. The four distinct December 2010 Cultural Services and Parks and Recreation editions were archived after the historical preparation manifest.'
            manifest['preservation_notice'] = 'An ABQInfo historical compilation, separate from the City-issued originals. Each complete City component follows a provenance sheet. All 46 originals remain separately preserved at their individual archive URLs.'
        manifest_path = BASE / (prefix + '-build-manifest.json')
        G.write_once(manifest_path.as_posix(), manifest)
        target = OUTPUT / c['proposed_filename']
        if prefix == '2011-preliminary':
            original = Path(c['local_output_path'])
            assert verified(original, c['build_result']['size_bytes'], c['build_result']['checksum_sha256'])
            shutil.copyfile(original, target)
        else:
            builder.build(manifest_path, target, BASE / '2011-published-build-validation.json')
        prepared.append({'path': target.as_posix(), 'size_bytes': target.stat().st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'component_count': len(c['sources'])})
    G.write_once((BASE / 'pdf-preparation.json').as_posix(), {'prepared_2011': prepared, 'originals_preserved': True, 'inventory_mutations': 0, 'r2_mutations': 0})


if __name__ == '__main__':
    main()
