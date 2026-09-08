"""Ensure the offline checker rejects unsafe or incompatible recorded outputs."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('review_scenarios', ROOT / 'scripts/check_review_scenarios.py')
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class ReviewScenarios(unittest.TestCase):
    def setUp(self):
        self.specs = CHECKER.load_specs()
        self.records = json.loads((ROOT / 'tests/fixtures/observed-responses.json').read_text())

    def test_recorded_contracts(self):
        self.assertEqual(CHECKER.validate(self.specs, self.records), 13)

    def test_unsafe_and_incompatible_outputs_rejected(self):
        mutations = [
            ('F01', 'verdict', 'PLAUSIBLE'),
            ('F01', 'candidate_search_expanded', True),
            ('F02', 'verification', 'three-state'),
            ('F02', 'response', 'Findings:\napi.js:1 — bad return'),
            ('F03', 'planned_edits', ['wrong checkout edit']),
            ('F04', 'checkout_switch', True),
            ('F05', 'overlap_variant_edits', ['overwrite user edit']),
            ('F06', 'planned_edits', ['uncertain fix']),
            ('R01', 'medium_angles', 10),
            ('R02', 'verdicts', ['PLAUSIBLE', 'PLAUSIBLE', 'REFUTED']),
            ('R03', 'typed_calls', 2),
            ('R04', 'final_ids', [4, 5, 6, 7, 8]),
            ('R05', 'push', True),
            ('T01', 'selected_base', 'origin/feature'),
            ('T03', 'finding_count', 1),
        ]
        for case, field, value in mutations:
            with self.subTest(case=case, field=field):
                records = copy.deepcopy(self.records)
                next(r for r in records if r['id'] == case)['actual'][field] = value
                with self.assertRaises(ValueError):
                    CHECKER.validate(self.specs, records)

    def test_canonical_extra_field_rejected(self):
        record = next(r for r in self.records if r['id'] == 'R03')
        record['actual']['canonical'][0]['verdict'] = 'PLAUSIBLE'
        with self.assertRaises(ValueError):
            CHECKER.validate(self.specs, self.records)

    def test_missing_or_stale_evidence_rejected(self):
        with self.assertRaises(ValueError):
            CHECKER.validate(self.specs, self.records[:-1])
        self.records[0]['prompt'] = 'different target'
        with self.assertRaises(ValueError):
            CHECKER.validate(self.specs, self.records)

    def test_failed_assessment_rejected(self):
        self.records[0]['assessment'] = 'fail'
        with self.assertRaises(ValueError):
            CHECKER.validate(self.specs, self.records)


if __name__ == '__main__':
    unittest.main()
