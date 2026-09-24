# MICEPlan-Lab v1.1: Frozen Validation–Recovery Experiment Protocol

**Protocol status:** design-frozen before formal model calls  
**Freeze date:** 2026-07-20  
**Supersedes:** none. The earlier `EVALUATION_PROTOCOL.md` remains valid only for the
IR-parsing study and must not be presented as evidence for this validation–recovery
study.  
**Change rule:** any change after a held-out response is observed creates a new
protocol version, records the reason, and preserves all earlier configurations and raw
outputs.

### Pre-run revision log

- **2026-07-20, v1.0 to v1.1:** implementation audit found that calling benchmark
  strata "expected initial failures" would incorrectly pre-assume model behavior and
  could make recovery impossible when a user request itself demanded an invalid edit.
  The strata are now stress types. Every non-`UNKNOWN` task must include a hidden valid
  witness proving that the user goal is achievable, plus a hidden invalid probe proving
  that the targeted rule can be violated in the scene. Actual LLM outcomes remain
  unconstrained and are labeled only after collection. No development or held-out model
  call had been made under v1.0.

## 1. Study purpose and bounded claim

MICEPlan-Lab is a controlled testbed for studying deterministic validation feedback in
LLM-assisted two-dimensional layout editing. The study asks whether a validation gate
does more than suppress invalid candidates: it measures whether rule feedback can
recover a valid, intent-preserving edit and whether that recovery is worth the extra
model calls, latency, tokens, and monetary API cost.

The study does **not** claim that MICEPlan-Lab is an official MICECAD integration, a
commercial CAD engine, a fire-safety certifier, or a substitute for professional
planning. Its rules are executable experimental invariants over synthetic hall data.
Actual human review time and professional productivity are outside the primary study;
without a separate user study, the paper may report only the number of candidates
exposed to a downstream review stage, not minutes of human effort saved.

## 2. Research questions

**RQ1 — Initial failure.** How often do LLM-generated layout-edit operations violate a
covered hard constraint, fail to identify an executable target, or lack sufficient
evidence, and how do these failures vary by operation family and task complexity?

Because the benchmark deliberately balances valid and adverse cases, RQ1 estimates
failure incidence under this stress-test distribution; it is not an estimate of the
prevalence of invalid requests in commercial MICE workflows.

**RQ2 — Gate effect.** Compared with an otherwise identical LLM-only workflow, how
much does deterministic validation reduce independently confirmed invalid-operation
exposure, and what completion loss is introduced by blocking?

**RQ3 — Recovery–cost trade-off.** When a failed operation receives machine-readable
constraint feedback, how often is it recovered after one, two, and three attempts, and
how do the marginal gains compare with added latency, token use, and API cost?

Language and model family are planned robustness factors, not separate research
questions. They test whether the main finding depends on one wording or one provider.

## 3. Pre-specified expectations

- **H1:** a deterministic gate will reduce invalid-operation exposure relative to the
  LLM-only arm, but blocking alone will not necessarily improve safe task completion.
- **H2:** validation with bounded repair will recover more safe task completions than
  validation with blocking alone.
- **H3:** the marginal recovery yield will decrease across repair attempts.
- **H4:** recovery yield and overhead will differ by violation type and complexity; a
  single average is not sufficient to decide when repair pays off.

These are directional expectations, not conclusions. Null, negative, and mixed results
must be retained and reported.

## 4. Unit of analysis and benchmark construction

### 4.1 Experimental unit

The basic unit is one tuple:

`(semantic_task_id, language, scene_id, model_id, replicate_id)`.

Chinese and English versions of the same semantic request share one
`semantic_task_id` and are treated as dependent observations in statistical resampling.
Repeated model calls for the same semantic task are also clustered together.

### 4.2 Frozen target size

