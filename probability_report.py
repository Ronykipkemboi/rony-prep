#!/usr/bin/env python3
"""
Probability Report Generator
Analyzes topic frequency across KCSE Math papers to support predictive study strategy.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_year_from_name(path: Path) -> Optional[int]:
    match = re.search(r"(20\d{2})", path.stem)
    return int(match.group(1)) if match else None


def _parse_paper_from_name(path: Path) -> Optional[int]:
    match = re.search(r"paper[\s_-]?([12])", path.stem, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _parse_section(value: Optional[str]) -> str:
    if not value:
        return "All Sections"
    cleaned = value.strip()
    return cleaned or "All Sections"


def _parse_topic(value: Optional[str]) -> str:
    if not value:
        return "Unknown"
    cleaned = value.strip()
    return cleaned or "Unknown"


def load_extractions(input_path: Path) -> list[dict]:
    if input_path.is_file():
        return [json.loads(input_path.read_text(encoding="utf-8"))]

    if not input_path.is_dir():
        raise FileNotFoundError(f"Input path not found: {input_path}")

    extractions: list[dict] = []
    for file_path in sorted(input_path.glob("*.json")):
        if file_path.name == "batch_summary.json":
            continue
        extractions.append(json.loads(file_path.read_text(encoding="utf-8")))
    return extractions


def extract_year(data: dict, fallback_name: Optional[str]) -> Optional[int]:
    metadata = data.get("extraction_metadata", {})
    year = metadata.get("year")
    if isinstance(year, int):
        return year
    if isinstance(year, str) and year.isdigit():
        return int(year)
    if fallback_name:
        return _parse_year_from_name(Path(fallback_name))
    return None


def extract_paper(data: dict, fallback_name: Optional[str]) -> Optional[int]:
    metadata = data.get("extraction_metadata", {})
    paper = metadata.get("paper")
    if isinstance(paper, int):
        return paper
    if isinstance(paper, str) and paper.isdigit():
        return int(paper)
    if fallback_name:
        return _parse_paper_from_name(Path(fallback_name))
    return None


def classify_probability(rate: float) -> str:
    if rate >= 0.7:
        return "High"
    if rate >= 0.4:
        return "Medium"
    return "Low"


def build_report(
    extractions: Iterable[dict],
    *,
    start_year: int,
    end_year: int,
) -> dict:
    if end_year < start_year:
        raise ValueError("end_year must be greater than or equal to start_year")

    topic_years: dict[tuple[str, str, str], set[int]] = {}
    years_with_data: set[int] = set()
    total_range_years = end_year - start_year + 1

    for data in extractions:
        fallback_name = data.get("extraction_metadata", {}).get("source_file")
        year = extract_year(data, fallback_name)
        paper = extract_paper(data, fallback_name)
        if year is None or year < start_year or year > end_year:
            continue
        years_with_data.add(year)
        paper_label = f"Paper {paper}" if paper in {1, 2} else "Paper Unknown"
        for question in data.get("questions", []):
            topic = _parse_topic(question.get("topic"))
            section = _parse_section(question.get("section"))
            topic_years.setdefault((topic, section, paper_label), set()).add(year)

    summaries: list[dict] = []
    for (topic, section, paper_label), years in topic_years.items():
        rate = (len(years) / total_range_years) if total_range_years else 0.0
        probability = classify_probability(rate)
        summary = (
            f"{topic} has appeared in {rate:.0%} of {paper_label} {section} papers "
            f"across {start_year}-{end_year}; Probability for this year: {probability}."
        )
        summaries.append(
            {
                "topic": topic,
                "section": section,
                "paper": paper_label,
                "appearance_rate": round(rate, 3),
                "years_appeared": sorted(years),
                "probability": probability,
                "summary": summary,
            }
        )

    summaries.sort(key=lambda item: item["appearance_rate"], reverse=True)
    return {
        "generated_at": _now_iso(),
        "range": {
            "start_year": start_year,
            "end_year": end_year,
            "intended_years": list(range(start_year, end_year + 1)),
            "years_with_data": sorted(years_with_data),
            "total_years_in_range": total_range_years,
            "total_years_with_data": len(years_with_data),
        },
        "topics": summaries,
    }


def print_report(report: dict) -> None:
    print("\n=== Probability Report ===")
    if not report["topics"]:
        print("No topic data available for the selected range.")
        return

    for item in report["topics"]:
        print(f"- {item['summary']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a probability report from extracted KCSE math questions.",
    )
    parser.add_argument("input_path", help="Directory of extraction JSONs or a single JSON file")
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument("--output", help="Optional path to save report JSON")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input_path)
    try:
        extractions = load_extractions(input_path)
        report = build_report(extractions, start_year=args.start_year, end_year=args.end_year)
    except Exception as exc:
        print(f"Error generating report: {exc}", file=sys.stderr)
        return 1

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Report saved to: {output_path}")

    print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
