# Intent-Preserving Seeded-Recovery Pilot Protocol — 2026-07-21

**Frozen before provider calls:** 2026-07-21  
**Evidence status:** development engineering pilot, not a held-out paper result.

## Fixed seeds

- `seed-task-0016-boundary` — `MOVE_BOOTH`, C1, boundary violation;
- `seed-task-0066-overlap` — `SPLIT_BOOTH`, C2, booth overlap;
- `seed-task-0006-protected_polygon` — `ADD_BOOTH`, C2, protected-polygon collision.

Each seed is paired with its Chinese and English request, giving six jobs. Every seed
was derived from a machine-audited valid witness by changing only coordinates. The
operation set, primary target, dimensions, and count still match the declared intent,
and the independent oracle returns exactly the named single rule.

## Conditions

1. `SEEDED_VALIDATE_AND_BLOCK`: gate and stop; zero model calls.
2. `SEEDED_VALIDATE_AND_REPAIR`: up to three calls with stable rule and object evidence.
3. `SEEDED_VALIDATE_AND_BLIND_RETRY`: up to three calls with the same prior candidate
   but only a generic retry instruction.

The two repair policies use K2.7 Code HighSpeed, 32,768 maximum output tokens, fixed
temperature 1.0, the same strict schema, and counterbalanced execution order. The
independent oracle is never included in a prompt.

## Pilot acceptance checks

- 6/6 seeded jobs and 18/18 outcomes complete;
- all attempt-zero runtime gates return `FAIL` with the declared seed rule;
- zero held-out request or seed is scheduled;
- rule feedback appears only in the rule-repair arm;
- the block arm makes zero calls;
- all raw responses, retries, latency, usage, gate events, and final outcomes are
  append-only and resumable.

No minimum recovery rate is required to pass this engineering pilot. A null or adverse
repair result is retained.
