"""Defensive contract-byte regressions; no change to settled authority."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts/project'))
import TaskGovernance as G


def main():
    passed = []
    with tempfile.TemporaryDirectory(dir=G.ROOT / 'tmp') as directory:
        root = Path(directory)
        task_path = root / 'active-task.json'
        contract_path = root / 'contract.json'
        task_path.write_text(json.dumps({
            'state': 'in_progress', 'contract': str(contract_path),
        }), encoding='utf-8')
        for label, contents in [('empty_contract', ''),
                                ('malformed_contract', '{"schema_version":')]:
            contract_path.write_text(contents, encoding='utf-8')
            with patch.object(G, 'ACTIVE_TASK', str(task_path)), \
                 patch.object(G, 'registry', return_value={}), \
                 patch.object(G, 'validate_plan') as validate, \
                 patch.object(G, 'changed_paths') as delta:
                try:
                    G.active_check('mutation', 'content_implementation')
                except json.JSONDecodeError:
                    passed.append(label + '_fails_before_substantive_operation')
                else:
                    raise AssertionError('Governance accepted ' + label)
                validate.assert_not_called()
                delta.assert_not_called()
    print(json.dumps({'result': 'passed', 'checks': passed}, indent=2))


if __name__ == '__main__':
    main()
