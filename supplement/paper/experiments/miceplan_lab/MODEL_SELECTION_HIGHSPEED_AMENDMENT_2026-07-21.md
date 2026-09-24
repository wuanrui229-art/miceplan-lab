# Kimi K2.7 HighSpeed Selection Amendment — 2026-07-21

**Frozen before HighSpeed calls:** 2026-07-21  
**Scope:** development engineering only; no held-out request may be used.

## Motivation

The standard `kimi-k2.7-code` configuration passed the original four-request quality
gate. During the subsequently frozen 36-request development launch, its first stored
call required three infrastructure attempts and 256.713 seconds. The next call failed
after three 90-second read timeouts. At that tail latency, the pre-specified formal
experiment would be operationally impractical and highly exposed to provider drift.

Moonshot documents `kimi-k2.7-code-highspeed` as the same K2.7 Code model served at a
higher output speed, with exactly twice the listed cache-hit, cache-miss, and output
token prices. This amendment tests the serving tier; it does not change prompts,
schema, policies, requests, or metrics.

Official source accessed on 2026-07-21:

<https://platform.kimi.ai/docs/pricing/chat-k27-code.md>

## Frozen requests and calls

Use the same four pre-specified development requests as the original selection:

- `task-0001-en`
- `task-0021-zh`
- `task-0036-en`
- `task-0086-zh`

Run one replicate, both initial prompt arms, strict LayoutEditIR schema, and zero
semantic repairs: eight expected calls. No response from the 36-request run is used as
a test item or tuning target.

## Pre-specified HighSpeed eligibility rule

HighSpeed replaces the standard serving tier for the complete development pilot only
if it satisfies all of the following:

1. 8/8 expected calls recorded;
2. zero infrastructure-error records;
3. 8/8 schema-valid LayoutEditIR outputs;
4. zero length truncations;
5. median latency no greater than 24,915 ms, half the standard-tier selection median;
6. median total tokens no greater than 4,199, a 25% allowance over the standard-tier
   selection median of 3,359.

The latency threshold requires the speed gain to offset the exact 2x token price at a
coarse planning level. If HighSpeed fails, it is not selected. Any alternative model
or provider requires another dated development-only selection record.

## Evidence boundary

This comparison determines operational feasibility only. The four-request outputs and
latencies are excluded from held-out effect estimates and paper claims about validation
or repair.
