"""Freeze authority once; query per record; revalidate before mutation and at completion."""
import argparse
import json
from TaskGovernance import (ROOT, REGISTRY, GovernanceError, active_check, file_hash,
                            freshness, load, population, registry, resolve, validate_plan, write_once)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('resolve')
    p.add_argument('--population', required=True)
    p.add_argument('--output', required=True)
    p = sub.add_parser('check')
    p.add_argument('--population', required=True)
    p.add_argument('--contract', required=True)
    p.add_argument('--plan')
    p.add_argument('--phase', choices=['review', 'mutation'], default='review')
    p = sub.add_parser('active')
    p.add_argument('--phase', choices=['review', 'mutation', 'final'], default='final')
    p.add_argument('--operation')
    p.add_argument('--candidate', action='append', default=[])
    p.add_argument('--page', action='append', default=[])
    p.add_argument('--r2-key')
    p.add_argument('--source-sha256')
    p = sub.add_parser('query')
    p.add_argument('--contract', required=True)
    p.add_argument('--candidate')
    p.add_argument('--governance-id')
    args = parser.parse_args()
    if args.command == 'active':
        result = active_check(args.phase, args.operation, args.candidate, args.page,args.r2_key,args.source_sha256)
    elif args.command == 'query':
        contract = load(args.contract)
        ids = contract['record_rules'][args.candidate] if args.candidate else contract['governance_ids']
        result = [r for r in contract['resolved_rules'] if r['governance_id'] in ids and
                  (not args.governance_id or r['governance_id'] == args.governance_id)]
    else:
        data = registry()
        pop = population(load(args.population))
        if args.command == 'resolve':
            result = resolve(pop, data, file_hash(REGISTRY))
            write_once(args.output, result)
            result = {'contract': args.output, 'applicable_governance_ids': result['governance_ids'],
                      'unresolved_gates': result['unresolved_gates'], 'conflicts': result['conflicts']}
        else:
            contract = load(args.contract)
            freshness(contract, pop, data, file_hash(REGISTRY))
            if args.plan:
                validate_plan(contract, load(args.plan), args.phase)
            result = {'valid': True, 'applicable_rules': len(contract['governance_ids'])}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (GovernanceError, FileNotFoundError, KeyError) as error:
        raise SystemExit('GOVERNANCE FAILURE: ' + str(error))
