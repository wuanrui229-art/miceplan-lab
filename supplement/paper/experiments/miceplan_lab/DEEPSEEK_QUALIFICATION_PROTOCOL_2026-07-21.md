# DeepSeek V4 Pro Development Qualification Protocol — 2026-07-21

**Frozen before provider calls:** 2026-07-21  
**Scope:** development-only second-family qualification; no held-out calls.  
**Evidence status:** engineering selection evidence, not a formal paper result.

## Fixed configuration

- Provider/model: DeepSeek Open Platform, `deepseek-v4-pro`;
- endpoint: DeepSeek beta chat-completions endpoint;
- reasoning: thinking enabled, high reasoning effort;
- output budget: 32,768 tokens;
- output contract: provider-enforced strict function tool with the frozen
  LayoutEditIR JSON Schema, converted only to DeepSeek's documented supported
  schema subset;
- replicate count: one;
- semantic repairs: zero.

DeepSeek's native strict function-tool mechanism is not the same wire-level feature as
Kimi's `response_format` JSON Schema. Both enforce the same frozen LayoutEditIR contract
at the provider boundary, and every returned candidate is additionally validated locally
against the unmodified Draft 2020-12 schema. This implementation difference must be
disclosed in any cross-provider comparison.

## Fixed requests and calls

1. `task-0001-en` — English feasible `ADD_BOOTH` control;
2. `task-0021-zh` — Chinese boundary-stress `MOVE_BOOTH`;
3. `task-0036-en` — English locked-object-stress `RESIZE_BOOTH`;
4. `task-0086-zh` — Chinese ambiguous-target `RESERVE_AISLE`.

For each request, run the base prompt and constraint-in-prompt arm. This produces exactly
eight planned initial calls. No test-split request or formal selected item may be sent.

## Pre-specified qualification gate

The configuration passes only if it has:

1. all 8 expected initial calls recorded;
2. zero infrastructure-error records;
3. 8/8 locally schema-valid LayoutEditIR outputs;
4. zero `finish_reason=length` responses.

If the strict-tool API rejects the schema or model configuration, retain the failed run,
record the provider error, and amend the adapter in a dated deviation note before a new
run. Do not silently fall back to prompt-only JSON output. Passing this gate permits a
larger development run only; it does not freeze a formal model.

## Cost record

For this dated run, cost is estimated from the official DeepSeek V4 Pro token prices in
`PRICING_DEEPSEEK_V4_PRO_2026-07-21.json`. Provider-reported prompt-cache hits are billed
at the cache-hit input price; the remaining prompt tokens use the cache-miss input price.

