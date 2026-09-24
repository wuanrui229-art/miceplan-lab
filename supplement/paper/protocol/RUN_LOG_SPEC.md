# MICEPlan-Lab Run Log and Resume Contract

## Purpose

This contract makes model runs auditable and restart-safe. It separates provider
failures from semantic failures, preserves raw responses, and prevents a resumed run
from silently replacing or resampling a completed semantic call.

## Immutable run manifest

Each run directory begins with `run_manifest.json`. It freezes the model, provider,
endpoint class, access date, decoding settings, request IDs, replicate IDs, randomized
schedule, prompt hashes, and output-schema hash. Reopening a run directory with a
different manifest is an integrity error.

The schedule randomizes request–replicate jobs and records the order of the two initial
prompt arms and the two repair policies. The three validation policies still reuse the
exact `LLM_ONLY` first candidate.

## Append-only files

- `calls.jsonl`: full prompt, model-visible request and scene, prior candidate, allowed
  feedback, raw provider response, parsed IR, latency, token use, and infrastructure
  retry metadata;
- `gate_events.jsonl`: every runtime-gate decision and rule attribution;
- `outcomes.jsonl`: one final record per request, replicate, and policy, together with
  independent offline-oracle labels;
- `infrastructure_errors.jsonl`: interruption, network, timeout, and provider failures.

Every line is wrapped in a SHA-256 chain containing its sequence number, previous-record
hash, payload, and current-record hash. A changed, deleted, inserted, or reordered line
causes verification to fail. API keys are never written.

## Composite identity and resume

A semantic call is identified from the run, request, replicate, prompt hash, semantic
attempt number, visible-scene hash, previous-candidate hash, and feedback hash. If that
identity already has a successful record, resume returns the stored response instead of
contacting the provider again. A failed infrastructure attempt is logged separately and
may be retried without being counted as a semantic repair.

An outcome is identified by run, request, replicate, and policy. Partial policy output
can therefore be resumed without overwriting completed policy records.

## Offline labeling boundary

Gold task specifications and the independent Shapely oracle are loaded only after the
five policy outcomes have been produced. They are never included in a model prompt or
runtime repair loop. The runtime gate decides when to pass, block, repair, or defer; the
offline oracle only labels the resulting candidate for analysis.

## Current evidence boundary

The journal and resume contract is verified with a scripted 12-request interruption
test. Scripted outputs are engineering tests, not empirical model results and must not
appear as evidence for the paper's validation-benefit claims.
