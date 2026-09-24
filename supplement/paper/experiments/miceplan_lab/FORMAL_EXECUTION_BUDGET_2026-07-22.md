# MICEPlan-Lab v1.2 Formal Execution Budget

**Status:** planning estimate only; zero held-out responses observed.  
**Rehearsal:** `formal_zero_call_rehearsal_2026-07-22.json` passed with zero model
calls.  
**Price date:** 2026-07-21; provider taxes and later price changes are excluded.

## Frozen workload

| Phase | Jobs | Policy outcomes | Minimum calls | Maximum calls |
| --- | ---: | ---: | ---: | ---: |
| Kimi Track N: natural incidence | 216 | 1,080 | 432 | 1,728 |
| Kimi Track S: seeded recovery | 210 | 630 | 420 | 1,260 |
| DeepSeek Track N: natural incidence | 216 | 1,080 | 432 | 1,728 |
| DeepSeek Track S: seeded recovery | 210 | 630 | 420 | 1,260 |
| **Total** | **852** | **3,420** | **1,704** | **5,976** |

The minimum assumes no natural candidate enters repair and every standardized seeded
failure is recovered on the first attempt in both repair arms. The maximum assumes
every bounded repair arm uses all three attempts. These are execution bounds, not
predictions of scientific outcomes.

## Evidence-based planning estimate

Existing development calls give the following observed averages:

- Kimi natural-generation call: USD 0.01691 and 11.40 seconds (`n=72`);
- Kimi seeded-repair call: USD 0.03450 and 20.13 seconds (`n=24`);
- DeepSeek qualified initial call: USD 0.00112 and 5.68 seconds (`n=8`).

Using those development averages, the four phases are expected to cost about **USD
22.75** if natural repair is rare and seeded repair normally succeeds on the first
attempt. A conservative all-attempt planning ceiling is approximately **USD 102**,
with a two-times allowance for DeepSeek repair calls because only its initial-call cost
has been observed. These values are budgeting estimates and must not appear as formal
experimental results.

Sequential wall-clock time is roughly five hours near the minimum. Tail latency and
retries can extend it substantially. Every call and policy outcome is append-only and
hash chained, so each phase may be stopped and safely resumed.

## Required execution order

1. Kimi Track N — establishes natural invalidity and containment incidence.
2. Kimi Track S — measures conditional recovery and cost on standardized failures.
3. DeepSeek Track N — model-family robustness check.
4. DeepSeek Track S — model-family robustness check for recovery.

Only one phase is authorized at a time. Before each phase, record the provider balance,
confirm that sending the held-out synthetic requests to that provider is permitted,
and preserve the generated run manifest. A phase must never be silently downsized after
results are visible; if cost prevents continuation, report the stopped design and the
completed denominator transparently.

## Frozen formal commands

The following commands are intentionally documented without `--execute`. Adding that
flag sends held-out requests and therefore requires explicit author approval for the
individual phase:

```text
python -m miceplan_lab.formal_run --track natural --provider kimi
python -m miceplan_lab.formal_run --track seeded --provider kimi
python -m miceplan_lab.formal_run --track natural --provider deepseek
python -m miceplan_lab.formal_run --track seeded --provider deepseek
```
