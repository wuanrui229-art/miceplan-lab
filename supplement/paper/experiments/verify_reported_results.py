from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "paper" / "data" / "miceplan_lab_v1_1"
RUNS = DATA / "runs"

NATURAL = {
    "Kimi": "formal-natural-kimi-v1-2",
    "DeepSeek": "formal-natural-deepseek-v1-2",
    "OpenAI": "formal-natural-openai-v1-2-extension",
}
SEEDED = {
    "Kimi": "formal-seeded-kimi-v1-2",
    "DeepSeek": "formal-seeded-deepseek-v1-2",
    "OpenAI": "formal-seeded-openai-v1-2-extension",
}


def payloads(path: Path) -> list[dict]:
    values: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                values.append(row.get("payload", row))
    return values


def require(label: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, observed {actual!r}")
    print(f"PASS  {label}: {actual}")


def check_natural() -> None:
    expected = {
        "Kimi": {"llm_rioer": 4, "block_rioer": 0, "llm_sts": 94, "block_sts": 94},
        "DeepSeek": {"llm_rioer": 9, "block_rioer": 0, "llm_sts": 51, "block_sts": 51},
        "OpenAI": {"llm_rioer": 1, "block_rioer": 0, "llm_sts": 66, "block_sts": 66},
    }
    for model, run_name in NATURAL.items():
        rows = payloads(RUNS / run_name / "outcomes.jsonl")
        by_policy = {
            policy: [row for row in rows if row["policy"] == policy]
            for policy in ("LLM_ONLY", "VALIDATE_AND_BLOCK")
        }
        require(f"{model} Track N LLM-only jobs", len(by_policy["LLM_ONLY"]), 216)
        require(f"{model} Track N Block jobs", len(by_policy["VALIDATE_AND_BLOCK"]), 216)
        observed = {
            "llm_rioer": sum(
                bool(row["offline_evaluation"]["rule_invalid_operation_exposed"])
                for row in by_policy["LLM_ONLY"]
            ),
            "block_rioer": sum(
                bool(row["offline_evaluation"]["rule_invalid_operation_exposed"])
                for row in by_policy["VALIDATE_AND_BLOCK"]
            ),
            "llm_sts": sum(
                bool(row["offline_evaluation"]["safe_task_success"])
                for row in by_policy["LLM_ONLY"]
            ),
            "block_sts": sum(
                bool(row["offline_evaluation"]["safe_task_success"])
                for row in by_policy["VALIDATE_AND_BLOCK"]
            ),
        }
        for metric, value in expected[model].items():
            require(f"{model} Track N {metric}", observed[metric], value)

    feasible = json.loads(
        (DATA / "formal_feasible_deferral_statistics_3model.json").read_text(
            encoding="utf-8"
        )
    )["models"]
    for model, expected_added in {"Kimi": 4, "DeepSeek": 110, "OpenAI": 2}.items():
        require(
            f"{model} newly deferred gold-executable jobs",
            feasible[model]["added_feasible_deferrals"],
            expected_added,
        )


def check_seeded() -> None:
    expected = {
        "Kimi": {"rule_success": 171, "blind_success": 177},
        "DeepSeek": {"rule_success": 139, "blind_success": 136},
        "OpenAI": {"rule_success": 166, "blind_success": 48},
    }
    for model, run_name in SEEDED.items():
        rows = payloads(RUNS / run_name / "outcomes.jsonl")
        rule = [row for row in rows if row["policy"] == "SEEDED_VALIDATE_AND_REPAIR"]
        blind = [
            row for row in rows if row["policy"] == "SEEDED_VALIDATE_AND_BLIND_RETRY"
        ]
        require(f"{model} Track S Rule jobs", len(rule), 210)
        require(f"{model} Track S Blind jobs", len(blind), 210)
        require(
            f"{model} Track S Rule safe successes",
            sum(bool(row["offline_evaluation"]["safe_task_success"]) for row in rule),
            expected[model]["rule_success"],
        )
        require(
            f"{model} Track S Blind safe successes",
            sum(bool(row["offline_evaluation"]["safe_task_success"]) for row in blind),
            expected[model]["blind_success"],
        )

        if model == "OpenAI":
            rule_actions = Counter(row["final_action"] for row in rule)
            blind_actions = Counter(row["final_action"] for row in blind)
            require("OpenAI Rule final DEFER", rule_actions["DEFER"], 38)
            require("OpenAI Rule final EXPOSE", rule_actions["EXPOSE"], 172)
            require("OpenAI Blind final DEFER", blind_actions["DEFER"], 162)
            require("OpenAI Blind final EXPOSE", blind_actions["EXPOSE"], 48)
            semantic_exposures = sum(
                row["final_action"] == "EXPOSE"
                and row["offline_evaluation"]["oracle"]["status"] == "PASS"
                and not bool(row["offline_evaluation"]["intent_correct"])
                for row in rule
            )
            require("OpenAI Rule geometry-PASS intent-incorrect exposures", semantic_exposures, 6)


def main() -> None:
    check_natural()
    check_seeded()
    print("PASS: all manuscript-level count checks matched the captured formal outcomes.")


if __name__ == "__main__":
    main()

