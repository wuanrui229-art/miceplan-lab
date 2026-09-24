# MICEPlan-Lab Development-Run Audit Plan

**Frozen before the 36-request run is interpreted:** 2026-07-21  
**Scope:** development split only; no value from this audit is a held-out paper result.

## Completion gate

- all 36 scheduled request instances have five policy outcomes;
- every stored JSONL hash chain verifies;
- no held-out request ID appears in the manifest, calls, gates, or outcomes;
- provider failures and retries remain separate from semantic repair attempts;
- no response is silently replaced or excluded.

## Prompt and contract checks

1. schema-valid IR rate and length-truncation count for both initial prompt arms;
2. operation-family, target, dimension, count, coordinate, and defer-intent agreement;
3. fabricated targets or references;
4. unsupported compliance claims;
5. systematic failures by Chinese/English, operation family, complexity, or stress
   class.

## Runtime-gate checks

1. runtime `PASS`, `FAIL`, and `UNKNOWN` against the independent oracle;
2. false passes, false blocks, and rule-attribution disagreement;
3. correct defers for masked or ambiguous evidence;
4. boundary, overlap, protected-polygon, and locked-mutation coverage.

## Repair checks

For rule-evidence repair and matched blind retry, report:

- Recovery@1, Recovery@2, and Recovery@3 among initially failed base candidates;
- marginal recovery at each attempt;
- repeated violations from one attempt to the next;
- regressions that replace a reported violation with a different violation or lose
  intent fidelity;
- semantic calls, model latency, tokens, and estimated API cost per recovery.

## Freeze decision

After examining only these development outputs, either:

1. freeze the prompt files, schema, runtime messages, repair bound, K2.7 decoding
   profile, and analysis code; or
2. make a dated development-only revision, rerun all 36 requests under a new run ID,
   and retain both runs.

The 144-request test split remains untouched until a freeze record explicitly states
that no further tuning is allowed.
