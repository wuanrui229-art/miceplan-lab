# K2.7 Output-Budget Development Revision — 2026-07-21

**Frozen before revised-budget calls:** 2026-07-21  
**Scope:** development configuration repair; no held-out calls.

## Observed development failure

The completed 36-request HighSpeed development run made 72 initial calls. Three calls
(4.17%) ended with `finish_reason=length`, 8,192 completion tokens, 8,191 recorded
reasoning tokens, empty response content, and no parseable IR. The affected development
requests were:

- `task-0001-en`, base prompt;
- `task-0021-zh`, base prompt;
- `task-0081-zh`, constraint-in-prompt.

The raw records are retained under
`kimi-k27-highspeed-development-v11-2026-07-21`. This run remains a development
diagnostic and is not overwritten.

## Provider constraint

Moonshot's K2.7 documentation states that K2.7 Code does not support non-thinking mode,
uses fixed temperature 1.0, and has a default `max_tokens` value of 32,768:

<https://platform.kimi.ai/docs/guide/kimi-k2-7-code-quickstart>

The experiment configuration therefore changes only `max_tokens`, from 8,192 to the
documented default 32,768. Prompts, schema, request content, policies, runtime gate,
oracle, and metrics do not change.

## Frozen qualification check

Run both initial arms on the three truncation cases plus control `task-0036-en`, one
replicate, zero semantic repairs: eight calls. The revised budget is eligible only if:

1. all 8 calls complete;
2. all 8 return schema-valid IR;
3. zero calls end with `finish_reason=length`;
4. zero infrastructure-error records occur.

If the check passes, rerun all 36 development requests under a new run ID. If any
qualification call consumes more than 16,384 completion tokens, record the tail and
re-estimate formal cost before model freeze even if the call completes.
