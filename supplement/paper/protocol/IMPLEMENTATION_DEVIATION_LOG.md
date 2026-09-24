# MICEPlan-Lab Pre-Formal Implementation Log

## 2026-07-20 — MFJS enum typing correction

The first Kimi connectivity request was rejected before generation because Moonshot
Flavored JSON Schema requires an explicit `type` for enum fields. The canonical
LayoutEditIR schema was corrected by adding explicit string or string/null types to the
operation type, language, region, and booth-type enums. The benchmark was regenerated,
all 278 records passed JSON Schema again, all 66 feasible witnesses and 42 invalid
probes passed their audits, and dataset hashes were updated.

No successful model response and no held-out call existed before this correction. The
semantic task content, operation families, stress quotas, research questions, policies,
and metrics were unchanged, so the protocol remains v1.1. The correction is retained
here rather than silently hidden.

## 2026-07-20 — provider-specific decoding controls

Connectivity diagnostics showed that current Kimi model families impose different
fixed controls. The development runner now records model-specific settings in each run
manifest: K2.6/K2.5 non-thinking mode, K2.7 Code temperature 1.0 with a larger output
budget, and K3 low reasoning effort. These settings are development candidates, not a
formal model freeze. Any selected formal configuration will be frozen before held-out
generation.

## 2026-07-21 — explicit clarification separated from invalid-operation exposure

The first six complete jobs of the 36-request development run revealed a construct
error in the initial-arm policy action. The runner classified every schema-valid IR as
`EXPOSE`, including an IR with no operations that explicitly requested clarification.
The offline oracle correctly labeled that object `UNKNOWN`, but the metric layer then
counted it as an invalid-operation exposure. This would overstate the benefit of the
validation policies because no layout operation existed to expose.

The interrupted run is retained under
`kimi-k27-development-full-2026-07-21` with 30 policy outcomes and 13 completed calls.
It is excluded from development comparisons. No held-out request was called. Before a
replacement development run, arm A and arm B were revised so a schema-valid IR with
`requires_confirmation=true` and no operations yields final action `DEFER`. The IOER
definition now explicitly counts only operation-bearing candidates. Correct-defer rate
continues to distinguish justified from unjustified deferral. This is a development-
stage construct-validity correction, not a result-driven held-out revision.

Before the replacement run stored any response, the outcome layer was also split into
rule-invalid exposure (`FAIL`), unsupported exposure (`UNKNOWN`), broader unsafe
exposure (no independent validity plus intent fidelity), and safe resolution (safe
task success or justified defer). Correct-defer rate now uses genuine `UNKNOWN` tasks
as its denominator. The empty launch directory
`kimi-k27-development-v11-deferfix-2026-07-21` contains no model call or outcome and is
not analyzed. These definitions were frozen in the protocol manifest before the next
development run began.

## 2026-07-21 — HighSpeed serving-tier qualification

The first standard-tier call in the frozen replacement development launch took
256.713 seconds after two read timeouts; its next scheduled call failed after three
read timeouts. The partial launch is retained under
`kimi-k27-development-v11-metricsfix-2026-07-21` with one successful call and one
infrastructure error, and no policy outcome. It is not analyzed as a development
comparison. Before making any HighSpeed request, a dated selection amendment froze the
same four development IDs, an 8/8 quality gate, a 2x speed threshold, and a 25% token
allowance. No held-out request was called.

## 2026-07-21 — K2.7 completion budget raised to provider default

The completed HighSpeed development run returned three empty, length-truncated
responses. Each consumed 8,192 completion tokens, of which 8,191 were recorded as
reasoning tokens. Moonshot's current documentation states that K2.7 cannot disable
thinking and defaults `max_tokens` to 32,768. A dated development-only qualification
plan therefore raised the K2.7 output budget from 8,192 to 32,768 and froze the three
observed truncation cases plus one control before new calls. No prompt, schema, policy,
rule, metric, benchmark item, or held-out record changed.
