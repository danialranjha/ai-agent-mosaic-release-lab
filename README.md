# AI-agent mosaic release lab

Two individually permitted answers can jointly reveal a designated forbidden conclusion. This lab compares source permission, one-answer checks and accumulated-release checks in a **finite invented fact system**. No AI model, retrieval system, real confidential data or network runs. It is an independent policy assay, not a reproduction of a paper's agent results.

## Hypothesis and threat model

A permitted user asks successive questions. An answer producer supplies structured fact IDs, which the trusted renderer turns into fixed sentences. The producer may offer the forbidden conclusion, including inside refusal wording. This access is assumed; no model persuasion or system compromise is demonstrated.

The policy catalog, fact meaning, source classifications, user identity and release log are trusted. The user has Internal clearance. A and B come from individually permitted Internal sources:

- A: Project Lumen uses supplier Cedar.
- B: Supplier Cedar uses depot Finch.
- C: Project Lumen uses depot Finch. The explicitly specified rule A AND B implies C.

C is designated Restricted. All names and relationships are invented. This is an exact toy relational rule, not an assertion that arbitrary business relationships are transitive.

Hypothesis: source-label and isolated-answer checks can release A then B; checking known consequences of previous releases plus the next proposed answer holds the completing answer. We also test when this check fails.

## Setup and commands

Python 3.10+ and standard library only. No install, credentials, model, network, server or external files needed. From this repository:

```sh
python3 -m unittest -v
python3 experiment.py
python3 verify.py
```

The commands regenerate [run.json](artifacts/run.json), [exact evidence table](artifacts/evidence.md) and [test/fault counts](artifacts/checks.json). Fixtures are selected counterexamples, not a sample of agent attacks. All experiment writes stay in this repository's artifacts folder.

## Technical walkthrough

- **Source labels:** Check whether all supplied source classifications are within Internal clearance, then release the supplied answer.
- **Answer closure:** Also apply known implication rules to the current answer's facts, holding the whole answer if a forbidden conclusion follows.
- **Transcript closure:** Apply those rules to previously released facts plus the proposed answer, holding the whole answer if a forbidden conclusion follows.

Here, closure means repeatedly applying explicit rules until no new fact can be derived. Rules do not parse arbitrary language. In the main example, the forbidden C can be stated directly or inferred from A plus B.

Only released facts enter the trusted log. A hold emits exactly `This answer is withheld.` It does not publish a redacted version or add the proposed facts to the log. The output observer decodes actual UTF-8 bytes using the six known sentences, then applies separately written implication checks. It does not infer success from an allow/hold status. Every step records bytes, selected facts, log state and the reader's accumulated consequences.

The run produced 39 rows: 13 chosen schedules under all three methods. Eleven tests passed with no errors or skips, including 120 exhaustive short-schedule/method comparisons. Deliberately forgetting history caused 18 assertion failures; disabling implication rules caused 19, with no test errors. Subtest failures can exceed the eleven top-level test methods. The main observed contrast is:

| Method | First answer A | Second answer B | Reader can derive C |
|---|---|---|---|
| Source labels | Released | Released | Yes |
| Answer closure | Released | Released | Yes |
| Transcript closure | Released | Held | No, under the stated knowledge model |

Reverse order tests the same rule in the other direction. A direct C answer and a refusal explicitly stating C test the content rather than the refusal label. A harmless fact U and a duplicate A test retained usefulness. A harmless mixed-label source set still passes: merely having different source labels does not imply a forbidden composite. Conversely, A and B have the same source label and still imply C.

The chain case permits C but forbids E. An additional fact D and rule C AND D implies E require repeated inference. Reversing the rule order ensures the checker must reach a fixed point.

## Limits and failure cases

The missing-rule fixture removes the controller's knowledge of A+B=>C while the separate reader oracle retains that relationship. The unrecorded-prior fixture gives the reader A outside the release log. The lost-session-state fixture erases the controller's log between A and B. These deliberately break the assumptions and can let the transcript check release a completing fact.

This is **cumulative inferability**, not the source paper's final-answer disclosure metric. The paper requires an answer to clearly convey its designated composite and does not count constituent co-reporting alone. This lab asks the different engineering question of what the reader can derive from a series of exact structured releases.

The fact IDs and rule catalog are provided, not extracted from a model answer. The finite decoder is not a deployable semantic detector. Unknown relationships, paraphrases, incorrect metadata, undiscovered prior knowledge, colluding users, concurrency, persistent storage, and other channels are not solved. The hold itself may reveal information; that side channel is not measured. A benign individual answer may be withheld because it completes a forbidden inference, so utility costs are deliberate. No leakage rates, model performance or universal confidentiality guarantee follow.

For a structured service with an explicit sensitive-combination policy, carry the user's released facts into the next check and test the candidate union before releasing bytes. Keep the known-rule catalog and release state trustworthy, and test missing rules, prior knowledge and state loss separately rather than treating a per-answer permission check as an aggregation guarantee.

## Source and provenance

[Agent Mosaic](https://arxiv.org/html/2610.30418v1), sections 1 and 3.1, motivates the same-label aggregation question. Section4 supplies the endpoint distinction above. Its code/reproducibility assets are promised upon acceptance in the inspected version. Our three policies, original fixtures and cross-answer rule check are independent extensions, not measured defenses from that paper. We reproduce none of its percentages. [Source mapping](source.json).

Only original experiment code, tests, configuration, generated technical evidence and documentation are in this repository. MIT licensed. There are no automated workflows or deployments.
