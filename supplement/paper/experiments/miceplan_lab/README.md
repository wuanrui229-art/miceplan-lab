# MICEPlan-Lab v1.1 Experiment Harness

This package implements the frozen MICEPlan-Lab validation–recovery protocol. The
current milestone contains the benchmark generator, JSON Schemas, independent Shapely
oracle, integrity audit, blinded author-review packet, five-condition policy runner,
OpenAI-compatible live adapter, hash-chained append-only journal, safe resume logic,
and descriptive metric recomputation. Development-only provider connectivity checks
have been executed, but no held-out or formal MICEPlan-Lab model run has started.

## Environment

```bash
python3 -m venv .venv-miceplan-lab
.venv-miceplan-lab/bin/python -m pip install -r paper/experiments/miceplan_lab/requirements.txt
```

## Rebuild and audit the benchmark

```bash
PYTHONPATH=paper/experiments .venv-miceplan-lab/bin/python -m miceplan_lab.generate_benchmark
PYTHONPATH=paper/experiments .venv-miceplan-lab/bin/python -m miceplan_lab.audit_benchmark
PYTHONPATH=paper/experiments .venv-miceplan-lab/bin/python -m miceplan_lab.verify_integrity
```

The repaired generator writes 8 scenes, 90 semantic tasks, and 180 bilingual requests
to `paper/data/miceplan_lab_v1_1/`; the rejected v1 benchmark and its preliminary runs
remain unchanged for provenance. The v1.1 audit validates every record against JSON
Schema, checks split leakage and balance, evaluates hidden feasible witnesses, requires
every deterministic probe to trigger exactly one target rule, checks natural DEFER
wording and entrance ambiguity evidence, rejects no-op C3 witnesses, creates a blinded
author-review packet, and updates content hashes.

After the complete bilingual surface-form packet has been checked, finalize the exact
reviewed dataset revision with:

```bash
PYTHONPATH=paper/experiments .venv-miceplan-lab/bin/python \
  -m miceplan_lab.finalize_surface_review
```

This records internal benchmark QA only. It must not be reported as practitioner or
CAD-domain expert validation.

## Run tests

```bash
PYTHONPATH=paper/experiments:paper/system .venv-miceplan-lab/bin/python \
  -m unittest discover -s paper/experiments/miceplan_lab/tests -v
```

The runtime differential test imports the existing MICEPlan runtime validator only for
comparison. The gold oracle itself does not import the runtime solver or geometry code.

`policy_runner.py` contains the five-condition state machine. Its tests use a scripted
adapter so rule-guided repair and blind retry can be compared without a provider call.

The 12-request smoke test deliberately interrupts execution and then resumes from the
append-only journal. It verifies that already completed semantic calls are reused rather
than sampled again, that exact base outputs are shared by the three validation policies,
and that all 60 policy outcomes can be reconstructed.

## Prepare or run the development pilot

The command is safe by default: without `--execute`, it prints the development-only
plan and makes no files and no provider calls.

```bash
PYTHONPATH=paper/experiments:paper/system .venv-miceplan-lab/bin/python \
  -m miceplan_lab.run_development --limit 36
```

After the development configuration has been checked, the explicit execution form is:

```bash
PYTHONPATH=paper/experiments:paper/system .venv-miceplan-lab/bin/python \
  -m miceplan_lab.run_development --limit 36 --execute
```

Use `--model <model-id>` to test a model available to the configured Kimi account.
Provider-specific fixed decoding controls for K2.6, K2.7 Code, and K3 are recorded in
the immutable run manifest. See `MODEL_SELECTION_NOTE_2026-07-20.md` before choosing a
formal model.

Run directories are written beneath `paper/data/miceplan_lab_v1_1/runs/`. See
`RUN_LOG_SPEC.md` for the audit and resume contract. Recompute descriptive metrics from
one completed run with:

```bash
PYTHONPATH=paper/experiments:paper/system .venv-miceplan-lab/bin/python \
  -m miceplan_lab.summarize_run paper/data/miceplan_lab_v1_1/runs/<run-id>
```

## Frozen formal execution

`formal_run.py` is the only entry point for the v1.2 held-out experiment. Its default
mode performs all integrity checks, constructs the four frozen model × track schedules,
and writes a zero-call rehearsal record. It does not send a request:

```bash
PYTHONPATH=paper/experiments:paper/system .venv-miceplan-lab/bin/python \
  -m miceplan_lab.formal_run
```

The frozen schedule contains 216 natural-incidence jobs and 210 seeded-recovery jobs
per model. Formal execution accepts exactly one track and one provider at a time and
requires the explicit `--execute` flag. The runner rejects stale source hashes,
development/test mixing, non-frozen model identifiers, incomplete surface-form QA, or
an unfrozen protocol.

Do not add `--execute` until the author has approved the held-out data transfer and
provider cost for that single phase.

## Research safeguards

- benchmark truth is never included in generation or repair prompts;
- the independent oracle labels candidates after policy execution;
- `UNKNOWN` tasks have no hidden edit answer and require defer/clarification;
- generated stress strata do not pre-assume that an LLM will fail;
- a provider request requires the explicit `--execute` flag;
- the development command selects no held-out request;
- an audit failure prevents a formal run rather than silently dropping a task.
