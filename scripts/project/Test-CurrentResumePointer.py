from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / 'project-state' / 'CURRENT.md'
text = CURRENT.read_text(encoding='utf-8-sig')

if len(text) > 1800:
    raise SystemExit(f'CURRENT.md exceeds the 1800-character resume-pointer limit ({len(text)}).')
if len(re.findall(r'(?m)^# Current project state\s*$', text)) != 1:
    raise SystemExit('CURRENT.md must have exactly one current-state heading.')
if re.search(r'(?im)^##\s+(historical|superseded|previous|prior)\b', text):
    raise SystemExit('CURRENT.md contains an embedded historical resume block.')

required_links = (
    'governance/active-task.json',
    'governance/pr207-owner-correction-2026-09-30/receipt.json',
    'governance/pr207-postmerge-closeout-2026-09-30/receipt.json',
    'governance/pr207-final-ref-verification-2026-09-30/final-verification.json',
    'governance/approved-queue-lightweight-triage-2026-09-30/triage.json',
    'ordinary-queue-current.json',
    'governance-workflow.md',
    'governance-registry.json',
)
missing = [link for link in required_links if f']({link})' not in text]
if missing:
    raise SystemExit('CURRENT.md is missing resume links: ' + ', '.join(missing))
for link in required_links:
    if not (ROOT / 'project-state' / link).is_file():
        raise SystemExit('CURRENT.md links to a missing artifact: ' + link)

print('CURRENT.md resume-pointer regression passed.')
