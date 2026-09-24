from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path


PAPER = Path(__file__).resolve().parents[1]
BIB = PAPER / "references.bib"
OUTPUT = PAPER / "experiments" / "results" / "reference_verification_2026-07-16.json"


def normalized(value: str) -> str:
    value = value.replace("{", "").replace("}", "")
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def entries() -> list[dict[str, str]]:
    text = BIB.read_text(encoding="utf-8")
    records: list[dict[str, str]] = []
    for match in re.finditer(r"@(\w+)\{([^,]+),(.*?)(?=\n\}\s*(?:\n@|\Z))", text, re.S):
        fields = {
            key.lower(): value.strip()
            for key, value in re.findall(r"^\s*(\w+)\s*=\s*\{(.*?)\}\s*,?\s*$", match.group(3), re.M)
        }
        records.append({"key": match.group(2), **fields})
    return records


def crossref(doi: str) -> dict:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "MICEPlan-reference-audit/1.0 (mailto:research-audit@example.com)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))["message"]


def main() -> None:
    results = []
    for index, record in enumerate(entries(), start=1):
        doi = record.get("doi", "")
        item = {"key": record["key"], "doi": doi, "bib_title": record.get("title", "")}
        try:
            metadata = crossref(doi)
            crossref_title = (metadata.get("title") or [""])[0]
            bib_normalized = normalized(item["bib_title"])
            crossref_normalized = normalized(crossref_title)
            score = SequenceMatcher(None, bib_normalized, crossref_normalized).ratio()
            short_title_compatible = (
                len(crossref_normalized) >= 8 and crossref_normalized in bib_normalized
            )
            years = []
            for field in ("published-print", "published-online", "issued", "created"):
                parts = metadata.get(field, {}).get("date-parts", [])
                if parts and parts[0]:
                    years.append(parts[0][0])
            item.update({
                "resolves": True,
                "crossref_title": crossref_title,
                "title_similarity": score,
                "short_title_compatible": short_title_compatible,
                "bib_year": int(record.get("year", "0") or 0),
                "crossref_years": sorted(set(years)),
                "container_title": (metadata.get("container-title") or [""])[0],
                "publisher": metadata.get("publisher", ""),
                "title_match": score >= 0.92 or short_title_compatible,
            })
        except Exception as exc:
            item.update({"resolves": False, "error": f"{type(exc).__name__}: {exc}"})
        results.append(item)
        print(f"[{index:02d}] {record['key']} resolves={item['resolves']} match={item.get('title_match')}", flush=True)
        time.sleep(0.15)

    report = {
        "checked": len(results),
        "resolved": sum(item["resolves"] for item in results),
        "title_matches": sum(item.get("title_match", False) for item in results),
        "all_resolved_and_matched": all(item["resolves"] and item.get("title_match") for item in results),
        "source": "Crossref REST API",
        "access_date": "2026-07-16",
        "items": results,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("checked", "resolved", "title_matches", "all_resolved_and_matched")}, indent=2))


if __name__ == "__main__":
    main()
