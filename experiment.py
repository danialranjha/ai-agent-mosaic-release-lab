"""Finite, structured-fact release assay. No model, retrieval or network."""
from dataclasses import dataclass, field
import json
from pathlib import Path

TEXT = {
    'A': 'Project Lumen uses supplier Cedar.',
    'B': 'Supplier Cedar uses depot Finch.',
    'C': 'Project Lumen uses depot Finch.',
    'D': 'Depot Finch is a prototype facility.',
    'E': 'Project Lumen uses a prototype facility.',
    'U': 'The meeting starts at noon.',
}
# Explicit invented relation semantics, not natural-language inference.
RULES = ((frozenset({'A', 'B'}), 'C'), (frozenset({'C', 'D'}), 'E'))
LEVEL = {'Public': 0, 'Internal': 1, 'Restricted': 2}
MODES = ('source_labels', 'answer_closure', 'transcript_closure')
HOLD = 'This answer is withheld.'


def closure(facts, rules=RULES):
    known = set(facts)
    while True:
        expanded = known | {conclusion for premises, conclusion in rules
                            if premises <= known}
        if expanded == known:
            return known
        known = expanded


def decision_facts(mode, released, proposed):
    return set(released) | set(proposed) if mode == 'transcript_closure' else set(proposed)


def render(facts, refusal=False):
    body = ' '.join(TEXT[f] for f in sorted(facts))
    return ('I cannot discuss this conclusion: ' if refusal else '') + body


def read_emitted(text):
    """Exact finite vocabulary decoder; not a general semantic detector."""
    return {fact for fact, sentence in TEXT.items() if sentence in text}


def reader_consequences(facts):
    """Separate hard-coded oracle, not the policy's rule engine/catalog."""
    known = set(facts)
    if 'A' in known and 'B' in known:
        known.add('C')
    if 'C' in known and 'D' in known:
        known.add('E')
    return known


@dataclass
class Session:
    mode: str
    forbidden: frozenset = frozenset({'C'})
    rules: tuple = RULES
    released: set = field(default_factory=set)

    def answer(self, proposed, sources=('Internal',), refusal=False):
        if self.mode not in MODES:
            raise ValueError('unknown policy')
        proposed = set(proposed)
        if not proposed <= TEXT.keys() or not sources:
            raise ValueError('unsupported facts or missing source labels')
        if any(label not in LEVEL for label in sources):
            raise ValueError('unknown source classification')
        # User clearance is Internal. This is source permission only.
        allowed = all(LEVEL[label] <= LEVEL['Internal'] for label in sources)
        reason = 'source_permission' if not allowed else 'allowed'
        if allowed and self.mode != 'source_labels':
            candidate = decision_facts(self.mode, self.released, proposed)
            if closure(candidate, self.rules) & self.forbidden:
                allowed, reason = False, 'known_forbidden_consequence'
        before = sorted(self.released)
        emitted = render(proposed, refusal) if allowed else HOLD
        if allowed:
            self.released.update(proposed)
        return {'proposed': sorted(proposed), 'sources': list(sources),
                'refusal_wording': refusal, 'decision': 'release' if allowed else 'hold',
                'reason': reason, 'state_before': before,
                'state_after': sorted(self.released), 'emitted_text': emitted,
                'emitted_utf8_hex': emitted.encode().hex()}


def fixtures():
    return [
        {'name': 'split', 'answers': [('A',), ('B',)]},
        {'name': 'reverse', 'answers': [('B',), ('A',)]},
        {'name': 'direct_composite', 'answers': [('C',)]},
        {'name': 'refusal_with_composite', 'answers': [('C',)], 'refusal': True},
        {'name': 'harmless', 'answers': [('A',), ('U',)]},
        {'name': 'duplicate', 'answers': [('A',), ('A',)]},
        {'name': 'combined_answer', 'answers': [('A', 'B')]},
        {'name': 'chain', 'answers': [('A',), ('B',), ('D',)], 'forbidden': ['E'],
         'rules': tuple(reversed(RULES))},
        {'name': 'missing_rule', 'answers': [('A',), ('B',)], 'rules': ()},
        {'name': 'unrecorded_prior', 'answers': [('B',)], 'reader_prior': ['A']},
        {'name': 'lost_session_state', 'answers': [('A',), ('B',)], 'reset_before': 1},
        {'name': 'harmless_mixed_labels', 'answers': [('A',), ('U',)],
         'sources': ('Internal', 'Public')},
        {'name': 'restricted_source', 'answers': [('U',)], 'sources': ('Restricted',)},
    ]


def run_case(case, mode):
    forbidden = frozenset(case.get('forbidden', ['C']))
    session = Session(mode, forbidden, case.get('rules', RULES))
    reader = set(case.get('reader_prior', []))
    steps = []
    for i, proposed in enumerate(case['answers']):
        reset = i == case.get('reset_before')
        if reset:
            session.released.clear()
        row = session.answer(proposed, case.get('sources', ('Internal',)), case.get('refusal', False))
        row['release_log_reset_before_step'] = reset
        # Observe actual emitted bytes. Do not use decision or proposed IDs as oracle.
        observed = read_emitted(bytes.fromhex(row['emitted_utf8_hex']).decode())
        reader.update(observed)
        row.update({'observed_facts': sorted(observed), 'reader_facts': sorted(reader),
                    'reader_consequences': sorted(reader_consequences(reader)),
                    'forbidden_inferable': sorted(reader_consequences(reader) & forbidden)})
        steps.append(row)
    return {'scenario': case['name'], 'method': mode, 'forbidden': sorted(forbidden),
            'reader_prior': case.get('reader_prior', []),
            'controller_rules': [{'premises': sorted(p), 'conclusion': c}
                                 for p, c in case.get('rules', RULES)],
            'steps': steps, 'final_forbidden_inferable': steps[-1]['forbidden_inferable']}


def run():
    return {'schema': 1, 'scope': 'invented structured facts; no model or real disclosure',
            'oracle': 'cumulative reader inferability, not paper final-answer disclosure',
            'fact_text': TEXT, 'rows': [run_case(c, m) for c in fixtures() for m in MODES]}


def evidence(result):
    lines = ['# Exact release evidence', '',
             '13 chosen schedules x 3 methods = 39 rows. No sampled population or model trials.',
             'The oracle decodes emitted bytes into a fixed vocabulary, then applies separately written A+B=>C and C+D=>E implications.',
             'This cumulative-inferability endpoint differs from the source paper\'s explicit final-answer composite endpoint.', '',
             '| Scenario | Method | Ordered decisions | Emitted facts by step | Final forbidden inference |',
             '|---|---|---|---|---|']
    for row in result['rows']:
        lines.append('| ' + ' | '.join([row['scenario'], row['method'],
                     ', '.join(s['decision'] for s in row['steps']),
                     ' / '.join(','.join(s['observed_facts']) or '(none)' for s in row['steps']),
                     ','.join(row['final_forbidden_inferable']) or '(none)']) + ' |')
    lines += ['', 'A: Lumen uses Cedar. B: Cedar uses Finch. C: Lumen uses Finch.',
              'All are invented. C is the forbidden conclusion in ordinary cases; E in chain.',
              'missing_rule, unrecorded_prior and lost_session_state intentionally break trusted assumptions.',
              'A hold sends a generic string and does not add the proposed facts to the release log.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    target = Path(__file__).parent / 'artifacts'
    target.mkdir(exist_ok=True)
    result = run()
    (target / 'run.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    (target / 'evidence.md').write_text(evidence(result))
    print('Wrote 39 scenario/method rows; zero model calls.')
