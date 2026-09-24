# Composite-Fault Seeded-Recovery Pilot Protocol — 2026-07-21

**Frozen before provider calls:** 2026-07-21  
**Evidence status:** development difficulty-calibration pilot, not a held-out paper result.

## Reason for this development revision

The pre-specified single-fault pilot completed with safe task success in all six paired
rule-feedback and blind-retry cases on the first attempt. That null paired difference is
retained. It shows that the single-fault cases were sufficient to test the runner but
not sufficient to discriminate whether explicit rule evidence helps beyond another
sample. Before any held-out call, this second pilot tests a harder, separately labeled
fault-cardinality stratum. Results from the two pilots will not be pooled without the
fault-cardinality label.

## Fixed seeds

- `seed-task-0016-boundary+overlap+protected_polygon` — `MOVE_BOOTH`, C1;
- `seed-task-0066-boundary+overlap+protected_polygon` — `SPLIT_BOOTH`, C2;
- `seed-task-0006-boundary+overlap+protected_polygon` — `ADD_BOOTH`, C2.

Each seed is paired with its Chinese and English request, giving six jobs. Every seed
is derived from the corresponding valid witness by changing only the primary
operation's coordinates. The operation type, target, count, dimensions, language-level
task, and intent signature are unchanged. The independent oracle must report exactly
`BOUNDARY`, `OVERLAP`, and `PROTECTED_POLYGON` before a seed is admitted.

## Conditions

1. `SEEDED_VALIDATE_AND_BLOCK`: gate and stop; zero model calls.
2. `SEEDED_VALIDATE_AND_REPAIR`: up to three calls with stable rule IDs and involved
   object evidence.
3. `SEEDED_VALIDATE_AND_BLIND_RETRY`: up to three calls with the same previous
   candidate and visible scene but no rule ID, object ID, or violation reason.

The two repair policies use `kimi-k2.7-code-highspeed`, a 32,768-token output ceiling,
fixed temperature 1.0, the same structured-output schema, and counterbalanced order.
The independent oracle and valid witness are never included in a prompt.

## Pilot acceptance and interpretation

- 6/6 jobs and 18/18 policy outcomes must complete;
- all attempt-zero gates must fail with the exact declared three-rule set;
- no held-out request or seed may be scheduled;
- feedback content must appear only in the rule-feedback arm;
- all outputs, calls, retries, usage, latency, and gate events remain append-only;
- no minimum recovery rate or positive rule-feedback effect is required.

If rule feedback and blind retry remain indistinguishable, the formal study will report
that explicit feedback did not add value under these visible-scene conditions, rather
than adding further post-hoc difficulty until a positive effect appears.
