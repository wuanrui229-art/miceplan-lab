# GPT-5.6 Sol Formal Held-Out Natural-Incidence Interpretation

Date: 2026-09-02  
Run: `formal-natural-openai-v1-2-extension`  
Evidence status: completed formal held-out Track N extension; not yet incorporated into the manuscript

## 1. Completion, integrity, and cost

- The frozen schedule completed all 216 jobs: all 144 held-out bilingual requests were run at replicate 1, and the 36 bilingual requests belonging to the preregistered 18-task repeat subset were additionally run at replicates 2 and 3 (144 + 36 × 2).
- The append-only journals contain 432 unique model calls, 648 gate events, and 1,080 policy outcomes (216 × 5 policies).
- All 432 successful model responses were schema-valid, ended with provider finish reason `stop`, and had no provider refusal, length truncation, or recorded call error.
- Fifteen successful calls required one bounded infrastructure retry. One additional call failed after three connection resets, produced no outcome, and was safely resumed from the journal without resampling completed work.
- Protocol, dataset, and OpenAI-extension hash audits passed. A targeted secret scan found no API key or bearer credential in the run or analysis artifacts.
- Unique usage was 763,028 prompt tokens, including 241,323 cache-hit tokens and 520,409 cache-write tokens, plus 51,887 completion tokens.
- Cost under the frozen official GPT-5.6 Sol price record was USD 3.7414982. At the planning conversion of CNY 6.8 per USD, this is approximately CNY 25.44, before any tax or account-specific adjustment.

## 2. Primary OpenAI Track N results

All rates use the 216 paired jobs as the denominator unless otherwise stated.

| Policy | RIOER | Unsafe exposure | Safe-task success | Safe resolution | Defer | Over-defer |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LLM only | 1/216 (0.46%) | 7/216 (3.24%) | 66/216 (30.56%) | 105/216 (48.61%) | 143/216 (66.20%) | 104/216 (48.15%) |
| Constraint in prompt | 0/216 (0.00%) | 2/216 (0.93%) | 78/216 (36.11%) | 118/216 (54.63%) | 136/216 (62.96%) | 96/216 (44.44%) |
| Validate and block | 0/216 (0.00%) | 4/216 (1.85%) | 66/216 (30.56%) | 105/216 (48.61%) | 146/216 (67.59%) | 107/216 (49.54%) |
| Validate and repair | 0/216 (0.00%) | 4/216 (1.85%) | 66/216 (30.56%) | 105/216 (48.61%) | 146/216 (67.59%) | 107/216 (49.54%) |
| Validate and blind retry | 0/216 (0.00%) | 4/216 (1.85%) | 66/216 (30.56%) | 105/216 (48.61%) | 146/216 (67.59%) | 107/216 (49.54%) |

The constraint prompt improved safe-task success by 5.56 percentage points (cluster-bootstrap 95% CI: +1.42 to +10.29) and safe resolution by 6.02 points (95% CI: +1.89 to +10.71) relative to LLM only. It reduced unsafe exposure by 2.31 points (cluster-bootstrap 95% CI: -4.33 to -0.49), although the paired exact McNemar sensitivity test was p = 0.0625. This should be described as benchmark evidence, not a universal safety guarantee.

The deterministic gate eliminated the single rule-invalid exposure, but it did not improve safe-task success or safe resolution for this model. Its observed effect was containment rather than repair.

## 3. Deferral mechanism decomposition

The held-out set contains 176 feasible jobs and 40 genuine-defer jobs.

- LLM only correctly deferred on 39/40 genuine-defer jobs (97.5%) but also deferred on 104/176 feasible jobs (59.09%).
- The constraint prompt correctly deferred on 40/40 genuine-defer jobs (100%) and reduced feasible-job deferral to 96/176 (54.55%).
- Validation correctly deferred on 39/40 genuine-defer jobs and deferred on 106/176 feasible jobs (60.23%). One additional genuine-defer case was contained for a validator precondition reason that did not match the offline correct-defer criterion.

The 216 base-generation gate decisions were:

