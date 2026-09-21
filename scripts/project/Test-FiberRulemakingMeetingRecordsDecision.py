#!/usr/bin/env python3
"""Validate the bounded June 2025 fiber-rulemaking meeting-record decision."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
decision = json.loads((ROOT / 'project-state/discovery/fiber-rulemaking-meeting-records-decision-2026-09-19.json').read_text(encoding='utf-8-sig'))
inventory = json.loads((ROOT / 'project-state/master-inventory.json').read_text(encoding='utf-8-sig'))
checkpoint = json.loads((ROOT / 'project-state/checkpoint.json').read_text(encoding='utf-8-sig'))
records = {row['id']: row for row in inventory['candidates']}

scope = {'src-05b68a5758490499', 'src-09592fba403c1e2f', 'src-2883388452797b58', 'src-b8b28358abc9a2de'}
assert set(decision['family']['scope_candidate_ids']) == scope
assert records['src-09592fba403c1e2f']['status'] == 'excluded'
assert records['src-2883388452797b58']['status'] == 'excluded'
assert records['src-b8b28358abc9a2de']['status'] == 'approved for addition'
assert records['src-05b68a5758490499']['status'] == 'requires human review'
assert records['src-09592fba403c1e2f']['checksum_sha256'] == 'dc0a42ea83998ce66b0e1add2a5c52048f12d3d6a41d4431dcbc48fc4908206b'
assert records['src-2883388452797b58']['checksum_sha256'] == '7fd4846bd508a3e466576a11574c172e22a21fce504e8547b9d012a88306bade'
assert records['src-b8b28358abc9a2de']['checksum_sha256'] == '068cc29a12e49e546a56d83f247ba2ecb7f05b80e3f4a03d4e0b2077891eb687'
assert records['src-b8b28358abc9a2de']['r2_url'] is None
assert records['src-b8b28358abc9a2de']['implementation_location'] is None
assert len(decision['quality_assessments']) == 1
assert decision['quality_assessments'][0]['id'] == 'src-b8b28358abc9a2de'
assert 'not a minute' not in records['src-09592fba403c1e2f']['exclusion_reason'].lower() or 'not official minutes' in records['src-09592fba403c1e2f']['validation_status']
assert decision['ordinary_queue_handoff']['next_actionable_candidate'] == 'src-09a0152fb526fcba'
assert 'src-09b266eabc8aa975' in checkpoint['resume_command']
assert 'src-09a90d2b97f9bd12' not in checkpoint['resume_command']
assert checkpoint['counts_by_status'] == inventory['counts']
print('PASS: June 2025 fiber rulemaking family is bounded, provenance-preserving, and non-publication-safe.')
