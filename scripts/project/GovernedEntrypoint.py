"""Fail-closed CLI gate for substantive tools; isolated tmp fixtures are not project tasks."""
import json
import sys
import tempfile
from pathlib import Path
from TaskGovernance import ROOT, GovernanceError, active_check, load, require


def require_tool_governance(script, arguments=None):
    arguments = list(sys.argv[1:] if arguments is None else arguments)
    relative=Path(script).resolve().relative_to(ROOT).as_posix()
    manifest=load('project-state/governance/entrypoints.json')
    tool=manifest['tools'][relative]
    # Explicit fixture inventory paths cannot write authoritative inventory via these tools.
    for option in ('--inventory','--master','--inventory-path'):
        if option in arguments:
            value=Path(arguments[arguments.index(option)+1])
            target=(ROOT/value).resolve() if not value.is_absolute() else value.resolve()
            if target.is_relative_to(ROOT/'tmp') or (target.is_relative_to(Path(tempfile.gettempdir()).resolve()) and not target.is_relative_to(ROOT)):
                if tool['operation_class'] not in ('document_review','family_review','quality_assessment'):
                    return
                records=json.loads(target.read_text(encoding='utf-8-sig')).get('candidates',[])
                if records and all(r['id'].startswith('test-') or '/test/' in str(r.get('source_url','')) or
                                   'example.' in str(r.get('source_url','')) or 'fixture' in ' '.join(r.get('processing_notes',[])).lower() for r in records):
                    return
    if '--check' in arguments and tool.get('check_is_read_only'):
        return
    operation=tool['operation_class']
    if relative.endswith('BackgroundCampaign.py'):
        # Its own gate uses the actual campaign operation and frozen IDs.
        return
    active_check('review' if operation in ('document_review','family_review','quality_assessment') else 'mutation',
                 operation,tool.get('candidate_ids',[]),tool.get('pages',[]))
