# Frozen evaluation protocol v0.1

Status: frozen before model experiments. Any change after observing results must be
logged with a reason and must not overwrite earlier raw outputs.

## 1. Evaluation assets

- Dataset: `MICEPlan-Eval-v1.1`.
- Hall models: 40 total; 8 development and 32 held-out test halls.
- Requests: 160 total; 32 development and 128 held-out test requests.
- Languages: 80 Chinese and 80 English requests.
- Request categories: simple, capacity-stress, compound, ambiguous, contradictory,
  revision, and protected-object.
- Gold origin: controlled templates followed by strict schema validation.
- Machine semantic audit: passed for all 160 request–gold pairs; the audit checks
  language, operation family, references, slots, policy flags, and expected states.
- Human review: pending; results must not be described as manually annotated until
  the review record is completed. Formal evaluation may proceed against the audited
  template gold as long as this limitation is stated explicitly.

### Frozen-protocol revision log

- **2026-07-16, v1 to v1.1:** A development-only Kimi pilot revealed that aisle
  coordinates were rounded in request text but retained as unrounded values in gold
  IR. The generator now writes the same rounded coordinate to both representations.
  `MICEPlan-Eval-v1` and all v0.1 raw model outputs remain archived. No held-out LLM
  request had been evaluated when this correction was made. Deterministic results on
  v1 are legacy evidence and must be regenerated on v1.1 before final reporting.

## 2. Parsing evaluation

### Systems

1. **Deterministic baseline:** the implemented bilingual pattern parser.
2. **Prompt-only LLM:** the selected model is asked for JSON without a strict output
   schema response constraint. The same JSON Schema is serialized as ordinary prompt
   context, and invalid output receives no automatic repair.
3. **Schema-constrained LLM:** the same model, system instructions, temperature, and
   request context are used with the strict `LayoutEditIR` JSON Schema.

The model name, provider, access date, decoding parameters, prompt text, latency, and
token counts must be preserved. Development requests may be used to refine prompts;
test requests may be run only after the prompt is frozen.

The schema-constrained configuration was frozen on 2026-07-16 as follows:

- provider: Moonshot AI / Kimi Open Platform;
- model: `kimi-k2.7-code`;
- temperature: 1;
- prompt: `layout-edit-ir-v0.3`;
- dataset: `MICEPlan-Eval-v1.1`;
- development evidence: 20-request balanced pilot;
- remaining observed limitation: one contradictory Chinese request omitted the
  machine-readable unresolved-reason token despite correct empty operations and
  confirmation decision.

No further prompt or schema change is permitted after the first held-out LLM call.

### Metrics

- schema-valid JSON rate (higher is better);
- operation exact match (higher is better);
- micro-averaged slot precision, recall, and F1 (higher is better);
- confirmation-decision accuracy and macro F1 (higher is better);
- executable-IR rate after deterministic compilation (higher is better);
- hallucinated object-reference rate (lower is better).

The main test is one complete run over 128 held-out requests. A stratified 40-request
subset is repeated three times to measure output stability without multiplying the
full API cost excessively.

## 3. Geometry and validation evaluation

### Solver evaluation

Executable gold IR records are compiled against their source halls. Report:

- candidate-generation rate;
- independently validated feasible-layout rate;
- hard-constraint violation count;
- median and 95th-percentile solver runtime;
- results by hall geometry category and request category.

An infeasible or blocked result is not automatically an error when the declared
request cannot safely be realized. Failure cases must be inspected and grouped.

### Validator fault-injection evaluation

For each held-out hall, create controlled mutations representing:

1. booth overlap;
2. booth outside the hall boundary;
3. obstacle, protected-aisle, or exit-clearance intersection;
4. duplicate booth identifier or visible number;
5. sold or locked booth mutation.

Measure fault-detection precision, recall, F1, and rule attribution accuracy. The
mutation label is known from the injector, but successful detection must come from
the independent validator.

## 4. Ablations

Only two causally interpretable comparisons are planned:

1. prompt-only output versus strict schema-constrained output, isolating syntax and
   provider-side contract enforcement from an in-prompt contract;
2. solver candidates accepted without independent validation versus the full
   validator-gated workflow, measured with fault injection.

Multi-agent, RAG, fine-tuning, knowledge graphs, and unrestricted CAD parsing are not
included because they are not required by the central claim.

## 5. Reporting rules

- Report development and test results separately.
- Do not select only successful examples.
- Preserve every raw model response, parse error, solver error, validator report,
  runtime, and configuration record.
- Do not claim regulatory compliance, professional productivity, industrial-grade
  operation, or superiority to human experts.
- Treat the template-derived dataset and internal geometry rules as controlled
  evaluation assets, not representative industry data.
