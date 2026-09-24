# Kimi K2.7 HighSpeed Selection Result — 2026-07-21

## Decision

`kimi-k2.7-code-highspeed` is selected for the complete 36-request development pilot.
The decision concerns serving feasibility only and is excluded from held-out effect
estimates.

## Frozen-gate result

| Requirement | Threshold | Observed | Result |
| --- | ---: | ---: | --- |
| Completed initial calls | 8/8 | 8/8 | Pass |
| Infrastructure-error records | 0 | 0 | Pass |
| Schema-valid IR | 8/8 | 8/8 | Pass |
| Length truncations | 0 | 0 | Pass |
| Median latency | <= 24,915 ms | 10,600 ms | Pass |
| Median total tokens | <= 4,199 | 3,489.5 | Pass |

The standard-tier selection median was 49,831 ms and 3,359 total tokens. HighSpeed was
approximately 4.7 times faster with a 3.9% higher median token count. Its eight calls
used 14,758 prompt tokens, including 1,536 cache-hit tokens, and 14,864 completion
tokens. At the provider's 2026-07-21 HighSpeed rates, the estimated cost was USD 0.1446
before tax.

## Limited diagnostic

Across the four development requests, both initial prompt arms produced three
intent-correct, independently valid edits and one correct explicit defer. This is a
small engineering diagnostic, not evidence about policy effects.

## Evidence boundary

The model family, prompt content, strict schema, requests, repair limit, runtime gate,
and oracle are unchanged. Only the provider serving tier differs. No held-out request
was called or inspected.
