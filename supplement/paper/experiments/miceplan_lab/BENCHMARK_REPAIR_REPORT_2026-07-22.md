# MICEPlan-Lab v1.1 Benchmark Repair Report

## Status

- Repair date: 2026-07-22
- Source benchmark: `miceplan-lab-v1`
- Repaired benchmark: `miceplan-lab-v1.1`
- Protocol version: `1.2`
- Formal or held-out model calls on v1.1: **none**
- Machine audit: **PASS**
- Internal bilingual surface-form review: **PASS**
- Practitioner or CAD-domain expert validation: **not claimed**

The original v1 files and preliminary development/model-selection runs are retained for
provenance. Formal experiments use the reviewed and hash-frozen v1.1 revision.

## Why v1 was rejected

The interactive author review covered all 90 semantic tasks and found 37 PASS and 53
FAIL. The failures fell into three recurring classes:

1. visible requests leaked the intended reason to defer or omitted the actual editing
   operation;
2. soft phrases such as “close to,” “same row,” and “outermost” were not measurable;
3. some C3 witnesses had no meaningful net spatial change, or an invalid probe combined
   several geometric faults despite carrying a single-rule label.

## Repairs in v1.1

- All 53 previously failed tasks changed in visible wording, stress allocation,
  witness, probe, or a combination of these fields; none was carried forward unchanged.
- Operation-specific missing-evidence requests now ask for a grid-relative edit while
  the unit and scale remain hidden in the visible context. The request no longer states
  the missing information explicitly.
- Ambiguous requests now use a natural reference such as “the entrance.” Each relevant
  scene has at least two entrances and plausible adjacent booth targets; the request no
  longer announces its own ambiguity.
- Unmeasurable proximity and outermost-position suffixes were removed. Boundary,
  overlap, and protected-region faults now arise from candidate operations, not from a
  vague preference in the user request.
- REMOVE_BOOTH no longer receives an artificial scale-missing stress condition because
  ordinary removal does not require a spatial scale.
- C3 ADD, MOVE, RESIZE, SPLIT, and RESERVE_AISLE tasks now create an actual compound
  layout change instead of deleting an object and recreating an identical object in the
  same footprint.
- Probe generation now searches for a candidate whose observed oracle result is exactly
  the one declared rule. Multi-fault candidates are rejected during generation.
- Intent checking now verifies operation-specific target IDs and can evaluate the zone
  of a supporting MOVE operation in compound resize tasks.

## Verified results

The repaired benchmark contains:

- 8 source scenes, all oracle-valid;
- 90 semantic tasks and 180 bilingual requests;
- 18 operation/complexity cells with 5 tasks per cell;
- 66 executable tasks with witnesses that pass both the oracle and intent signature;
- 24 DEFER tasks with the required context masks and scene evidence;
- 42 deterministic invalid probes, each triggering exactly one target rule;
- the frozen held-out stress distribution: 18 feasible controls and 9 tasks for each of
  BOUNDARY, OVERLAP, PROTECTED_POLYGON, LOCKED_MUTATION, AMBIGUOUS_TARGET, and
  MISSING_EVIDENCE.

The complete MICEPlan-Lab unit suite reports **32/32 tests passed**. Additional audit
guards reject leaked/vague wording, unsupported entrance ambiguity, no-op C3 witnesses,
and any probe that activates more than its declared rule.

## Formal selection impact

Repairing the C3 intent constraints made more intent-preserving seeded failures
available. Protocol v1.2 therefore freezes:

- 72 held-out natural-incidence tasks / 144 bilingual requests;
- 63 seeded recovery cases (36 single-rule and 27 two-rule composite seeds);
- 126 bilingual seeded jobs per full replicate;
- 21 balanced seeded repeat cases.

Three-rule composite seeds remain outside the primary sample and are reserved for
sensitivity analysis.

## Review boundary

All 90 repaired bilingual task pairs received an author-supervised internal
surface-form QA pass before any v1.1 held-out API call. The review checked translation
equivalence, visible operation content, and absence of leaked defer reasons. Geometry,
intent witnesses, context masks, and invalid probes remain machine-audited. This is
benchmark quality control, not practitioner annotation or CAD-domain expert validation.