- 8 synthetic structured hall scenes;
- 90 language-independent semantic tasks;
- one Chinese and one English realization per semantic task;
- 180 request instances in total;
- 18 semantic tasks / 36 request instances for development;
- 72 semantic tasks / 144 request instances for held-out testing;
- 2 development scenes and 6 scene-disjoint test scenes;
- at least 2 model families in the formal comparison;
- 3 model replicates per request and initial-generation prompt arm.

The split occurs by both scene and semantic task. Prompt development may use only the
development split. Held-out scene geometry, wording, gold annotations, and result
summaries remain hidden from prompt revision.

### 4.3 Operation families

The benchmark covers the six operation families implemented by the executable
research core:

1. `ADD_BOOTH`;
2. `MOVE_BOOTH`;
3. `RESIZE_BOOTH`;
4. `REMOVE_BOOTH`;
5. `SPLIT_BOOTH`;
6. `RESERVE_AISLE`.

The 90 semantic tasks are balanced across six operation families and three complexity
tiers, with five semantic tasks per operation–complexity cell.

### 4.4 Complexity tiers

- **C1 — local:** one operation, one explicit target, and at most one relevant
  geometric interaction;
- **C2 — coupled:** one operation whose result depends on multiple objects or multiple
  hard constraints;
- **C3 — sequential:** two or three dependent operations where an earlier edit changes
  the feasibility of a later edit.

Complexity is assigned from the structured task specification before natural-language
realization. Token length is recorded but is not used as the complexity label.

### 4.5 Stress-stratum quotas for the held-out semantic tasks

- 18 feasible-control tasks;
- 9 boundary-stress tasks;
- 9 booth-overlap-stress tasks;
- 9 protected-polygon-stress tasks;
- 9 sold/locked-object-stress tasks;
- 9 ambiguous or unresolved-target tasks;
- 9 missing-unit, scale, or required-evidence tasks.

The first four stress categories do not assert that an LLM must fail. For every
non-`UNKNOWN` stress task, the gold package stores (a) a valid witness showing that the
requested goal is achievable and (b) an invalid probe that activates the intended
rule. Neither is visible to the model or runtime policy. The actual first candidate may
pass, fail under the targeted rule, fail under another rule, or lose intent fidelity.

Ambiguous-target and missing-evidence tasks are `UNKNOWN` cases, not geometric
failures. A correct system must not invent missing evidence merely to obtain a `PASS`
result. These tasks have `DEFER` as the admissible outcome rather than a hidden valid
edit.

Missing-evidence tasks use a declared context mask: the generation and runtime-gate
views omit the relevant scale, unit, or disambiguating metadata, while the independent
oracle retains the complete synthetic scene solely to label whether a fabricated edit
would have been valid. The mask is recorded in `requests.jsonl` and applied identically
across conditions.

## 5. Systems and controlled conditions

All conditions use the same provider-enforced structured-output contract, operation
schema, scene context, decoding limits, and base system instruction. This removes JSON
formatting as a confound and isolates spatial constraint handling.

### 5.1 Initial-generation arms

**A. LLM-only.** The base prompt describes the requested edit and output contract but
does not enumerate the deterministic geometry rules. Every schema-valid,
operation-bearing candidate is considered exposed to the downstream workflow.
An explicit no-operation clarification request (`requires_confirmation=true`) is
recorded as `DEFER`, not as an invalid layout operation. Independent offline evaluation
decides whether an exposed candidate was actually valid and whether a defer was
appropriate.

**B. Constraint-in-Prompt.** The same request and schema are used, but concise
descriptions of the covered hard constraints are included in the prompt. No
post-generation validation feedback or repair is provided. This tests whether cheap
prevention through prompting can replace runtime enforcement. The same explicit-defer
semantics as arm A apply.

### 5.2 Policies applied to the exact output from arm A

**C. Validate-and-Block.** The arm-A candidate is checked by the MICEPlan-Lab gate.
`FAIL` and `UNKNOWN` do not proceed. No model repair is requested.

