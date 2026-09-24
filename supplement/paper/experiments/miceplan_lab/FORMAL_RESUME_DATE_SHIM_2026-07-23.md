# Formal Kimi Track N Cross-Date Resume Record

Date: 2026-07-23  
Run ID: `formal-natural-kimi-v1-2`

The original formal run was initialized on 2026-07-22 and stopped after the provider
returned HTTP 429 for insufficient balance. When the author recharged on 2026-07-23, the
unchanged runner generated `access_date=2026-07-23`; the append-only journal correctly
refused the mismatch with the existing `access_date=2026-07-22` manifest before sending any
new request.

The frozen runner and tests were not modified. The external resume launcher:

1. builds the current requested plan;
2. substitutes the existing manifest's access date only for comparison;
3. refuses execution unless every other field is exactly equal;
4. exposes the original date to the unchanged runner for manifest reconstruction; and
5. invokes the same natural/Kimi/run-ID execution path with append-only resume enabled.

This is an operational cross-date resume correction. It does not change the model, provider,
endpoint, prompts, schema, request selection, schedule, replicate IDs, policies, repair
limit, decoding parameters, prices, source hashes, gold visibility, or expected call bounds.
