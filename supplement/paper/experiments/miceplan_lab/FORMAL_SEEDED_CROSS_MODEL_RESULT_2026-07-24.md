# Cross-Model Track S Result

Date: 2026-07-24  
Models: Kimi K2.7 and DeepSeek  
Paired cases per model: 210  
Unique semantic-task clusters: 36  

## Result

The same frozen seeded-failure schedule was evaluated with Kimi and DeepSeek.
The primary comparison was safe recovery under deterministic rule feedback
minus safe recovery under blind retry.

| Model | Rule feedback by attempt 3 | Blind retry by attempt 3 | Paired difference |
|---|---:|---:|---:|
| Kimi | 171/210 (81.43%) | 177/210 (84.29%) | −2.86 pp |
| DeepSeek | 139/210 (66.19%) | 136/210 (64.76%) | +1.43 pp |

The cross-model interaction was +4.29 percentage points in the direction
`(DeepSeek rule-minus-blind) − (Kimi rule-minus-blind)`. Its semantic-task
cluster-bootstrap 95% confidence interval was [−4.84, +13.30] percentage points.
The interval crosses zero, so the apparent difference in feedback benefit
between the two models is not established.

At attempt 1, the interaction was +0.48 percentage points with a 95% confidence
interval of [−10.80, +11.40] percentage points.

## Meaning for the paper

The two models do not support a model-independent claim that textual rule
feedback improves recovery over an equal-budget blind retry. Deterministic
validation remains useful as a safety gate, but feedback-driven repair should
be treated as a separate mechanism whose benefit depends on model behavior,
failure type, and repair design.

This result directly supports the paper's trade-off framing: a validation gate
can prevent invalid operations from reaching the workflow while still creating
blocking, retry, latency, and repair costs. The useful research question is not
whether validation is universally beneficial, but under which failure and model
conditions its prevented errors justify those costs.

## Reproducibility

- Statistics:
  `paper/data/miceplan_lab_v1_1/formal_cross_model_seeded_statistics.json`
- Analysis script:
  `paper/experiments/compare_formal_seeded_models.py`
- Bootstrap replicates: 10,000
- Bootstrap unit: semantic task
- Deterministic rerun SHA-256:
  `adfc730f3dea1a748b4359cf690b940f739d2c74e0d3f0e7a3d87ba396760e74`

