from __future__ import annotations

import copy
import json
import sys
from datetime import date as real_date

from miceplan_lab import formal_run


RUN_ID = "formal-seeded-kimi-v1-2"


class ResumeDate:
    frozen: real_date

    @classmethod
    def today(cls) -> real_date:
        return cls.frozen


def validate_manifest_for_resume() -> real_date:
    """Allow a cross-date resume only when access_date is the sole difference."""
    run_directory = formal_run.RUNS / RUN_ID
    manifest_path = run_directory / "run_manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("The original formal Track S manifest is missing")

    existing = json.loads(manifest_path.read_text(encoding="utf-8"))
    requested = formal_run.build_plan("seeded", "kimi", RUN_ID)
    aligned = copy.deepcopy(requested)
    aligned["access_date"] = existing.get("access_date")
    if aligned != existing:
        raise RuntimeError(
            "Resume refused: a field other than access_date differs from the frozen manifest"
        )
    return real_date.fromisoformat(str(existing["access_date"]))


def main() -> None:
    formal_run.load_local_env(formal_run.ROOT / "paper" / "system" / ".env")
    ResumeDate.frozen = validate_manifest_for_resume()
    formal_run.date = ResumeDate
    sys.argv = [
        "resume_formal_kimi_track_s.py",
        "--track",
        "seeded",
        "--provider",
        "kimi",
        "--run-id",
        RUN_ID,
        "--execute",
    ]
    print("resume_manifest_check: PASS (only access_date was aligned)", flush=True)
    formal_run.main()


if __name__ == "__main__":
    main()
