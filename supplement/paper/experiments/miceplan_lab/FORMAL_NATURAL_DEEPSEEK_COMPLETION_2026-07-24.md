# DeepSeek Formal Track N Completion Record

Date completed: 2026-07-24  
Run ID: `formal-natural-deepseek-v1-2`  
Status: **complete**

## Integrity and completion

- scheduled jobs: 216/216
- policy outcomes: 1,080/1,080
- successful provider responses recorded as semantic calls: 442
- frozen minimum calls: 432
- frozen maximum calls: 1,728
- deterministic-gate events: 658
- infrastructure-error records: 2
- schema-valid calls: 435/442 (98.42%)
- length-truncated calls: 0/442
- successful-call infrastructure retries: 11
- append-only hash-chain verification: PASS
- benchmark and protocol manifest verification: PASS

The first infrastructure stop followed three provider read timeouts. The second was an
incomplete chunked HTTP response. Both stopped before the affected job committed; the run
resumed from the append-only journal without rerunning completed jobs. The 11 successful-call
retries comprise eight read timeouts and three peer connection resets that recovered within
the bounded adapter retry policy.

Seven successful HTTP responses did not yield a schema-valid candidate: five contained
malformed tool-argument JSON and two returned a schema-incompatible value despite the
provider's strict-tool beta contract. These responses are retained as unusable model outputs,
not discarded as infrastructure failures.

## Usage and operational cost

- prompt tokens: 1,055,419
- cached input tokens: 686,080
- completion tokens: 205,535
- total provider-reported tokens: 1,260,954
- estimated provider cost: USD 0.3420 before tax

The estimate applies the frozen 2026-07-21 DeepSeek V4 Pro prices to recorded cache-hit
input, cache-miss input, and completion tokens. It is not a billing receipt. Per-policy costs
in the audit are conceptual because the shared base call is reused by multiple policies.

## Formal policy summary

| Policy | n | Rule-invalid exposure | Unsafe exposure | Safe task success | Safe resolution | Block | Defer | Over-defer |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LLM-only | 216 | 9 (4.17%) | 160 (74.07%) | 51 (23.61%) | 53 (24.54%) | 3 (1.39%) | 2 (0.93%) | 0 |
| Constraint in Prompt | 216 | 23 (10.65%) | 138 (63.89%) | 71 (32.87%) | 75 (34.72%) | 3 (1.39%) | 4 (1.85%) | 0 |
| Validate and Block | 216 | 0 | 12 (5.56%) | 51 (23.61%) | 53 (24.54%) | 3 (1.39%) | 150 (69.44%) | 148 (68.52%) |
| Validate and Blind Retry | 216 | 0 | 12 (5.56%) | 53 (24.54%) | 55 (25.46%) | 0 | 151 (69.91%) | 149 (68.98%) |
| Validate and Rule-Feedback Repair | 216 | 0 | 12 (5.56%) | 54 (25.00%) | 56 (25.93%) | 0 | 150 (69.44%) | 148 (68.52%) |

Unsafe exposure is broader than geometric invalidity: it also counts an exposed candidate
that is unsupported or does not preserve task intent. The gate removed all observed
rule-invalid exposures but could not turn DeepSeek's many unsupported or semantically wrong
base candidates into task completions. Instead, it converted most of them into deferrals.

## Primary containment comparison

Effect direction is **Validate and Block minus LLM-only**. Confidence intervals use 10,000
semantic-task cluster-bootstrap samples with the frozen schedule seed.

| Outcome | Validate and Block | LLM-only | Paired difference | 95% cluster-bootstrap CI | Exact McNemar p |
|---|---:|---:|---:|---:|---:|
| Rule-invalid exposure | 0/216 | 9/216 (4.17%) | -4.17 pp | [-7.65, -1.39] pp | 0.0039 |
| Unsafe exposure | 12/216 (5.56%) | 160/216 (74.07%) | -68.52 pp | [-79.17, -57.21] pp | < 1e-40 |
| Safe task success | 51/216 (23.61%) | 51/216 (23.61%) | 0.00 pp | [0.00, 0.00] pp | no discordance |
| Safe resolution | 53/216 (24.54%) | 53/216 (24.54%) | 0.00 pp | [0.00, 0.00] pp | no discordance |

No independently valid geometric operation was falsely blocked under the pre-specified
false-block definition. The containment gain is real, but the 68.52% over-deferral rate shows
that exposure reduction alone is not a sufficient usability or productivity claim.

## Constraint-prompt trade-off

Effect direction is **Constraint in Prompt minus LLM-only**.

| Outcome | Paired difference | 95% cluster-bootstrap CI | Exact McNemar p |
|---|---:|---:|---:|
| Rule-invalid exposure | +6.48 pp | [+2.40, +11.07] pp | 0.0013 |
| Unsafe exposure | -10.19 pp | [-16.00, -4.74] pp | 0.00020 |
| Safe task success | +9.26 pp | [+4.90, +13.89] pp | < 0.0001 |
| Safe resolution | +10.19 pp | [+5.66, +14.81] pp | < 0.0001 |

Explicit constraint prompting improved overall task success and reduced broad unsafe
exposure, but it also increased the narrower geometric-rule violation rate. This is a
measured trade-off, not evidence that prompting alone is a safe substitute for runtime
validation.

## Natural repair opportunity

Only 9/216 shared natural base candidates independently failed a geometric rule, so Track N
provides a small conditional-recovery denominator:

- Rule-Feedback Repair recovered 3/9 by attempt 3;
- Blind Retry recovered 2/9 by attempt 3;
- the all-task safe-task-success difference was +0.46 percentage points for rule feedback,
  with a 95% cluster-bootstrap interval of [0.00, +1.47] points and exact McNemar p = 1.0;
- Rule-Feedback Repair added a mean 0.0093 calls, 0.141 seconds, 43.7 tokens, and about
  USD 0.000020 per job relative to Blind Retry.

This denominator is too small for a feedback-specific recovery claim. The separately frozen
Track S is the primary conditional-recovery experiment.

## Analysis implementation note

The reusable development audit code contained two formal-run assumptions that required a
post-run read-only compatibility layer:

1. it classified the constraint prompt as a base prompt because it checked the generic
   substring `generation prompt` first; the wrapper instead uses the exact prompt hashes
   already frozen in the run manifest;
2. it calculated expected jobs as though every unique request received all three replicates;
   the wrapper uses the manifest's frozen 216-job and 1,080-outcome expectations.

The raw run manifest, calls, gate events, outcomes, and error records were not modified.

## Interpretation boundary

This formal held-out result uses one DeepSeek beta model configuration, synthetic
two-dimensional scenes, and an internally quality-controlled benchmark. It does not measure
professional review time, CAD productivity, venue compliance, or human acceptance.

The defensible Track N conclusion is:

> DeepSeek replicated deterministic containment of encoded geometric violations, but the
> gate converted a large share of unsafe or unsupported model outputs into deferrals rather
> than successful edits. Prompt-only constraints improved task success while increasing
> geometric-rule exposure, demonstrating a model-specific safety–utility trade-off.

DeepSeek Track S remains a separate unexecuted phase in this record and requires its own
balance check and explicit authorization.