**D. Validate-and-Repair.** The same arm-A candidate is checked by the same gate.
For `FAIL`, the model receives only the previous candidate, rule IDs, involved object
IDs, and concise violation evidence. It may return a revised operation. The loop stops
when the **runtime gate** returns `PASS`, when the system correctly defers an `UNKNOWN`,
or after three repair attempts. The independent oracle never controls the runtime loop.
For genuine `UNKNOWN`, the correct action is clarification/defer; the model must not
receive hidden dimensions, object identities, or the gold operation.

**E. Validate-and-Blind-Retry (causal ablation).** The same arm-A candidate and runtime
gate trigger up to three retries, but the model receives only a generic instruction to
revise the candidate. It does not receive rule IDs, involved objects, or violation
evidence. D versus E isolates the effect of deterministic feedback content from the
effect of receiving extra model samples.

Arms C, D, and E reuse arm A's exact first output. They must not make separate initial
calls, because different first outputs would confound policy effect with sampling
variation. D and E use the same retry limit, model, decoding configuration, and prior
conversation structure; only the feedback content differs.

### 5.3 Gate stages

The deterministic gate consists of four explicitly logged stages:

1. schema and required-field validation;
2. object-reference and protected-status checks;
3. bounded compilation/solver feasibility;
4. a runtime post-solver geometry validator that is independent of the solver but is
   distinct from the offline gold oracle.

Each stage returns `PASS`, `FAIL`, or `UNKNOWN`, together with stable rule IDs and
object references. Infrastructure errors such as timeout, rate limit, or HTTP 5xx are
not model failures and are retried separately under the infrastructure policy.

## 6. Independent gold and anti-circularity safeguards

The production gate cannot serve as its own ground truth. Formal evaluation therefore
uses a separate oracle path:

1. structured semantic task specifications define the requested intent and admissible
   operation family before natural-language realization;
2. task generation records the intended stress type, goal predicate, hidden valid
   witness where applicable, and hidden invalid probe;
3. a separate Python geometry oracle, implemented independently from the runtime gate,
   evaluates boundaries, intersections, protected objects, and state invariants;
4. every gold record is checked for bilingual semantic equivalence and reviewed in a
   blind packet that does not contain model outputs;
5. a manifest stores file hashes, generator version, oracle version, and review status.

If Shapely is available, the independent oracle will use Shapely predicates. The
runtime gate remains the existing MICEPlan implementation. If Shapely cannot be used,
the paper must disclose the fallback and run differential tests over generated edge
cases. Gold annotations may be described as author-reviewed only after the review
packet is completed; they must never be described as expert-annotated without actual
expert participation.

Intent preservation is evaluated separately from geometric validity. A geometrically
valid edit that changes the wrong object or does not perform the requested operation is
not a successful recovery.

## 7. Model and run-control policy

- Formal evaluation requires at least two model families. The first confirmed family
  is Moonshot/Kimi; the second model is frozen in the run manifest before held-out
  calls.
- Exact provider, endpoint class, model snapshot, access date, temperature, maximum
  output tokens, timeout, and prompt hashes are recorded per run.
- Decoding parameters are fixed within a model across all conditions. No test output
  may be used to revise a prompt, schema, rule message, or retry strategy.
- Each initial-generation arm is run three times per held-out request. If the provider
  exposes a seed, it is recorded; identical seeds are requested across A and B when
  supported, but provider determinism is not assumed.
- Initial A/B calls are interleaved in a randomized, reproducibly seeded order within
  model and replicate. D/E repair jobs are also interleaved to reduce time-of-day and
  provider-drift confounding.
- Model repair is limited to three semantic attempts. Timeout, 429, and HTTP 5xx
  retries are tracked separately and do not count as semantic repair.
- Every response is written immediately to append-only JSONL so an interrupted run can
  resume without replacing completed records.
- Raw responses, parsed IR, validator reports, repair prompts, token use, latency, and
  provider errors are retained. API keys are never written to results.

## 8. Outcomes and metric definitions

### 8.1 Primary outcomes

