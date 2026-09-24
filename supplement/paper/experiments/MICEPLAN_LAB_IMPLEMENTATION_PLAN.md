# MICEPlan-Lab v1 Implementation Plan

## Outcome

Build a batch research harness that compares five constraint-handling policies over
the same initial LLM outputs, measures bounded repair, and produces publication-ready
tables from append-only raw evidence.

## Existing assets to reuse

- `paper/system/miceplan/models.py`: hall model and six operation families;
- `paper/system/miceplan/parser.py`: OpenAI-compatible structured-output adapter;
- `paper/system/miceplan/solver.py`: bounded deterministic compilation;
- `paper/system/miceplan/geometry.py`: runtime geometry gate;
- `paper/experiments/evaluate_kimi_parser.py`: provider calls, usage capture, resume,
  and append-only JSONL patterns;
- `paper/data/miceplan_eval_v1_1`: development material only, not formal evidence for
  the new research questions.

The untracked website
`github/micecad-ai-booth-planning/app/study/` contains useful rule and policy sketches,
but its 24 controlled candidates are pilot fixtures rather than formal LLM outputs.

## Work packages

### WP1 — Benchmark generator and audit

Deliverables:

- 8 scene-disjoint hall layouts;
- 90 semantic task specifications;
- 180 bilingual request instances;
- one hidden valid witness for every non-`UNKNOWN` task;
- one hidden invalid probe for every declared stress rule;
- split, balance, and leakage audit;
- blinded author-review packet;
- immutable manifest and hashes.

Acceptance gate: all twelve integrity checks in `DATA_SPEC.md` pass.

### WP2 — Independent oracle

Deliverables:

- Python/Shapely-based geometry implementation separate from the runtime gate;
- intent-fidelity evaluator for target, operation family, dimensions, position, count,
  and protected-object preservation;
- differential tests against the runtime gate;
- edge-case suite for touching boundaries, zero-area intersections, concave halls,
  repeated identifiers, and multi-operation order.

Acceptance gate: all controlled gold mutations reproduce their declared class, and
all clean scenes pass.

### WP3 — Five-condition runner

Deliverables:

- `LLM_ONLY` and `CONSTRAINT_IN_PROMPT` initial prompt arms;
- `VALIDATE_AND_BLOCK` and `VALIDATE_AND_REPAIR` policies derived from each exact
  `LLM_ONLY` first output;
- `VALIDATE_AND_BLIND_RETRY` as a matched-call ablation that withholds rule evidence;
- machine-readable repair feedback without gold leakage;
- three-attempt semantic-repair bound;
- separate infrastructure retries;
- append-only raw output, event, error, and final-outcome logs;
- safe resume by composite record key.

Acceptance gate: a 12-request synthetic smoke suite can be interrupted and resumed
without duplicate semantic calls or overwritten raw records.

### WP4 — Development pilot and freeze

Deliverables:

- 36 development requests run on the first model;
- prompt and schema error audit;
- cost estimate for the full matrix;
- frozen prompt, model, and price manifests;
- no inspection of held-out model responses.

Acceptance gate: at least 95% call completion, zero gold leakage, and complete usage
fields for successful calls.

### WP5 — Formal experiment

Planned initial-call matrix:

`144 requests × 2 initial arms × 2 models × 3 replicates = 1,728 initial calls`.

Repair calls are made only for arm-A outputs entering either repair policy. Both
`VALIDATE_AND_REPAIR` and matched `VALIDATE_AND_BLIND_RETRY` use at most three calls per
initial failure. The absolute upper bound is therefore 5,184 repair calls, although the
runtime gate should stop many loops earlier. The runner reports a live upper-bound cost
before the formal run and supports model-by-model execution.

Acceptance gate: each scheduled model condition reaches at least 95% completion; all
missing records have documented provider or infrastructure causes.

### WP6 — Analysis and paper artifacts

Deliverables:

- benchmark-composition table;
- main policy table with STS, IOER, block/defer rate, latency, tokens, calls, and cost;
- rule-feedback versus blind-retry causal ablation;
- Recovery@1/2/3 and marginal-recovery table;
- violation-type, complexity, language, and model breakdowns;
- cluster-bootstrap confidence intervals and paired effect sizes;
- marginal-recovery versus cumulative-cost plot;
- blinded failure packet containing successful recovery, repeated failure, regression,
  false block, and correct defer examples;
- machine-readable summary JSON consumed by the Typst paper.

Acceptance gate: every numerical paper claim maps to a raw field, analysis function,
and protocol-defined metric.

## Scope guards

- Do not add RAG, multi-agent orchestration, knowledge graphs, fine-tuning, or a new CAD
  backend unless a result reveals a protocol-level necessity.
- Do not use the public website interface as experimental evidence.
- Do not add a human study merely to make the paper look broader.
- Do not estimate human minutes saved without observing humans.
- Do not revise prompts after seeing held-out outputs.
- Do not select only visually successful layouts.

## Implementation sequence for the next coding turn

1. add JSON Schemas and a benchmark generator under
   `paper/experiments/miceplan_lab/`;
2. generate only the development split first;
3. implement the independent oracle and its tests;
4. add the five-condition state machine using a fake model adapter;
5. verify logging, restart safety, and metric computation locally;
6. call Kimi only after the development smoke suite is fully deterministic.
