# Reproducibility Supplement

## Paper

**Separating Containment from Repair: A Cross-Model Evaluation of Deterministic Validation in LLM Layout Editing**

This de-identified package contains the frozen benchmark inputs, prompts, schemas, six formal three-endpoint runs, append-only execution records, analysis code, tests, model-freeze records, and contemporaneous price snapshots used by the revised manuscript.

The package supports offline verification of the reported results. It does not contain provider credentials and does not require an API key for the verification steps below. A new live run would require separate credentials and may differ because proprietary endpoints can change.

## Package structure

- `paper/data/miceplan_lab_v1_1/`: requests, scenes, gold labels, standardized seeded failures, prompts, schemas, frozen manifests, six formal run directories, and derived statistical summaries.
- `paper/experiments/miceplan_lab/`: runtime gate, independent oracle, execution logic, journal integrity checks, tests, and provider adapters retained for methodological transparency.
- `paper/experiments/`: natural-track, seeded-track, cross-endpoint, and feasible-job deferral analyses.
- `paper/system/miceplan/`: deterministic geometry and layout-state implementation used by the experimental gate.
- `paper/protocol/`: evaluation protocol, post-review protocol supplement, model-freeze records, run-log specification, and price snapshots.
- `SHA256SUMS.txt`: checksums for every file in the package other than the checksum file itself.

Only the six formal held-out runs are included:

- Natural Track N: Kimi K2.7 Code HighSpeed, DeepSeek V4 Pro, and OpenAI GPT-5.6 Sol.
- Seeded Track S: the same three recorded provider endpoints.

Development runs, virtual environments, caches, credentials, and unrelated manuscript drafts are excluded.

## Environment

Python 3.11 or later is recommended. From the package root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r paper/experiments/miceplan_lab/requirements.txt
```

## One-command offline verification

The following command reads the captured formal outcomes and checks the central counts reported in the revised paper. It makes no provider calls.

```bash
PYTHONPATH=paper/experiments:paper/system python paper/experiments/verify_reported_results.py
```

Expected final line:

```text
PASS: all manuscript-level count checks matched the captured formal outcomes.
```

## Recompute the post-review analyses

These commands regenerate the three-endpoint comparison files from the captured records:

```bash
PYTHONPATH=paper/experiments:paper/system python paper/experiments/compare_formal_natural_three_models.py
PYTHONPATH=paper/experiments:paper/system python paper/experiments/compare_formal_seeded_three_models.py
PYTHONPATH=paper/experiments:paper/system python paper/experiments/analyze_feasible_deferral_three_models.py
```

The scripts use 10,000 semantic-task-cluster bootstrap replicates with fixed seeds. The generated JSON files are written to `paper/data/miceplan_lab_v1_1/`.

## Tests and journal integrity

Run the implementation tests:

```bash
PYTHONPATH=paper/experiments:paper/system python -m pytest paper/experiments/miceplan_lab/tests paper/system/tests
```

Verify the frozen protocol/dataset manifests and every append-only journal in the six formal runs:

```bash
PYTHONPATH=paper/experiments:paper/system python -m miceplan_lab.verify_integrity
python paper/experiments/verify_all_journals.py
```

## Interpretation boundary

Track N estimates observed incidence, containment, task success, and deferral on this benchmark. Track S estimates conditional recovery from standardized intent-preserving geometric failures. Track S does not estimate natural error frequency and does not represent all target-selection, unsupported-reference, missing-field, or malformed-semantic failures.

The Rule Repair versus Blind Retry contrast is package-level. Rule Repair changes both the supplied gate evidence and associated minimum-change/evidence-based deferral instructions; it is not an evidence-token-only ablation.

RIOER is a machine-confirmed rule-invalid exposure proxy. It is not a measure of downstream human review, task harm, professional acceptance, regulatory compliance, or operational safety.

## Privacy and credentials

The submission copy excludes API keys, bearer tokens, local user paths, email addresses, virtual environments, and keychain contents. Provider adapters refer only to environment-variable or keychain labels. The included model responses are recorded research outputs, not credentials.
