# K2.7 32K Output-Budget Qualification Result — 2026-07-21

## Decision

The 32,768-token K2.7 HighSpeed profile passes the pre-specified development
qualification and may be used for a complete replacement development run.

## Result

| Requirement | Observed | Result |
| --- | ---: | --- |
| Completed calls | 8/8 | Pass |
| Schema-valid IR | 8/8 | Pass |
| Length truncations | 0 | Pass |
| Infrastructure-error records | 0 | Pass |
| Calls above 16,384 completion tokens | 0 | Pass |

Completion-token counts were 1,534, 1,707, 3,100, 3,321, 4,244, 4,402, 9,720,
and 9,892. The two values above 8,192 confirm that the former limit would have
truncated otherwise successful responses. Median latency was 20.264 seconds and
median total tokens were 5,634.5.

All prompt, schema, policy, gate, oracle, benchmark, and metric files remain unchanged.
No held-out request was called.
