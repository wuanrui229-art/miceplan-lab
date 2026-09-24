# DeepSeek Strict-Schema Development Amendment — 2026-07-21

**Recorded after the failed request and before the replacement run.**

The first run, `model-selection-deepseek-v4-pro-2026-07-21`, stopped before any
model generation. DeepSeek returned HTTP 400 while parsing the strict tool schema:
`field anyOf: missing field type`. The append-only infrastructure-error record is
retained in that run directory.

The rejected schema represented JSON null with an `anyOf` branch containing only
`enum: [null]`. DeepSeek's strict-mode documentation lists `anyOf` but does not list
`null` among supported types, and the provider requires each branch to declare a
supported type. The replacement adapter therefore uses the reserved string
`__MICEPLAN_NULL__` only as a wire representation for the seven nullable operation
fields. It decodes that sentinel to JSON null and then validates the candidate locally
against the original, unmodified Draft 2020-12 LayoutEditIR schema.

This is a reversible provider-compatibility encoding, not a change to the benchmark,
prompts, requests, runtime gate, or oracle. The replacement run must use a new run ID.
The original eight-call qualification criteria remain unchanged. This provider-specific
encoding must be disclosed as a limitation in any Kimi–DeepSeek comparison.

Official strict-mode reference accessed 2026-07-21:
<https://api-docs.deepseek.com/guides/tool_calls/>

## Second provider-contract failure

The replacement run,
`model-selection-deepseek-v4-pro-nullsentinel-v2-2026-07-21`, also stopped before
model generation. DeepSeek accepted the revised schema but returned HTTP 400 because
thinking mode does not support the forced `tool_choice` used to require the strict IR
function. The error is retained in that run's append-only log.

For the next development-only run, thinking is explicitly disabled while the forced
strict function tool is retained. This prioritizes a provider-enforced, parseable IR
contract over optional hidden reasoning. DeepSeek's official thinking-mode guide states
that `{"thinking":{"type":"disabled"}}` is the supported OpenAI-format toggle. No
request, prompt, schema semantics, output budget, or qualification criterion changes.
The next attempt must again use a new run ID.

Official thinking-mode reference accessed 2026-07-21:
<https://api-docs.deepseek.com/guides/thinking_mode/>