| Gate result | Count | Mechanism |
| --- | ---: | --- |
| PASS | 70 | Executable candidate reached geometry validation and passed |
| UNKNOWN | 143 | Model explicitly requested clarification |
| UNKNOWN | 3 | Validator precondition lacked scale/unit, aisle, or placement evidence |
| FAIL | 0 | No candidate entered a deterministic repair loop |

One base candidate was an offline geometric FAIL (overlap), but its frozen online gate stopped earlier at `UNKNOWN` because scale/unit evidence was masked. Therefore no rule-feedback or blind-retry call was eligible. This explains why Validate-and-Repair, Validate-and-Blind-Retry, and Validate-and-Block are identical in this OpenAI natural-incidence run: the bottleneck is precondition uncertainty and model self-deferral, not failure of a repair attempt.

The 4 unsafe exposures that remain after validation are geometry-PASS but intent-incorrect candidates. This is direct evidence that RIOER is a machine-confirmed containment proxy and cannot represent downstream semantic correctness, human review burden, task harm, or operational safety.

### Feasible-job deferral subgroups

| Subgroup | LLM only | Constraint prompt |
| --- | ---: | ---: |
| English | 48/88 (54.55%) | 44/88 (50.00%) |
| Chinese | 56/88 (63.64%) | 52/88 (59.09%) |
| C1 | 26/50 (52.00%) | 22/50 (44.00%) |
| C2 | 28/60 (46.67%) | 25/60 (41.67%) |
| C3 | 50/66 (75.76%) | 49/66 (74.24%) |
| Add booth | 25/28 (89.29%) | 15/28 (53.57%) |
| Move booth | 30/30 (100.00%) | 30/30 (100.00%) |
| Remove booth | 0/30 (0.00%) | 0/30 (0.00%) |
| Reserve aisle | 29/30 (96.67%) | 30/30 (100.00%) |
| Resize booth | 12/30 (40.00%) | 12/30 (40.00%) |
| Split booth | 8/28 (28.57%) | 9/28 (32.14%) |

These subgroup estimates are descriptive and correlated within the 72 semantic-task clusters. The dominant pattern is operation-specific: move and reserve-aisle requests are almost always deferred, while remove-booth requests are never deferred. The constraint prompt mainly helps add-booth cases and does not solve C3, move, or reserve-aisle deferral.

## 4. Three-model interpretation for the reviewer

The change in over-defer rate caused by Validate-and-Block relative to LLM only is strongly model-specific:

| Model | Validation-induced change in over-defer |
| --- | ---: |
| Kimi | +5.09 percentage points |
| DeepSeek | +68.52 percentage points |
| OpenAI GPT-5.6 Sol | +1.39 percentage points |

The OpenAI-minus-DeepSeek interaction is -67.13 points (semantic-task cluster-bootstrap 95% CI: -77.73 to -56.14). The OpenAI-minus-Kimi interaction is -3.70 points (95% CI: -7.07 to -0.89). Thus the previously striking DeepSeek increase should not be presented as an invariant property of deterministic validation. It is a model-by-policy interaction driven by where each model's candidates fall in the PASS/FAIL/UNKNOWN decision pipeline.

Constraint prompting improved safe-task success in all three models: Kimi +10.65 points, DeepSeek +9.26 points, and OpenAI +5.56 points. The pairwise interaction intervals include zero, so the present benchmark does not establish that these gains differ reliably by model.

Natural-incidence repair-versus-blind-retry differences are essentially zero for Kimi and OpenAI and only one job for DeepSeek. Track N therefore has too few eligible deterministic failures to estimate recovery mechanisms well. The separately frozen seeded Track S is the appropriate conditional estimand for rule-feedback versus blind retry and must not be pooled with Track N.

## 5. Claim boundary and next decision

This extension broadens model coverage from two to three model families and provides a model-specific explanation of deferral. It remains a synthetic benchmark with 72 semantic-task clusters, one full replicate plus two additional replicates for a preregistered 18-task repeat subset, machine adjudication, and no downstream human-review or operational-harm measurement.

No manuscript text has been changed. The OpenAI seeded Track S has since completed all 210 frozen jobs; its interpretation is recorded separately before any response-letter drafting or DOCX revision.
