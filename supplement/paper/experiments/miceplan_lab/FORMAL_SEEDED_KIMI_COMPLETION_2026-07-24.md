# Kimi Formal Track S Completion Record

Date completed: 2026-07-24  
Run ID: `formal-seeded-kimi-v1-2`  
Status: **complete**

## Integrity and completion

- scheduled paired jobs: 210/210
- policy outcomes: 630/630
- unique semantic model calls: 428
- frozen minimum calls: 420
- frozen maximum calls: 1,260
- deterministic-gate events: 1,058
- infrastructure-error records: 3
- schema-valid successful calls: 428/428
- length-truncated successful calls: 0/428
- append-only hash-chain verification: PASS
- benchmark and protocol manifest verification: PASS
- frozen seed-file hash and schedule-coverage verification: PASS

The three infrastructure-error records are operational audit records, not model outcomes:
two record the same quota-exhaustion stop and immediate retry on 2026-07-23; the third records
the network-sandbox DNS failure on 2026-07-23. The run resumed from its append-only journal
after recharge and network authorization. No completed job was rerun.

The run crossed midnight before its final resume. A strict external resume shim aligned the
newly generated `access_date` to the original 2026-07-23 manifest only after verifying that
every other manifest field was identical. Model, endpoint, task IDs, seeds, prompts, schema,
decoding, schedule, and source hashes were unchanged.

## Usage and operational cost

- prompt tokens: 846,131
- cached input tokens: 221,002
- completion tokens: 1,642,828
- total provider-reported tokens: 2,488,959
- estimated provider cost: USD 14.4143 before tax

The estimate applies the frozen 2026-07-21 Kimi K2.7 Code HighSpeed prices to recorded
cache-hit input, cache-miss input, and completion tokens. It is not a billing receipt.

## Primary paired result

Effect direction below is **Rule-Feedback Repair minus matched Blind Retry**. Confidence
intervals use 10,000 semantic-task cluster-bootstrap samples and the frozen schedule seed
20260723. Chinese/English variants and repeated measurements are therefore not treated as
independent tasks.

| Outcome | Rule feedback | Blind retry | Paired difference | 95% cluster-bootstrap CI | Exact McNemar p |
|---|---:|---:|---:|---:|---:|
| Recovery@1 | 168/210 (80.0%) | 174/210 (82.9%) | -2.86 pp | [-8.33, +2.80] pp | 0.451 |
| Recovery@3 | 171/210 (81.4%) | 177/210 (84.3%) | -2.86 pp | [-8.16, +2.48] pp | 0.418 |

For Recovery@3, both policies succeeded in 155 pairs, only rule feedback succeeded in 16,
only blind retry succeeded in 22, and neither succeeded in 17. The interval includes both a
modest disadvantage and a small advantage. This run therefore provides **no evidence that
the specific rule message improved recovery beyond another matched sample**. The point
estimate favors blind retry, but the data do not establish a reliable negative effect.

## Containment, recovery, and semantic regressions

Every standardized initial candidate independently failed exactly its declared geometric
rule set while retaining the original intent signature.

| Policy | n | Safe task success | Geometrically invalid exposure | Other unsafe exposure | Block | Defer |
|---|---:|---:|---:|---:|---:|---:|
| Validate and Block | 210 | 0 (0.0%) | 0 | 0 | 210 | 0 |
| Rule-Feedback Repair | 210 | 171 (81.4%) | 0 | 37 | 0 | 2 |
| Blind Retry | 210 | 177 (84.3%) | 0 | 33 | 0 | 0 |

The deterministic gate contained all final geometric violations in all three policies.
Blocking achieved containment by refusing every injected failure and consequently completed
none of the requested edits. Both bounded-recovery policies restored most tasks, but their
remaining exposed failures were geometrically valid edits that did not preserve the
independent task-intent signature. Thus, a geometry gate can stop the rules it implements
without guaranteeing semantic correctness.

## Fault-cardinality result

| Injected fault cardinality | n | Rule feedback Recovery@3 | Blind retry Recovery@3 | Paired difference | 95% cluster-bootstrap CI |
|---|---:|---:|---:|---:|---:|
| One rule | 120 | 89/120 (74.2%) | 92/120 (76.7%) | -2.50 pp | [-11.03, +6.73] pp |
| Two rules | 90 | 82/90 (91.1%) | 85/90 (94.4%) | -3.33 pp | [-8.11, 0.00] pp |

The pre-specified interaction, two-rule minus one-rule feedback effect, was -0.83 percentage
points with a 95% cluster-bootstrap interval of [-11.26, +8.31] points. There is no evidence
in this run that fault cardinality changed the relative value of rule feedback. The higher
absolute recovery of two-rule cases is a benchmark-stratum observation, not evidence that
two-rule faults are generally easier.

## Paired overhead

| Measure | Mean rule-minus-blind difference per job | 95% cluster-bootstrap CI |
|---|---:|---:|
| model calls | 0.000 | [-0.019, +0.019] |
| latency | +0.104 s | [-3.114, +3.138] s |
| provider-reported tokens | +304.5 | [-207.6, +817.6] |
| estimated API cost | +USD 0.00142 | [-USD 0.00261, +USD 0.00536] |

Rule feedback and blind retry each averaged 1.019 model calls per paired job. Their measured
cost and latency differences were small and uncertain. A secondary signed-rank sensitivity
check suggested a token-distribution difference before correction, but the pre-specified
cluster-bootstrap interval for the mean crossed zero; no standalone efficiency claim is
made from that secondary result.

## Analysis implementation note

The frozen analysis module initially stopped because its lookup loaded
`fault_seeds_v1_2.jsonl` but not the simultaneously frozen
`fault_seeds_composite_v1_2.jsonl`. A post-run read-only compatibility wrapper verified both
files against the original run-manifest hashes, rejected duplicate IDs, required exact
coverage of the frozen scheduled seed IDs, and then invoked the unchanged pre-specified
metric functions. Raw calls, gate events, outcomes, and the run manifest were not modified.
The additional cluster-bootstrap script is deterministic; two executions produced the same
SHA-256 result file.

## Interpretation boundary

This is a formal held-out conditional-recovery experiment on transparent,
intent-preserving injected failures. It does not estimate how often Kimi naturally produces
these failures; that is the role of Track N. It evaluates one model, one rule-feedback
encoding, synthetic two-dimensional scenes, and an internally quality-controlled benchmark.
It is not practitioner validation, a human-effort study, or evidence of production CAD
integration.

The defensible Kimi-only conclusion is:

> Deterministic validation reliably contained the encoded geometric violations, but its
> rule-specific feedback did not improve recovery over matched blind resampling under the
> evaluated conditions. Most repair failures arose from semantic intent regressions rather
> than residual geometric violations.

DeepSeek Track N and Track S remain separate unexecuted robustness phases and require their
own explicit authorization.
