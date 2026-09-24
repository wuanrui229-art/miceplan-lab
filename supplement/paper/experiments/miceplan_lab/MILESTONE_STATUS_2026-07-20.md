# MICEPlan-Lab Implementation Status — 2026-07-20

## Completed

- Protocol v1.1 pre-run correction recorded and hashes verified.
- JSON Schemas implemented for scenes, requests, hidden gold, LayoutEditIR, and run
  manifests.
- Eight scene-disjoint synthetic halls generated: two development and six held-out.
- Ninety semantic tasks generated with five tasks in every operation–complexity cell.
- One hundred eighty bilingual requests generated: 36 development and 144 held-out.
- Held-out stress quotas exactly match 18 controls plus nine tasks in each of six stress
  categories.
- Sixty-six executable tasks have hidden feasible witnesses that pass both intent and
  Shapely geometry checks.
- Forty-two deterministic stress tasks have hidden invalid probes that activate their
  declared rules.
- Twenty-four `UNKNOWN` tasks contain no hidden edit answer and use reproducible context
  masks.
- Machine audit passed all 278 scene/request/gold records against JSON Schema.
- Independent Shapely oracle implemented without importing the runtime gate or solver.
- Runtime-versus-oracle differential tests cover boundary, overlap, protected polygon,
  and locked-object mutation rules.
- Five-condition state machine implemented with exact initial-output reuse and a
  matched blind-retry ablation.
- Initial prompt-arm order and repair-policy order are reproducibly counterbalanced in
  the recorded run schedule.
- Development prompt templates implemented for base generation, constraint prompting,
  rule-evidence repair, and generic blind retry.
- OpenAI-compatible live adapter implemented with provider-enforced JSON Schema,
  bounded infrastructure retries, raw-response retention, and normalized usage fields.
- Hash-chained append-only call, gate-event, outcome, and infrastructure-error journals
  implemented with composite-key resume.
- Development-only runner requires an explicit `--execute` flag; its default dry run
  makes no provider call and schedules no held-out request.
- Descriptive IOER, STS, block/defer, call, latency, and token summaries can be
  recomputed from raw outcome records.
- Protocol and dataset integrity verifiers pass.

## Verification evidence

- New MICEPlan-Lab tests: 21 passed.
- Existing MICEPlan core regression tests: 13 passed.
- Interrupted 12-request smoke suite: resumed to 60/60 policy outcomes with no duplicate
  completed semantic-call key.
- Source scenes passing independent oracle: 8/8.
- Feasible witnesses passing oracle and intent: 66/66.
- Invalid probes activating expected rules: 42/42.
- Bilingual task pairs present: 90/90.

## Deliberately not completed yet

- Author review packet: 0/90 reviewed; status remains `PENDING`.
- Kimi development model selection: completed on four pre-specified development
  requests. K2.7 Code completed 8/8 schema-valid initial calls with no truncation or
  infrastructure error. K3-low stopped after three provider-overload responses on its
  first scheduled request. K2.7 is provisional for the development pilot; this is not
  a formal result.
- Full 36-request Kimi development pilot: not started.
- Second model selection: not frozen.
- Append-only production run journal and resume mechanism: completed and smoke-tested.
- OpenAI-compatible live model adapter for the five-condition runner: implemented,
  smoke-tested, and used for eight recorded K2.7 development calls.
- Statistical analysis pipeline and formal results: pending.

No held-out empirical claim about validation benefit, recovery, latency, or cost is
supported at this milestone. The completed evidence concerns benchmark integrity,
executable experimental design, and provider-interface diagnostics only.
