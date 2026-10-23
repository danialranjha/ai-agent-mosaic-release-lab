import unittest
from itertools import product
import experiment as lab


class ReleaseTests(unittest.TestCase):
    def row(self, name, mode):
        case = next(c for c in lab.fixtures() if c['name'] == name)
        return lab.run_case(case, mode)

    def test_actual_split_bytes(self):
        for mode in ('source_labels', 'answer_closure'):
            row = self.row('split', mode)
            self.assertEqual([s['emitted_text'] for s in row['steps']],
                             ['Project Lumen uses supplier Cedar.', 'Supplier Cedar uses depot Finch.'])
            self.assertEqual(row['final_forbidden_inferable'], ['C'])
        row = self.row('split', 'transcript_closure')
        self.assertEqual([s['emitted_text'] for s in row['steps']],
                         ['Project Lumen uses supplier Cedar.', 'This answer is withheld.'])
        self.assertEqual(row['steps'][1]['state_after'], ['A'])
        self.assertEqual(row['final_forbidden_inferable'], [])

    def test_reverse_and_hold_does_not_poison_state(self):
        row = self.row('reverse', 'transcript_closure')
        self.assertEqual([s['decision'] for s in row['steps']], ['release', 'hold'])
        session = lab.Session('transcript_closure')
        session.answer(['A'])
        session.answer(['B'])
        answer = session.answer(['U'])
        self.assertEqual(answer['state_after'], ['A', 'U'])
        self.assertEqual(answer['emitted_text'], 'The meeting starts at noon.')

    def test_direct_and_refusal_content(self):
        for name in ('direct_composite', 'refusal_with_composite', 'combined_answer'):
            self.assertEqual(self.row(name, 'source_labels')['final_forbidden_inferable'], ['C'])
            for mode in ('answer_closure', 'transcript_closure'):
                row = self.row(name, mode)
                self.assertEqual(row['steps'][0]['emitted_text'], 'This answer is withheld.')
                self.assertEqual(row['final_forbidden_inferable'], [])

    def test_benign_and_mixed_labels(self):
        for name in ('harmless', 'duplicate', 'harmless_mixed_labels'):
            for mode in lab.MODES:
                row = self.row(name, mode)
                self.assertEqual([s['decision'] for s in row['steps']], ['release', 'release'])
                self.assertEqual(row['final_forbidden_inferable'], [])

    def test_chain_fixed_point_and_order(self):
        self.assertEqual(lab.closure({'A', 'B', 'D'}, tuple(reversed(lab.RULES))), {'A', 'B', 'C', 'D', 'E'})
        for mode in ('source_labels', 'answer_closure'):
            self.assertEqual(self.row('chain', mode)['final_forbidden_inferable'], ['E'])
        row = self.row('chain', 'transcript_closure')
        self.assertEqual([s['decision'] for s in row['steps']], ['release', 'release', 'hold'])
        self.assertEqual(row['final_forbidden_inferable'], [])

    def test_broken_assumptions_are_visible(self):
        for name in ('missing_rule', 'unrecorded_prior', 'lost_session_state'):
            row = self.row(name, 'transcript_closure')
            self.assertEqual(row['final_forbidden_inferable'], ['C'])
            self.assertTrue(all(s['decision'] == 'release' for s in row['steps']))

    def test_session_isolation(self):
        one, two = lab.Session('transcript_closure'), lab.Session('transcript_closure')
        one.answer(['A'])
        self.assertEqual(two.answer(['B'])['decision'], 'release')
        self.assertEqual(one.answer(['B'])['decision'], 'hold')

    def test_source_permissions_and_invalid_inputs(self):
        for mode in lab.MODES:
            self.assertEqual(self.row('restricted_source', mode)['steps'][0]['emitted_text'], lab.HOLD)
        for facts, labels in [(['UNKNOWN'], ['Internal']), (['A'], []), (['A'], ['Unknown'])]:
            with self.assertRaises(ValueError):
                lab.Session('transcript_closure').answer(facts, labels)

    def test_exhaustive_short_schedules_independent_boolean_oracle(self):
        # 40 schedules (length 0..3) x three methods = 120 comparisons.
        # Predicate implemented here without production closure or reader oracle.
        for length in range(4):
            for seq in product('ABD', repeat=length):
                for mode in lab.MODES:
                    with self.subTest(seq=seq, mode=mode):
                        session = lab.Session(mode)
                        observed = set()
                        for fact in seq:
                            forbidden = mode == 'transcript_closure' and (
                                (fact == 'A' and 'B' in observed) or
                                (fact == 'B' and 'A' in observed))
                            row = session.answer([fact])
                            self.assertEqual(row['decision'], 'hold' if forbidden else 'release')
                            expected_text = lab.HOLD if forbidden else lab.TEXT[fact]
                            self.assertEqual(bytes.fromhex(row['emitted_utf8_hex']).decode(), expected_text)
                            if not forbidden:
                                observed.add(fact)
                        self.assertEqual(session.released, observed)

    def test_observer_reads_bytes_and_ignores_decision_claims(self):
        self.assertEqual(lab.read_emitted('This answer is withheld.'), set())
        self.assertEqual(lab.read_emitted('I cannot discuss this conclusion: Project Lumen uses depot Finch.'), {'C'})
        self.assertEqual(lab.reader_consequences({'A', 'B', 'D'}), {'A', 'B', 'C', 'D', 'E'})

    def test_repeatability_and_all_rows(self):
        first, second = lab.run(), lab.run()
        self.assertEqual(first, second)
        self.assertEqual(len(first['rows']), 39)
        for row in first['rows']:
            for step in row['steps']:
                self.assertEqual(bytes.fromhex(step['emitted_utf8_hex']).decode(), step['emitted_text'])
                if step['decision'] == 'hold':
                    self.assertEqual(step['observed_facts'], [])
                    self.assertEqual(step['state_after'], step['state_before'])


if __name__ == '__main__':
    unittest.main()
