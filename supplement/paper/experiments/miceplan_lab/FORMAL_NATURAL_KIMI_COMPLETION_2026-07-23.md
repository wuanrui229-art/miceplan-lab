# Kimi Formal Track N Completion Record

Date completed: 2026-07-23  
Run ID: `formal-natural-kimi-v1-2`  
Status: **complete**

> Historical phase note (2026-07-24): Kimi Track S subsequently completed. Its independent
> completion and analysis record is
> `FORMAL_SEEDED_KIMI_COMPLETION_2026-07-24.md`. The phase-boundary wording below records the
> state when Track N closed.

## Integrity and completion

- scheduled jobs: 216/216
- policy outcomes: 1,080/1,080
- semantic model calls: 434
- frozen minimum calls: 432
- frozen maximum calls: 1,728
- gate events: 650
- infrastructure-error records: 1
- append-only hash-chain verification: PASS
- benchmark and protocol manifest verification: PASS

The single infrastructure-error record is the 2026-07-22 quota/balance HTTP 429 that stopped
the first execution. After author recharge, the run resumed from the existing journal and
completed without another infrastructure-error record. The two calls above the frozen minimum
were bounded natural-repair calls; the run remained far below its maximum.

## Usage and operational cost

- prompt tokens: 816,420
- cached input tokens: 253,213
- completion tokens: 1,039,465
- total provider-reported tokens: 1,855,885
- median call latency: 8.29 s
- p95 call latency: 36.27 s
- estimated provider cost: USD 9.48 before tax

The estimate applies the frozen 2026-07-21 Kimi K2.7 Code HighSpeed prices to the recorded
cache-hit input, cache-miss input, and completion-token counts. It is not a billing receipt.

## Descriptive policy summary

| Policy | n | Invalid-operation exposure | Safe task success | Block | Defer | Mean semantic calls |
|---|---:|---:|---:|---:|---:|---:|
| LLM-only | 216 | 1.85% | 43.52% | 0.00% | 33.33% | 1.000 |
| Constraint in prompt | 216 | 0.46% | 54.17% | 0.00% | 26.85% | 1.000 |
| Validate and Block | 216 | 0.00% | 43.52% | 0.46% | 38.43% | 1.000 |
| Validate and Blind Retry | 216 | 0.00% | 43.98% | 0.00% | 38.43% | 1.005 |
| Validate and Rule-Feedback Repair | 216 | 0.00% | 43.98% | 0.00% | 38.43% | 1.005 |

These are unadjusted descriptive rates. They do not replace the prespecified paired,
cluster-bootstrap, rule-cardinality, intent-fidelity, false-block, over-deferral, and cost
analysis. In particular, Track N contains very few natural geometric repair opportunities.
The equality of the two natural-repair summaries is not evidence that feedback is generally
useless; the separately frozen Track S is the conditional-recovery experiment designed to
answer that question.

## Phase boundary

Kimi Track S has not been started by this completion record. Starting it requires its own
provider-balance check and explicit author authorization. DeepSeek Track N and Track S also
remain unstarted.
