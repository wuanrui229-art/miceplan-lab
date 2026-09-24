# MICEPlan-Lab Development Model-Selection Protocol

**Frozen before calls:** 2026-07-21  
**Purpose:** select one Kimi configuration for the 36-request development pilot.  
**Evidence status:** engineering selection only; never a formal paper result.

## Fixed requests

1. `task-0001-en` — English, feasible `ADD_BOOTH` control;
2. `task-0021-zh` — Chinese, boundary-stress `MOVE_BOOTH`;
3. `task-0036-en` — English, locked-object-stress `RESIZE_BOOTH`;
4. `task-0086-zh` — Chinese, ambiguous-target `RESERVE_AISLE`.

These IDs were chosen before inspecting any response from the compared configurations.
They balance language and cover a clean edit, two deterministic hard-constraint stress
types, and one legitimate defer case.

## Compared configurations

- `kimi-k3`: low reasoning effort, 4,096 maximum completion tokens;
- `kimi-k2.7-code`: provider-fixed temperature 1.0, 8,192 maximum output tokens.

Both use the same request records, visible scenes, two initial prompt arms, strict
LayoutEditIR schema, and one replicate. Semantic repair is disabled for this selection
test, so each model has exactly eight planned model calls if infrastructure succeeds.

## Pre-specified selection gate

A configuration is eligible only if it has:

1. all 8 expected initial calls recorded;
2. zero infrastructure-error records;
3. 8/8 schema-valid LayoutEditIR outputs;
4. zero `finish_reason=length` responses.

If both configurations pass, prefer the configuration with lower median total tokens;
use median latency as the tie-breaker. If neither passes, do not freeze a model and do
not expand to the 36-request pilot. Diagnose or add a different Kimi configuration in a
new dated selection protocol.

## Scope guard

No held-out request, repair-rate result, IOER estimate, STS estimate, or scientific
claim may be derived from this four-request selection exercise.
