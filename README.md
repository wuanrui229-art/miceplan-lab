# MICEPlan-Lab

**Separating Containment from Repair: A Cross-Model Evaluation of Deterministic Validation in LLM Layout Editing**

Research by **Anrui Wu**, Macau University of Science and Technology.

MICEPlan-Lab studies two distinct questions: whether deterministic validation contains rule-invalid layout edits, and whether feedback helps a language model repair them. It includes an independent geometry/intent adjudicator, frozen bilingual tasks, recorded model responses, and reproducible analyses.

## Evidence in this repository

The [reproducibility supplement](supplement/README.md) contains the original frozen inputs, source code and six formal runs for three recorded endpoints. Each endpoint has 216 natural-track jobs and 210 seeded-recovery jobs. The provider/model labels describe the captured experiments, not current model availability.

The natural-track gate contained all 14 observed rule violations. On seeded tasks, OpenAI rule-guided repair produced 166 successes versus 48 for blind retry (118 additional successes out of 210 cases). This endpoint-specific result does not establish a universal repair benefit. See the supplement for the other endpoints, intent checks and limitations.

## Reproduce recorded counts offline

Python 3.11 or later:

```bash
cd supplement
python -m venv .venv
source .venv/bin/activate
python -m pip install -r paper/experiments/miceplan_lab/requirements.txt
PYTHONPATH=paper/experiments:paper/system python paper/experiments/verify_reported_results.py
```

No API key is required for offline verification. See the supplement for implementation tests, journal checks and statistical recomputation. Live execution is a separate operation that requires credentials and incurs provider charges.

## Relationship to MICECAD

[MICECAD AI Booth Planning](https://github.com/wuanrui229-art/micecad-ai-booth-planning) is the interactive product prototype. This repository presents the separate research harness and evidence; the browser prototype is not itself the evaluated research system.

## Provenance and interpretation

The `supplement/` directory preserves the supplied reproducibility package, including its original checksum manifest. Some nested development notes describe earlier milestones; the supplement's top-level README describes the included final six-run package. The GitHub packaging adds this navigation page without rewriting captured experimental results.

These are bounded synthetic 2D editing experiments. Results do not establish professional CAD performance, regulatory compliance, downstream user safety or current provider behavior. Manuscript publication status should be checked against the author's current publication record.