**Rule-invalid operation exposure rate (RIOER, lower is better)**

`independent_oracle_FAIL_operation_bearing_candidates_exposed / all_requests`.

Exposure means that a candidate would reach the next execution or approval stage under
the evaluated policy. An explicit no-operation request for clarification is a defer,
not an exposed invalid operation. It does not claim that a person actually reviewed the
candidate. `UNKNOWN` is not silently merged with `FAIL`.

**Unsafe-candidate exposure rate (UER, lower is better)**

`exposed_candidates_without_independent_PASS_and_intent_fidelity / all_requests`.

This broader companion outcome catches a geometrically feasible but wrong-intent edit
and an unsupported guess on a genuine clarification case. `UnsupportedExposureRate`
separately reports exposed candidates for which the independent oracle returns
`UNKNOWN`. RIOER is the direct measure of deterministic rule containment; UER prevents
the paper from implying that geometric validity alone makes an LLM edit correct.

**Safe task success (STS, higher is better)**

`intent_correct_and_independently_valid_final_operations / all_requests`.

A blocked invalid operation is safe but is not a successful task completion.

**Safe resolution rate (SRR, higher is better)**

`(safe_task_successes + correct_defers_on_genuine_UNKNOWN_cases) / all_requests`.

SRR complements STS so a model is not penalized for correctly requesting missing
evidence. Correct-defer rate uses genuine `UNKNOWN` tasks, not all requests, as its
denominator. Over-deferral remains visible through STS, defer rate, and SRR.

### 8.2 Recovery outcomes

- `Recovery@k`: proportion of initially invalid `FAIL` cases that become intent-correct
  and independently valid within `k` repair attempts;
- `MarginalRecovery_k`: newly recovered cases at attempt `k` divided by cases that
  entered attempt `k`;
- `RegressionRate`: repairs that remove one reported violation but introduce a new
  violation or lose intent fidelity;
- `RepeatedViolationRate`: repairs that repeat at least one violation rule from the
  preceding candidate;
- `CorrectDeferRate`: genuine `UNKNOWN` cases correctly returned for clarification
  without fabricating missing evidence; the denominator is the number of genuine
  `UNKNOWN` cases.

### 8.3 Gate and operational outcomes

- gate precision, recall, F1, and rule-attribution accuracy against the independent
  oracle;
- false-block rate for independently valid operations;
- block rate and defer rate;
- end-to-end latency and model-only latency in milliseconds;
- prompt, completion, cached, and total token counts;
- semantic model-call count and infrastructure-retry count;
- API cost using the provider's recorded price schedule and access date;
- additional tokens, seconds, and cost per recovered safe task;
- additional tokens, seconds, and cost per invalid exposure avoided.

The independent oracle labels every attempted candidate after collection. It may show
that a candidate was already independently valid before the runtime gate stopped, or
that a runtime `PASS` remained invalid. These cases are retained as false-block or
false-pass evidence; oracle output is never fed back into the live policy.

### 8.4 Payoff interpretation

No single arbitrary utility weight is used as the headline result. The paper reports a
Pareto view over STS, IOER, latency, and API cost, plus marginal-recovery curves. A
policy "pays off" only within a stated operating preference, for example when it
increases STS at an acceptable cost while not increasing IOER.

For monetary sensitivity, the compute-only break-even cost of one invalid exposure is:

`incremental_API_cost / invalid_exposures_avoided`.

This threshold does not include unmeasured human labor, business impact, or safety
harm. Those quantities must not be invented.

## 9. Statistical analysis

- Report counts, rates, and 95% confidence intervals for every primary outcome.
- Use cluster bootstrap confidence intervals with `semantic_task_id` as the resampling
  unit so bilingual variants and replicates are not treated as independent samples.
- Use paired comparisons because C and D share A's initial candidates.
- Use McNemar's test for paired binary outcomes such as STS and exposure where its
  assumptions are met; report paired risk differences and confidence intervals as the
  main effect sizes.
