# MICEPlan-Lab v1.2 Formal Experiment Supplement

**Status:** pre-registered design candidate; no held-out model response has been observed.  
**Date:** 2026-07-21  
**Base protocol:** `MICEPLAN_LAB_PROTOCOL_V1.md` (v1.1).  
**Supersedes:** v1.1 Sections 2, 4.2, 7, 8.2, 9, and the claim–evidence map only where
this supplement is more specific. All safety, anti-circularity, logging, stopping, and
reporting boundaries in v1.1 remain in force.

## 1. Final study question

When an LLM proposes a two-dimensional layout edit, when does a deterministic
validation gate create useful recovery rather than only blocking, retrying, and adding
cost?

The study separates two quantities that the original design risked conflating:

1. **Natural incidence:** how often an unmodified LLM candidate is rule-invalid,
   unsupported, wrong-intent, safely executable, or an appropriate defer.
2. **Conditional recoverability:** given an intent-preserving candidate with a known
   geometric failure, whether explicit rule evidence improves recovery beyond a matched
   retry that sees the same request, scene, and previous candidate.

The paper must not use injected-fault recovery rates as estimates of natural model
failure frequency.

## 2. Development evidence used only to freeze the design

One complete 36-request K2.7 Code HighSpeed development run produced no independent
geometric failure in the base arm; its observed problems were primarily unsupported
exposure, wrong intent, and over-deferral. Therefore, natural failures alone could not
identify Recovery@k on development data.

Two separately frozen six-job seeded pilots then tested single-rule and three-rule
coordinate mutations. In both pilots, rule-feedback repair and blind retry each reached
safe task success in 6/6 cases on the first attempt. These null paired differences are
retained. They establish that extra sampling can solve visible geometry errors and that
rule evidence must not be assumed to add value merely because a validator exists.

No further development difficulty will be added after this supplement in pursuit of a
positive feedback effect.

## 3. Formal Track N: natural incidence and gate effect

- Population: all 72 held-out semantic tasks and both Chinese and English realizations
  (144 request instances).
- Full sample: one replicate for every request and both initial prompts (LLM-only and
  constraint-in-prompt).
- Stability subset: one held-out semantic task per operation-family × complexity cell
  (18 tasks, both languages) receives two additional replicates.
- Validate-and-Block, Validate-and-Repair, and Validate-and-Blind-Retry reuse the exact
  LLM-only first candidate. Only candidates that the runtime gate labels `FAIL` enter
  repair; `UNKNOWN` is deferred.

Primary natural outcomes are rule-invalid operation exposure rate, unsafe-candidate
exposure rate, safe task success, safe resolution, false blocking, and over-deferral.
Recovery is reported only over observed initial independent failures, with its actual
denominator shown.

## 4. Formal Track S: conditional seeded recovery

The formal sample is fixed in `formal_selection_v1_2.json` before calls:

- one intent-preserving single-rule seed for each of 36 eligible held-out semantic
  tasks;
- one intent-preserving two-rule seed for each of 27 eligible held-out semantic
  tasks;
- both Chinese and English requests for every seed, giving 126 jobs in the full
  replicate;
- a 21-seed operation-family × complexity subset receives two additional replicates;
- three-rule seeds are not part of the primary formal sample.

Each injected candidate is a coordinate-only mutation of a machine-audited valid
witness. The operation family, object target, count, dimensions, and declared intent
signature are unchanged. Admission requires independent-oracle `FAIL` with exactly the
declared rule set. The paper will call these **standardized intent-preserving injected
failures**, not LLM-generated errors.

The three policies are Block, Rule-Feedback Repair, and Blind Retry. Both repair arms
use the same previous candidate, request, visible scene, model, output contract, retry
limit, and execution schedule. Only stable rule IDs, involved object IDs, and message
codes are removed from the blind arm. The oracle and valid witness are never visible.

## 5. Primary comparisons

1. LLM-only versus Validate-and-Block on naturally produced candidates: invalid and
   unsafe exposure avoided versus safe completion lost.
2. Rule-Feedback Repair versus Blind Retry on seeded failures: paired difference in
   Recovery@1 and Recovery@3.
3. Single-rule versus two-rule failures: interaction of feedback condition with fault
   cardinality.
4. Block versus bounded repair: additional safe completions per model call, second,
   output token, and dollar.

Success requires both independent geometric `PASS` and preservation of the task intent
signature. A geometrically valid edit to the wrong object is a failure.

## 6. Statistical and reporting plan

- Report raw denominators, rates, paired risk differences, and 95% cluster-bootstrap
  intervals with semantic task as the cluster.
- Use McNemar's test only as a secondary paired binary test where discordant counts are
  sufficient; a zero-discordance result is reported directly, not forced into a
  significance claim.
- Use paired bootstrap intervals for calls, tokens, latency, and monetary cost.
- Analyze fault cardinality, rule set, operation family, complexity, language, and
  model as pre-specified strata; low-count strata remain descriptive.
- Development, formal natural, and formal seeded results remain separate.
- A null result for rule feedback is publishable evidence: it means that, under the
  evaluated visibility conditions, the gate's value came from containment while repair
  benefited from resampling rather than the specific rule message.

## 7. Model and execution freeze gate

The primary model is Moonshot `kimi-k2.7-code-highspeed`, temperature 1.0 and 32,768
maximum output tokens. A second, genuinely different model family must be named,
configured, and smoke-tested on development data before formal calls. Provider prices,
model identifiers, access dates, prompts, schema, source-tree hash, Python/runtime
versions, host platform, and all selected IDs must be stored in immutable manifests.

Formal execution is prohibited until:

1. the bilingual surface-form review is complete and is reported only as internal
   benchmark QA, not practitioner or domain-expert validation;
2. `formal_selection_v1_2.json` passes integrity audit;
3. the second model family is frozen;
4. the formal runner refuses any development/formal split mix and supports append-only
   resume;
5. a final dry-run manifest reports zero model calls.

## 8. Bounded claim

The strongest permissible conclusion is conditional:

> In MICEPlan-Lab's synthetic two-dimensional editing tasks, deterministic validation
> prevented specified invalid candidates from proceeding. Explicit rule feedback did
> or did not improve bounded recovery over matched resampling for the evaluated error
> cardinalities and models, at the reported latency, token, and API costs.

This does not establish regulatory compliance, professional productivity, commercial
MICECAD interoperability, or performance on unrestricted CAD files.
