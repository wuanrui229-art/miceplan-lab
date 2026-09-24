# Controlled experiment results summary

Status: controlled held-out evidence is available. All 160 template-derived
request–gold pairs passed the machine semantic audit; human review is still pending.
The frozen Kimi configuration has now been evaluated on all 128 held-out requests.
Claims remain limited to this synthetic benchmark and implemented rule set.

## Environment

- Python 3.9.6.
- macOS 15.5, ARM64.
- Single local process.
- No external LLM call was included in these timing measurements.

## Deterministic parsing baseline

Held-out test split: 128 requests.

| Metric | Result |
|---|---:|
| Schema-valid output | 100.0% |
| Operation exact match | 57.8% |
| Slot precision | 64.3% |
| Slot recall | 62.3% |
| Slot F1 | 63.3% |
| Confirmation accuracy | 72.7% |
| Confirmation macro F1 | 72.6% |
| Pipeline-state accuracy | 72.7% |
| Hallucinated internal-reference rate | 0.0% |

The pattern baseline handled protected-object requests well but failed to capture
both operations in compound requests, where operation exact match was 0%. This is a
useful lower bound rather than a competitive system result. Chinese and English test
operation exact match were 60.6% and 45.2%, respectively, showing that handcrafted
patterns were not language-neutral.

## Kimi schema-constrained development pilots

The pilots used the same 20 development request IDs, balanced across Chinese and
English and covering all seven request categories. They used Moonshot AI's
`kimi-k2.7-code` model with temperature 1. The held-out LLM test split was not
accessed. Version 0.1 used the original dataset; versions 0.2.1 and 0.3 used the
coordinate-corrected v1.1 dataset.

| Metric | v0.1 | v0.2.1 | v0.3 frozen |
|---|---:|---:|---:|
| Schema-valid output | 100.0% | 100.0% | 100.0% |
| Operation exact match | 45.0% | 60.0% | 100.0% |
| Slot F1 | 82.8% | 95.1% | 99.4% |
| Confirmation accuracy | 80.0% | 100.0% | 100.0% |
| IR-decision exact match | 25.0% | 55.0% | 95.0% |
| Pipeline-state accuracy | 80.0% | 100.0% | 100.0% |
| Hallucinated internal-reference rate | 0.0% | 0.0% | 0.0% |
| Median API latency | 12.76 s | 10.94 s | 8.40 s |
| 95th-percentile API latency | 37.05 s | 20.73 s | 17.96 s |
| Total tokens | 32,006 | 31,124 | 31,805 |

The v0.1 45.0% operation exact-match value requires qualification. Five failures were
canonicalization differences such as `east side` versus `east`; two were caused by
the generator rounding coordinates in the request text while retaining unrounded
coordinates in the gold IR. Four remaining mismatches concerned contradiction
representation, a missing relative region, or an unspecified booth type. The pilot
therefore identified both prompt-contract weaknesses and a dataset defect. Version
0.3 resolved all operation mismatches; one Chinese contradiction still omitted the
gold unresolved-reason token, leaving IR-decision exact match at 95.0%. The prompt is
now frozen. These development results must not be reported as held-out effectiveness
evidence.

### Prompt-only versus provider-enforced schema

The frozen v0.3 instructions were also evaluated without provider-side
`response_format`. The same schema was serialized as ordinary prompt context, and
invalid output received no repair.

| Metric | Prompt-only | Schema-constrained |
|---|---:|---:|
| Schema-valid output | 95.0% | 100.0% |
| Operation exact match | 95.0% | 100.0% |
| Slot F1 | 99.4% | 99.4% |
| Confirmation accuracy | 95.0% | 100.0% |
| Full IR-decision exact match | 95.0% | 95.0% |
| Pipeline-state accuracy | 95.0% | 100.0% |
| Median latency | 9.96 s | 8.40 s |
| 95th-percentile latency | 24.02 s | 17.96 s |
| Total tokens | 34,291 | 31,805 |

The single prompt-only failure was semantically reasonable but contract-invalid: it
invented a top-level `contradiction_reason` field instead of using the permitted
`unresolved_references` field. The schema-constrained run prevented this contract
violation, although it omitted the unresolved reason on the same request. With only
20 paired development cases, this is a concrete failure demonstration rather than
statistically sufficient evidence of superiority.

## Formal held-out LLM comparison

The frozen v0.3 configuration was evaluated on the 128-request test split under two
paired conditions: the closed schema supplied only in prompt context, and the same
schema enforced through the provider's structured-output interface. Both conditions
used `kimi-k2.7-code`, temperature 1, identical inputs, and no output repair.

