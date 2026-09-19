#!/usr/bin/env python3
"""Regression check for generic canonical terminal-decision retention."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APPLIER = ROOT / 'scripts/project/Apply-SavedTerminalResearch.py'

research = {
    'decisions': [
        {'id': 'copy', 'recommended_status': 'duplicate', 'canonical_id': 'canonical', 'relationship': 'Byte-identical delivery copy.'},
        {'id': 'older', 'recommended_status': 'superseded', 'canonical_id': 'canonical', 'relationship': 'Replaced by the retained final version.'},
        {'id': 'excluded', 'recommended_status': 'excluded', 'exclusion_reason': 'Not a distinct record.'},
    ]
}

def candidate(candidate_id, source_url):
    return {
        'id': candidate_id, 'status': 'pending review', 'source_url': source_url,
        'direct_file_url': None, 'cited_successors': [], 'processing_notes': [],
        'exclusion_reason': None, 'validation_status': 'not run',
    }

inventory = {
    'allowed_statuses': ['pending review', 'duplicate', 'superseded', 'excluded'],
    'candidates': [
        candidate('canonical', 'https://example.test/canonical.pdf'),
        candidate('copy', 'https://example.test/copy.pdf'),
        candidate('older', 'https://example.test/older.pdf'),
        candidate('excluded', 'https://example.test/excluded.pdf'),
    ],
}

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    research_path, inventory_path = root / 'research.json', root / 'inventory.json'
    research_path.write_text(json.dumps(research), encoding='utf-8')
    inventory_path.write_text(json.dumps(inventory), encoding='utf-8')
    subprocess.run([
        sys.executable, str(APPLIER), '--research', str(research_path),
        '--inventory', str(inventory_path), '--ids', 'copy,older,excluded',
        '--updated-at', '2026-09-19T00:00:00Z',
    ], check=True)
    rows = {row['id']: row for row in json.loads(inventory_path.read_text(encoding='utf-8'))['candidates']}
    for candidate_id, status, relation in (
        ('copy', 'duplicate', 'Byte-identical delivery copy.'),
        ('older', 'superseded', 'Replaced by the retained final version.'),
    ):
        row = rows[candidate_id]
        assert row['status'] == status
        assert row['cited_successors'] == ['https://example.test/canonical.pdf']
        assert 'canonical inventory record canonical' in row['exclusion_reason']
        assert relation in row['exclusion_reason']
        assert 'canonical relationship retained' in row['validation_status']
        assert any('canonical inventory record canonical' in note for note in row['processing_notes'])
    assert rows['excluded']['exclusion_reason'] == 'Not a distinct record.'

print('PASS: terminal duplicate and superseded decisions retain canonical provenance generically.')
