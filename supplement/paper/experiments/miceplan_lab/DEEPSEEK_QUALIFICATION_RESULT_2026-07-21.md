# DeepSeek V4 Pro Development Qualification Result — 2026-07-21

## Outcome

`deepseek-v4-pro` **passed** the pre-specified development qualification gate in
non-thinking strict-tool mode.

- Initial calls recorded: 8/8;
- locally schema-valid LayoutEditIR outputs: 8/8;
- length truncations: 0;
- infrastructure-error records in the successful run: 0;
- median total tokens per call: 2,777;
- median latency: 6,035 ms;
- total observed usage: 18,734 prompt, 3,210 completion, and 4,608 provider-reported
  cached tokens;
- estimated unique API cost: USD 0.00895.

The successful append-only run is
`model-selection-deepseek-v4-pro-strict-nonthinking-v3-2026-07-21`. No held-out
request ID appears in its manifest, calls, or outcomes.

## Development behavior, not a scientific result

On the four fixed requests, the base arm safely completed two edits, correctly deferred
one ambiguous request, and exposed one unsupported candidate. The constraint-in-prompt
arm completed the same two edits and defer but produced an overlapping placement for the
remaining request. The deterministic gate contained both unsafe candidates under the
validation policies. With only four selected development requests, these observations
are diagnostics and must not be reported as held-out effectiveness estimates.

## Provider compatibility record

Two earlier requests failed before model generation and are retained rather than
deleted. The first exposed DeepSeek strict mode's lack of a usable JSON null type in
this schema; the second showed that thinking mode rejects a forced `tool_choice`.
The working adapter therefore:

1. uses an explicit reserved wire sentinel for nullable operation fields and decodes it
   before validation against the unchanged frozen IR schema;
2. disables thinking;
3. retains the forced provider-enforced strict tool call;
4. validates every decoded candidate locally.

This output-interface difference from Kimi is a disclosed cross-provider limitation.
The result qualifies DeepSeek as the second model family required by protocol v1.2; it
does not authorize or constitute formal held-out execution.

