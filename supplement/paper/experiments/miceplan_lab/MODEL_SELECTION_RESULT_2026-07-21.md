# MICEPlan-Lab Development Model-Selection Result — 2026-07-21

## Decision

`kimi-k2.7-code` is the provisional model for the 36-request development pilot.
This is an engineering choice, not a held-out scientific result. The formal model
configuration remains unfrozen until the complete development split and its failure
audit are finished.

## Pre-specified gate result

| Configuration | Expected calls | Recorded calls | Schema-valid | Length truncations | Infrastructure errors | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `kimi-k3`, low reasoning | 8 | 0 | 0/8 | 0 | 1 | Fail |
| `kimi-k2.7-code` | 8 | 8 | 8/8 | 0 | 0 | Pass |

K3 returned `engine_overloaded_error` on all three bounded infrastructure attempts for
the first scheduled development request, so the run stopped without sampling the
remaining requests. K2.7 completed all eight initial calls. Its median latency was
49.831 seconds and its median total-token count was 3,359.

## Development-only diagnostic

The four-request sample is too small for an empirical claim, but it verifies that the
planned conditions can produce informative contrasts. On `task-0001-en`, the base
prompt placed a 3 m by 3 m booth at `(33, 20)` in an L-shaped hall. That rectangle lies
outside the hall polygon. Both the runtime gate and the independently implemented
Shapely oracle classified the candidate as a boundary failure. The validation
conditions blocked it. The constraint-in-prompt arm independently placed the booth at
`(35, 11)`, which passed the oracle. Two other requests passed under both initial arms,
and the deliberately ambiguous request produced a clarification state that gated
policies deferred rather than exposing.

This observation is retained only as a prompt-and-runner diagnostic. It does not enter
the paper's held-out estimates.

## Recorded token cost and expansion estimate

The eight K2.7 calls used 14,758 input tokens, including 4,178 cache-hit tokens, and
12,940 output tokens. The provider price listed on 2026-07-21 was USD 0.19 per million
cache-hit input tokens, USD 0.95 per million cache-miss input tokens, and USD 4.00 per
million output tokens:

<https://platform.kimi.ai/docs/pricing/chat-k27-code.md>

The estimated cost of the selection run is therefore USD 0.0626 before tax. Scaling
the observed token mix gives the following planning bounds for one 36-request
development replicate:

| Planning case | Calls | Unbuffered estimate | With 25% repair-prompt buffer |
| --- | ---: | ---: | ---: |
| Two initial arms only | 72 | USD 0.56 | USD 0.70 |
| 25% base failures; both repair policies exhaust three attempts | 126 | USD 0.99 | USD 1.23 |
| Every base output fails; all repairs exhaust the bound | 288 | USD 2.25 | USD 2.82 |

At the observed median latency, the corresponding serial runtimes are approximately
1.0, 1.7, and 4.0 hours. Infrastructure retries can make the tail longer. These are
budget estimates, not performance results.

## Next gate

Run all 36 development requests with K2.7, one replicate, both initial arms, and up to
three semantic repairs for each matched repair policy. Then audit schema failures,
intent errors, gate/oracle disagreement, repeated violations, regressions, repair
yield, latency, and token use. Only after that audit may prompts and the K2.7 formal
configuration be frozen.