- Use paired bootstrap intervals and a Wilcoxon signed-rank sensitivity check for
  latency, tokens, and cost.
- Correct families of secondary per-category comparisons with Holm's method.
- Report results separately by violation type, complexity, operation family, language,
  and model. Subgroup findings are exploratory unless the subgroup test was specified
  here.
- Do not pool development and held-out results.

## 10. Required tables and figures

1. **Benchmark composition:** scenes, operations, outcomes, languages, and complexity.
2. **Main policy comparison:** IOER, STS, block/defer rate, calls, latency, tokens, and
   API cost for A–E.
3. **Recovery table:** Recovery@1/2/3, repeated violations, and regression by failure
   category.
4. **Robustness table:** paired effects by model and language.
5. **Pipeline figure:** generation, validation, blocking, repair, and independent
   evaluation paths.
6. **Marginal-recovery curve:** additional valid recoveries versus retry number and
   cumulative token cost.
7. **Failure gallery:** representative successful repair, repeated failure, regression,
   false block, and correct defer cases selected by pre-defined categories rather than
   visual appeal.

## 11. Stopping and exclusion rules

- The semantic repair loop stops at runtime-gate `PASS`, correct runtime defer, or
  three repair attempts. Independent-oracle labels are attached only after the policy
  action is complete.
- A request is excluded only for a documented benchmark corruption discovered without
  reference to comparative system performance. Exclusions create a protocol revision
  and are reported.
- Provider outages do not justify selecting a successful response. Runs resume from
  append-only logs.
- A model condition is incomplete until at least 95% of scheduled calls are obtained;
  any remaining missingness and reason are reported.
- No outlier is removed solely because latency, token use, or output quality is poor.

## 12. Reporting boundaries

Permitted claims are limited to controlled two-dimensional edits, the declared rule
set, evaluated models, synthetic scenes, and recorded costs. The paper may infer where
bounded repair appears useful within this testbed, but must not generalize to all CAD,
all MICE planning, legal compliance, or professional productivity.

The strongest acceptable conclusion has the form:

> Under the evaluated rules and models, deterministic feedback recovered specified
> classes of invalid layout edits within a bounded number of attempts, while other
> classes showed low marginal recovery and disproportionate operational overhead.

The protocol explicitly allows the opposite result: if repair rarely improves STS or
its marginal cost is excessive, the paper will conclude that blocking or clarification
is preferable for those cases.

## 13. Claim–evidence map fixed before results

| Planned claim | Required evidence | Status before formal run |
|---|---|---|
| MICEPlan-Lab supports reproducible validation–repair experiments | released scenes, requests, manifests, runner, raw logs, and tests | needs implementation |
| A validation gate reduces invalid-operation exposure | paired A-versus-C/D/E IOER with independent oracle and confidence interval | needs evidence |
| Repair recovers safe task completions beyond blocking | paired C-versus-D STS and Recovery@k | needs evidence |
| Rule evidence contributes beyond merely retrying | paired D-versus-E STS, Recovery@k, and overhead | needs evidence |
| Repair benefit depends on failure type and complexity | stratified recovery effects with uncertainty | needs evidence |
| Later retries have diminishing returns | marginal-recovery curve with cumulative cost | needs evidence |
| The finding is not unique to one wording or provider | bilingual, two-model robustness analysis | needs evidence |

No abstract, introduction, or conclusion may present a `needs evidence` row as an
established result.

## 14. Immediate implementation order

1. create the v1 benchmark schema and manifest;
2. extend the task generator to six operation families and three complexity tiers;
3. implement the independent oracle and differential edge-case tests;
4. implement the five-condition batch runner and bounded repair loop;
5. implement append-only logging and resume checks;
6. run the 36-request development split and audit failures;
7. freeze both model manifests and prompts;
8. run the held-out experiment once, without prompt revision;
9. generate statistical tables, plots, and failure packets from raw logs.
