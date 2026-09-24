from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "paper" / "data" / "miceplan_lab_v1_1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_dataset_manifest() -> list[str]:
    manifest = json.loads((DATASET / "manifest.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    search_roots = [DATASET, DATASET / "schemas", DATASET / "prompts"]
    for name, metadata in manifest["files"].items():
        matches = [root / name for root in search_roots if (root / name).exists()]
        if len(matches) != 1:
            failures.append(f"{name}: expected one tracked file, found {len(matches)}")
            continue
        observed = sha256(matches[0])
        if observed != metadata["sha256"]:
            failures.append(f"{name}: hash mismatch")
    return failures


def verify_protocol_manifest() -> list[str]:
    manifest = json.loads((DATASET / "protocol_manifest.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    for item in manifest["files"]:
        path = ROOT / item["path"]
        if not path.exists():
            failures.append(f"{item['path']}: missing")
        elif sha256(path) != item["sha256"]:
            failures.append(f"{item['path']}: hash mismatch")
    return failures


def main() -> None:
    failures = verify_protocol_manifest() + verify_dataset_manifest()
    if failures:
        raise SystemExit("\n".join(failures))
    print("MICEPlan-Lab protocol and dataset manifests verified.")


if __name__ == "__main__":
    main()
