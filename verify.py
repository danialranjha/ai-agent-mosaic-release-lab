"""Run focused suite and two functional faults; record actual test outcomes."""
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import experiment
import test_experiment


def check():
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_experiment)
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=2).run(suite)
    return {'tests': result.testsRun, 'failures': len(result.failures),
            'errors': len(result.errors), 'skipped': len(result.skipped),
            'passed': result.wasSuccessful()}


def main():
    baseline = check()
    with patch.object(experiment, 'decision_facts', lambda mode, released, proposed: set(proposed)):
        forget = check()
    with patch.object(experiment, 'closure', lambda facts, rules=experiment.RULES: set(facts)):
        no_rules = check()
    results = {'baseline': baseline, 'faults': {'forget_history': forget, 'disable_rules': no_rules},
               'exhaustive_schedule_method_comparisons': 120,
               'scope': 'selected finite rules and structured vocabulary; no statistical or model efficacy claim'}
    target = Path(__file__).parent / 'artifacts'
    target.mkdir(exist_ok=True)
    (target / 'checks.json').write_text(json.dumps(results, indent=2, sort_keys=True) + '\n')
    print(json.dumps(results, indent=2))
    assert baseline['passed'] and baseline['skipped'] == 0
    assert all(r['failures'] > 0 and r['errors'] == 0 and r['skipped'] == 0 for r in (forget, no_rules))


if __name__ == '__main__':
    main()
