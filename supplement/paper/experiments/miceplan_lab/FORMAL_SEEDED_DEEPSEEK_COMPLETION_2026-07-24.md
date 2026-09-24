# DeepSeek Track S Formal Completion Record

Date: 2026-07-24  
Run ID: `formal-seeded-deepseek-v1-2`  
Track: formal seeded conditional recovery (Track S)  
Provider: DeepSeek Open Platform  

## Scope

This run used the frozen Track S schedule and compared three policies on the same
210 seeded-invalid layout-editing cases:

1. `SEEDED_VALIDATE_AND_BLOCK`
2. `SEEDED_VALIDATE_AND_REPAIR` (deterministic rule feedback)
3. `SEEDED_VALIDATE_AND_BLIND_RETRY` (retry without rule feedback)

Track S estimates conditional recovery after an intent-preserving invalid
candidate has been injected. It does not estimate how often a model naturally
creates such failures and must not be pooled with Track N.

## Completion and integrity

- Scheduled jobs: 210/210
- Recorded policy outcomes: 630/630
- Unique model calls: 580
- Gate events: 1,210
- Infrastructure errors: 0
- Schema-valid calls: 577/580
- Length truncations: 0
- Append-only hash chains: verified
- Record-key uniqueness: verified
- Frozen dataset and protocol manifests: verified
- Initial seeded candidates all failed the declared rule while preserving the
  intended edit signature: verified
- Rule-feedback payloads matched the recorded repair prompts: verified

The run started with a CNY 17.50 account balance and ended with CNY 14.34, for an
observed balance reduction of CNY 3.16. Token-accounting cost under the frozen
pricing snapshot was USD 0.458349321.

## Primary results

| Measure | Rule feedback | Blind retry | Paired difference (rule − blind) |
|---|---:|---:|---:|
| Recovery at attempt 1 | 108/210 (51.43%) | 113/210 (53.81%) | −2.38 pp |
| Recovery by attempt 3 | 139/210 (66.19%) | 136/210 (64.76%) | +1.43 pp |

For recovery by attempt 3, the semantic-task cluster-bootstrap 95% confidence
interval for the paired difference was [−7.35, +10.09] percentage points, and
the exact paired McNemar p-value was 0.8013. The data therefore do not establish
an overall recovery advantage for rule feedback over blind retry.

The paired outcome table at attempt 3 was:

- Both succeeded: 106
- Rule feedback only succeeded: 33
- Blind retry only succeeded: 30
- Neither succeeded: 41

The deterministic block policy exposed no invalid operation but recovered none
of the 210 seeded-invalid candidates, because it intentionally performs no
repair.

## Overhead of rule feedback

Compared with blind retry, rule feedback had:

- Mean model-call difference: 0.00 calls per case
- Mean latency difference: +817.66 ms per case; cluster-bootstrap 95% CI
  [+300.67, +1,382.25] ms
- Mean token difference: +277.75 tokens per case; cluster-bootstrap 95% CI
  [−74.54, +669.30]
- Mean estimated cost difference: +USD 0.0000999 per case; cluster-bootstrap
  95% CI [−USD 0.0000146, +USD 0.0002288]

Rule feedback removed the only final rule-invalid exposure observed under blind
retry (0/210 versus 1/210), but it did not produce a statistically supported
increase in safe task success and it added measurable latency.

## Interpretation boundary

The supported claim is narrow: in this controlled seeded-failure benchmark,
deterministic validation prevented invalid outputs from passing unchecked, but
generic textual rule feedback did not reliably outperform a retry with the same
attempt budget. This run measures machine-side safety, recovery, latency, token,
and cost proxies. It does not directly measure human review time or professional
layout quality.

## Artifacts

- Raw append-only run:
  `paper/data/miceplan_lab_v1_1/runs/formal-seeded-deepseek-v1-2/`
- Descriptive analysis:
  `seeded_analysis.json` and `seeded_analysis.md`
- Paired inferential statistics:
  `seeded_statistics.json`

