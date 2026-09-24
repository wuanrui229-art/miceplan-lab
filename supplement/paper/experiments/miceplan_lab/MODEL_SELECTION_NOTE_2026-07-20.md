# MICEPlan-Lab Model Selection Note — 2026-07-20

## Scope

These checks used one development request only. They are interface and configuration
diagnostics, not paper results. No held-out response was requested or inspected.

## Kimi K2.7 Code

- The first request was rejected because the inherited temperature was `0`; official
  K2.7 Code parameters require `1.0`.
- After correcting the temperature and MFJS enum types, two initial-arm requests were
  accepted by the provider.
- With a 2,048-token output cap, both calls ended with `finish_reason=length`, empty
  final content, and all completion tokens consumed by `reasoning_content`.
- Observed latencies were approximately 49 and 56 seconds. These values are diagnostic
  observations from one request and must not be generalized.
- The runner now assigns K2.7 Code an 8,192-token cap. This setting has not yet been
  accepted as a frozen formal configuration.

## Kimi K2.6, non-thinking

- Two provider calls completed in approximately 3–4 seconds.
- Both responses ignored the strict LayoutEditIR schema and invented a different
  operation structure, matching the provider documentation's warning that K2.6 can be
  unstable with complex JSON Schemas.
- K2.6 is therefore not preferred for the main experiment because schema failure would
  obscure the intended spatial-validation comparison.

## Kimi K3, low reasoning effort

- K3 is a general model with strict structured-output support and configurable low
  reasoning effort, making it a better conceptual fit than a coding-only model.
- Two bounded connectivity attempts returned no model response. The fully recorded
  attempt failed three times with HTTP 429 `engine_overloaded_error`.
- This is a provider-availability result, not evidence about K3 output quality. Retry at
  a different time before making a selection.

## Provisional decision

1. Do not freeze the Kimi model yet.
2. Retry a four-request development subset with K3-low when the endpoint is available.
3. If K3 availability remains poor, run the same subset with K2.7 Code at the corrected
   8,192-token cap and report its reasoning overhead honestly.
4. Select a second model from a different provider family; another Kimi version does
   not satisfy the planned cross-family robustness comparison.
5. Do not simplify the research schema merely to make K2.6 appear successful unless a
   new protocol version explicitly treats schema simplification as an experimental
   factor.

## Evidence boundary

The failed configuration attempts and provider responses remain in separate
development run directories. They are retained for auditability but excluded from
formal analysis. The dataset manifest correctly remains
`formal_model_calls_started: false`.