| Metric | Prompt-only | Schema-constrained |
|---|---:|---:|
| Schema-valid output | 96.1% | **100.0%** |
| Operation exact match | 96.1% | **100.0%** |
| Slot F1 | 96.7% | **99.2%** |
| Confirmation accuracy | 96.1% | **100.0%** |
| Full IR-decision exact match | 87.5% | **93.0%** |
| Pipeline-state accuracy | 96.1% | **100.0%** |
| Hallucinated internal-reference rate | 0.0% | 0.0% |
| Median latency | 10.62 s | 11.09 s |
| 95th-percentile latency | 20.66 s | 24.15 s |
| Total tokens | 229,328 | 222,410 |

Full IR-decision agreement increased by 5.47 percentage points. Eight paired requests
were correct only under schema enforcement and one only under prompt-only output;
the two-sided exact McNemar p-value is 0.039. Schema validity improved by 3.91 points,
but the five-versus-zero discordance gives p = 0.063, so this difference is described
as an observed reduction in failures rather than a conventionally significant one.

All nine remaining schema-constrained IR mismatches involved contradictory booth
counts. The model selected the correct operation, confirmation decision, and pipeline
state, but placed the contradiction marker in `hard_constraints` or `assumptions`
instead of `unresolved_references`. Thus, structured decoding ensured syntax but did
not fully determine semantic field placement. Five prompt-only outputs were unusable:
four could not be parsed as the closed IR and one introduced an undeclared
`contradiction_reason` field.

The launcher was accidentally started concurrently. Canonical reports therefore use
the earliest complete response for each of the 128 expected request IDs; later
duplicates remain preserved in the raw files. The deterministic reconstruction and
provenance record are stored with the experiment artifacts.

## Deterministic solving and validation

Held-out executable gold IR: 80 requests. Clarification cases were excluded before
solving.

| Outcome or metric | Result |
|---|---:|
| Candidate generated | 73/80 (91.3%) |
| Awaiting approval after validation | 68/80 (85.0%) |
| Blocked by independent validation | 5/80 (6.3%) |
| Proven infeasible by capacity bound | 7/80 (8.8%) |
| Feasible among generated candidates | 68/73 (93.2%) |
| Median solver time | 0.028 ms |
| 95th-percentile solver time | 0.792 ms |
| Median validation time | 2.257 ms |
| 95th-percentile validation time | 4.629 ms |

All five blocked candidates intersected a configured protected polygon. The result
shows that solver output and approvable output are not equivalent, supporting the
separate validator gate. The very low runtime reflects small normalized synthetic
halls and must not be generalized to production CAD scale.

## Validator fault injection

The held-out 32 halls produced 32 clean cases and 160 controlled fault cases: overlap,
outside-boundary placement, protected-polygon intersection, duplicate identifier,
and protected-object mutation.

| Metric | Result |
|---|---:|
| Fault-detection precision | 100.0% |
| Fault-detection recall | 100.0% |
| Fault-detection F1 | 100.0% |
| Primary-rule attribution accuracy | 100.0% |
| Median validation time | 2.125 ms |
| 95th-percentile validation time | 4.406 ms |

Perfect performance is expected for these explicitly constructed invariant
violations. It demonstrates regression coverage of the five implemented checks, not
complete detection of real CAD, building-code, or exhibition-design errors.

## Reviewer-facing interpretation

1. The deterministic parser is not sufficient for compound bilingual interpretation;
   a schema-constrained LLM experiment is justified.
2. Candidate generation alone is not a safe acceptance criterion because five
   solver outputs were independently blocked.
3. The validator behaves correctly on the injected invariant violations, but the
   fault model is intentionally narrow.
4. The current evidence supports a controlled software-engineering prototype claim,
   not an industrial productivity or regulatory-compliance claim.
5. The paired held-out run supports a benchmark-scoped contract-reliability benefit
   from provider-side schema enforcement, while contradiction field placement remains
   an observed semantic weakness.

## Raw evidence

- `results/deterministic_parser_v1_1_report.json`
- `results/deterministic_parser_v1_1_predictions.jsonl`
- `results/solver_v1_1_report.json`
- `results/solver_v1_1_cases.jsonl`
- `results/validator_fault_v1_1_report.json`
- `results/validator_fault_v1_1_cases.jsonl`
- `results/kimi_schema_pilot_v0_1_reproducibility_snapshot.jsonl`
- `results/kimi_schema_pilot_v0_2_1_report.json`
- `results/kimi_schema_pilot_v0_3_report.json`
- `results/kimi_prompt_only_pilot_v0_3_report.json`
- `results/kimi_schema_test_v0_3_canonical_report.json`
- `results/kimi_prompt_only_test_v0_3_canonical_report.json`
- `results/kimi_formal_test_v0_3_comparison.json`
