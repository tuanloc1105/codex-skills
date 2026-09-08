#!/usr/bin/env python3
"""Validate recorded dry-run contracts; never invoke or grade a live model."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {'T01', 'T03', *(f'F{i:02}' for i in range(1, 7)),
            *(f'R{i:02}' for i in range(1, 6))}
CANONICAL = {'file', 'line', 'summary', 'failure_scenario'}
ORDER = ['find_verify', 'fix_check', 'reverify_backfill', 'prepare',
         'comment', 'artifact', 'final']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(findings):
    require(isinstance(findings, list), 'canonical output must be an array')
    for item in findings:
        require(isinstance(item, dict) and set(item) == CANONICAL,
                'canonical finding must have exactly four keys')
        require(type(item['line']) is int and item['line'] > 0, 'invalid line')
        for key in CANONICAL - {'line'}:
            require(isinstance(item[key], str) and item[key].strip(), f'empty {key}')


def validate(specs, observations):
    require(isinstance(specs, list) and isinstance(observations, list), 'expected lists')
    cases = {}
    for case in specs:
        require(isinstance(case, dict), 'case must be an object')
        for key in ['id', 'mode', 'prompt', 'expected']:
            require(isinstance(case.get(key), str) and case[key].strip(), f'missing {key}')
        require(case['id'] not in cases, 'duplicate case ID')
        require(isinstance(case.get('contract'), dict), 'missing case contract')
        cases[case['id']] = case
    require(set(cases) == REQUIRED, 'missing or unexpected scenario IDs')
    seen = set()
    actual = {}
    for record in observations:
        require(isinstance(record, dict), 'observation must be an object')
        key = record.get('id')
        require(key in cases and key not in seen, 'unknown or duplicate observation')
        seen.add(key)
        for field in ['mode', 'prompt', 'expected']:
            require(record.get(field) == cases[key][field], f'{key}: stale {field}')
        require(record.get('provenance') == 'same-context coordinator dry-run',
                f'{key}: this recorded suite is not an independent model run')
        require(record.get('assessment') == 'pass', f'{key}: failed/unassessed observation')
        require(isinstance(record.get('assessment_reason'), str) and record['assessment_reason'].strip(),
                f'{key}: missing manual assessment reason')
        response = record.get('actual')
        require(isinstance(response, dict) and isinstance(response.get('response'), str)
                and response['response'].strip(), f'{key}: missing actual response')
        actual[key] = response
    require(seen == REQUIRED, 'missing response observations')
    for key in ['T01', 'T03', 'F02', 'F03', 'F04', 'F06']:
        require(actual[key].get('planned_edits') == [], f'{key}: forbidden planned edit')
    require(actual['T01'].get('selected_base') == 'origin/main'
            and actual['T01'].get('finding_count') == 1, 'T01: target omission')
    require(actual['T03'].get('finding_count') == 0, 'T03: stale finding')
    fix = actual['F01']
    require(fix.get('verification') == 'action-only three-state'
            and fix.get('verdict') == 'CONFIRMED'
            and fix.get('candidate_search_expanded') is False
            and fix.get('planned_edits') == ['return inner();']
            and bool(fix.get('planned_checks')), 'F01: unsafe or missing fix confirmation')
    low = actual['F02']
    require(low.get('verification') == 'none' and low.get('candidate_search_expanded') is False,
            'F02: widened review')
    require(re.fullmatch(r'[^\n]+:\d+ — [^\n]+', low['response']) is not None,
            'F02: invalid exact low output')
    for key in ['F03', 'F04']:
        require(actual[key].get('checkout_switch') is False and actual[key].get('skip_reason'),
                f'{key}: mismatch must skip checkout')
    require(actual['F05'].get('overlap_variant_edits') == []
            and actual['F05'].get('safe_variant_edits') == ['return inner();']
            and actual['F05'].get('preserved_paths') == ['README.md'], 'F05: unsafe overlap')
    require(actual['F06'].get('verdict') == 'PLAUSIBLE'
            and actual['F06'].get('confirmation_needed'), 'F06: missing uncertainty')
    route = actual['R01']
    require(route.get('medium_angles') == 8 and route.get('xhigh_angles') == 10
            and route.get('full_diff_access') is True, 'R01: routing/coverage drift')
    require(actual['R02'].get('verdicts') == ['excluded', 'PLAUSIBLE', 'REFUTED']
            and actual['R02'].get('confirmation_needed'), 'R02: unsupported certainty')
    report = actual['R03']
    canonical(report.get('canonical'))
    require(len(report['canonical']) == 1, 'R03: missing plausible finding')
    require('Unconfirmed:' in report['canonical'][0]['failure_scenario']
            and 'idempotency contract' in report['canonical'][0]['failure_scenario'],
            'R03: missing uncertainty text; manual semantic assessment also required')
    require(set(report.get('custom', {})) == set(report.get('custom_requested_keys', []))
            and report['custom'].get('verdict') == 'PLAUSIBLE'
            and report['custom'].get('confirmation_needed'), 'R03: custom schema drift')
    require(report.get('typed_calls') == 1 and report.get('typed_prose_duplicate') is False,
            'R03: duplicate typed report')
    typed = report.get('typed', {})
    require(set(typed) == {'level', 'findings'} and typed['level'] == 'high', 'R03: typed wrapper')
    require(len(typed['findings']) == 1 and typed['findings'][0].get('verdict') == 'PLAUSIBLE'
            and len(typed['findings'][0]['short_summary']) <= 60, 'R03: typed finding')
    require('idempotency contract' in typed['findings'][0]['failure_scenario']
            and 'Confirmation needed:' in report.get('human', ''), 'R03: lost confirmation')
    require(actual['R04'].get('final_ids') == list(range(4, 12))
            and actual['R04'].get('omitted_with_12') == 1
            and actual['R04'].get('new_location_kept') is True, 'R04: cap/backfill drift')
    actions = actual['R05']
    require(actions.get('all_actions') == ORDER, 'R05: action order')
    require(actions.get('review_only_actions') == ['find_verify', 'prepare', 'final']
            and actions.get('fix_only_actions') == ORDER[:4] + ['final'], 'R05: implicit action')
    require(actions.get('push') is False and actions.get('commit') is False, 'R05: unauthorized Git action')
    canonical(actions.get('publisher_failure_output'))
    return len(seen)


def load_specs():
    return [case for path in sorted((ROOT / 'tests/fixtures').glob('*-cases.json'))
            for case in json.loads(path.read_text())]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observations', type=Path,
                        default=ROOT / 'tests/fixtures/observed-responses.json')
    args = parser.parse_args()
    try:
        count = validate(load_specs(), json.loads(args.observations.read_text()))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'FAIL: {error}\n')
    print(f'PASS: {count} recorded same-context dry-run contracts. '
          'Not independent model compliance or performance evidence.')


if __name__ == '__main__':
    main()
