# Cross-Model Formal Track N Result

Date: 2026-07-24  
Models: Kimi K2.7 Code HighSpeed and DeepSeek V4 Pro  
Status: **both formal Track N runs complete**

The two models used the same 216 frozen job keys, requests, scenes, policy definitions,
replicate IDs, independent oracle, and semantic-task clusters. Cross-model intervals use
10,000 semantic-task cluster-bootstrap samples. The interaction direction is:

`(DeepSeek policy effect) - (Kimi policy effect)`.

## Deterministic gate

| Effect: Validate and Block minus LLM-only | Kimi | DeepSeek | Cross-model difference | 95% cluster-bootstrap CI |
|---|---:|---:|---:|---:|
| rule-invalid exposure | -1.85 pp | -4.17 pp | -2.31 pp | [-5.09, +0.44] pp |
| unsafe exposure | -5.56 pp | -68.52 pp | -62.96 pp | [-73.31, -52.31] pp |
| safe task success | 0.00 pp | 0.00 pp | 0.00 pp | [0.00, 0.00] pp |
| over-defer | +5.09 pp | +68.52 pp | +63.43 pp | [+52.88, +73.98] pp |

The gate eliminated observed geometric-rule exposure in both model families without
reducing safe task success. However, it acted mainly as a rejection/defer mechanism for
DeepSeek: the much larger exposure reduction was accompanied by a correspondingly large
over-deferral increase. Containment replicated; workflow utility did not.

## Constraint prompting

| Effect: Constraint in Prompt minus LLM-only | Kimi | DeepSeek | Cross-model difference | 95% cluster-bootstrap CI |
|---|---:|---:|---:|---:|
| rule-invalid exposure | -1.39 pp | +6.48 pp | +7.87 pp | [+3.06, +13.14] pp |
| unsafe exposure | -4.17 pp | -10.19 pp | -6.02 pp | [-14.90, +2.42] pp |
| safe task success | +10.65 pp | +9.26 pp | -1.39 pp | [-8.33, +5.36] pp |
| safe resolution | +12.04 pp | +10.19 pp | -1.85 pp | [-9.31, +5.39] pp |

Constraint prompting improved task success for both models, but its geometric-safety effect
reversed direction. In DeepSeek it increased geometric-rule exposure despite improving
broader task outcomes. This interaction argues against treating prompt constraints as a
model-independent replacement for runtime validation.

## Natural rule feedback versus blind retry

Rule feedback and blind retry were indistinguishable on Kimi's very small natural repair
opportunity. DeepSeek rule feedback produced one additional safe task over blind retry:
+0.46 percentage points over all 216 jobs. The cross-model difference was +0.46 points with
a 95% cluster-bootstrap interval of [0.00, +1.44] points. Natural geometric failure
denominators were only 4 for Kimi and 9 for DeepSeek, so no feedback-specific generalization
is made from Track N.

## Defensible cross-model conclusion

> Deterministic validation provided model-robust containment of encoded geometric
> violations, but the operational price of containment was strongly model dependent. For a
> model with many unsupported or semantically wrong candidates, the gate prevented exposure
> primarily by converting outputs into deferrals rather than by increasing successful task
> completion. Prompt-only constraints improved task success across models but did not provide
> model-stable geometric safety.

This result concerns synthetic held-out tasks and machine-measured outcomes. It does not
measure human review effort or professional CAD productivity.
