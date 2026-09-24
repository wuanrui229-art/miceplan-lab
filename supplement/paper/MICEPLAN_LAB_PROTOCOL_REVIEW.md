# Adversarial Review of MICEPlan-Lab Protocol v1.1

Review date: 2026-07-20. This review evaluates the protocol before benchmark or formal
model implementation. A `needs experiment` item is not a protocol failure; it is a
claim that must remain absent from the paper until evidence exists.

The v1.1 pre-run revision replaces pre-assumed initial-error labels with stress strata
and requires hidden feasible witnesses for all executable tasks. This prevents the
benchmark from making an impossible user request and then presenting failed recovery as
a model limitation.

## 1. Contribution

**Question:** What new knowledge can this study provide beyond showing that a rule
checker blocks violations?  
**Assessment:** pass at design level. The protocol treats blocking as an incomplete
outcome and measures safe completion, bounded recovery, repeated violations,
regressions, and marginal cost. It also includes a blind-retry condition so any recovery
gain can be attributed to rule evidence rather than extra samples alone.

**Question:** Is the contribution merely a MICE-branded instance of a known verifier
pattern?  
**Assessment:** needs experiment. Domain substitution is not accepted as the novelty.
The paper must contribute operation-level failure and recovery evidence, a reproducible
benchmark, and generalizable policy findings. If those findings are weak or obvious,
the contribution must be framed as a benchmark/tool paper or reduced to a short paper.

## 2. Writing clarity

**Question:** Are validation, gold evaluation, and repair clearly separated?  
**Assessment:** pass. Runtime policies stop only on runtime-gate output. The independent
oracle labels outputs after collection and never supplies repair evidence.

**Question:** Are safety, validity, and completion conflated?  
**Assessment:** pass. Invalid-operation exposure and safe task success are separate
primary metrics. A blocked operation is not counted as a completed task.

## 3. Experimental strength

**Question:** Could positive repair results come from receiving more LLM samples?  
**Assessment:** pass at design level. Validate-and-Blind-Retry matches the retry budget
without revealing rule evidence.

**Question:** Is one model or one wording sufficient?  
**Assessment:** needs implementation. The formal run requires two model families,
bilingual pairs, and three replicates. A one-model result may be retained as a pilot
but cannot support a model-general claim.

**Question:** Does the benchmark estimate real-world invalid-operation prevalence?  
**Assessment:** pass only with the stated limitation. The benchmark is a balanced stress
test. Overall failure rates are benchmark-specific and must not be described as field
prevalence.

## 4. Evaluation completeness

**Question:** Is the validator evaluated against itself?  
**Assessment:** pass at design level. The protocol requires an independently implemented
oracle, generated fault provenance, differential edge tests, and a blind review packet.
It still needs implementation and review evidence.

**Question:** Are important outcomes missing?  
**Assessment:** pass. The protocol covers exposure, safe completion, recovery by retry,
regression, repeated violation, defer behavior, gate precision/recall, latency, tokens,
calls, and API cost.

**Question:** Could the author tune on held-out results?  
**Assessment:** pass. Scene- and task-disjoint splits, prompt hashes, append-only logs,
and a versioned change rule are specified. Implementation must enforce these rather
than relying on memory.

## 5. Method-design soundness

**Question:** Does an `UNKNOWN` result get incorrectly treated as a violation that the
model should repair?  
**Assessment:** pass. Genuine missing evidence is deferred. Context masks make evidence
availability reproducible and prevent hidden gold from entering the runtime path.

**Question:** Does the paper make unsupported claims about professional review effort?  
**Assessment:** pass. Without a human study, only downstream candidate exposure may be
reported. Human minutes, productivity, regulatory safety, and business impact are
explicitly excluded.

**Question:** Can the current implementation execute the full protocol?  
**Assessment:** needs implementation. The research core already supports six operation
families, structured model calls, a bounded solver, and a runtime validator. It still
lacks the new benchmark, independent Shapely oracle, five-condition state machine,
gold-safe repair prompts, and analysis pipeline.

## 6. Highest remaining rejection risks

1. **Synthetic-only external validity.** Mitigation: make the controlled scope explicit,
   use irregular test scenes, and include failure-type analysis. A later public-layout
   transfer case may strengthen the paper but is not allowed to redefine v1 results.
2. **Predictable headline.** Mitigation: center the paper on where repair ceases to pay,
   not on the trivial fact that blocking reduces exposure.
3. **Small effective sample after clustering.** Mitigation: perform a pre-run paired
   power/sensitivity simulation using no held-out outputs; increase the benchmark only
   through a new protocol version before any formal calls.
4. **Oracle dependence on author-generated tasks.** Mitigation: complete the blind
   review packet, retain generator provenance, and use a separately implemented
   geometry library plus differential edge tests.
5. **Model/API drift.** Mitigation: freeze model identifiers, interleave conditions,
   record access dates, and report provider behavior as a limitation.

## 7. Claim–evidence decision

No empirical claim is currently supported. What is complete is the experimental
design. The next admissible claim is only:

> We pre-specified a controlled, paired evaluation of blocking, rule-guided repair, and
> matched blind retry for LLM-assisted two-dimensional layout editing.

Claims about error reduction, recovery, cost, generalization, or practical value remain
`needs evidence` until the formal run and analysis are complete.
