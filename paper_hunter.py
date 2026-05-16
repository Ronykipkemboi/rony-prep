#!/usr/bin/env python3
"""
KCSE Paper Hunter
Discover and download KCSE Mathematics Paper 1 and Paper 2 PDFs for predictive analysis.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
import urllib.parse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

import requests
from bs4 import BeautifulSoup

DEFAULT_START_YEAR = 2015
DEFAULT_END_YEAR = 2024
DEFAULT_PAPERS = (1, 2)
DEFAULT_OUTPUT_DIR = Path("downloads/kcse_papers")
DEFAULT_MANIFEST_PATH = Path("downloads/kcse_papers_manifest.json")
SEARCH_URL = "https://duckduckgo.com/html/"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
# Year hits are helpful, but exact paper matches should dominate and wrong-paper hits should lose hard.
YEAR_MATCH_SCORE = 3
PAPER_MATCH_SCORE = 8
OTHER_PAPER_PENALTY = 10
RESULT_TEXT_SCORE = 1
PAPER_ALTERNATES = {1: 2, 2: 1}
BAD_PDF_CONTENT_TYPES = {"text/html", "application/xhtml+xml", "text/xml", "application/xml"}


@dataclass
class PaperRecord:
    year: int
    paper: int
    query: str
    source_url: Optional[str]
    local_path: Optional[str]
    status: str
    error: Optional[str]
    discovered_at: str


@dataclass
class SearchResult:
    url: str
    text: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_query(year: int, paper: int) -> str:
    return f"KCSE Mathematics Paper {paper} {year} pdf"


def _normalize_duckduckgo_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname or ""
    if hostname in {"duckduckgo.com", "www.duckduckgo.com"} and parsed.path.startswith("/l/"):
        params = urllib.parse.parse_qs(parsed.query)
        if "uddg" in params and params["uddg"]:
            return urllib.parse.unquote(params["uddg"][0])
    return url


def fetch_search_results(session: requests.Session, query: str, max_results: int) -> list[SearchResult]:
    response = session.get(SEARCH_URL, params={"q": query}, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    links: list[SearchResult] = []
    for anchor in soup.select("a.result__a"):
        href = anchor.get("href")
        if not href:
            continue
        links.append(SearchResult(url=_normalize_duckduckgo_url(href), text=anchor.get_text(" ", strip=True)))

    if not links:
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if href.startswith("http"):
                links.append(SearchResult(url=_normalize_duckduckgo_url(href), text=anchor.get_text(" ", strip=True)))

    deduped: list[SearchResult] = []
    seen = set()
    for result in links:
        if result.url in seen:
            continue
        seen.add(result.url)
        deduped.append(result)
        if len(deduped) >= max_results:
            break
    return deduped


def _is_pdf_url(url: str) -> bool:
    return urllib.parse.urlparse(url).path.lower().endswith(".pdf")


def _result_text(result: SearchResult) -> str:
    return f"{result.text} {result.url}".lower()


def _score_search_result(result: SearchResult, year: int, paper: int) -> int:
    if paper not in PAPER_ALTERNATES:
        raise ValueError(f"Unsupported paper value: {paper}")

    text = _result_text(result)
    score = 0

    if str(year) in text:
        score += YEAR_MATCH_SCORE
    if re.search(rf"\bpaper[\s_-]*{paper}\b", text):
        score += PAPER_MATCH_SCORE
    other_paper = PAPER_ALTERNATES[paper]
    if re.search(rf"\bpaper[\s_-]*{other_paper}\b", text):
        score -= OTHER_PAPER_PENALTY
    if result.text:
        score += RESULT_TEXT_SCORE

    return score


def choose_pdf_url(results: Iterable[SearchResult], year: int, paper: int) -> Optional[str]:
    candidates = [result for result in results if _is_pdf_url(result.url)]
    if not candidates:
        return None
    best_result = max(candidates, key=lambda result: _score_search_result(result, year, paper))
    return best_result.url


def _is_valid_pdf_file(path: Path) -> bool:
    try:
        with path.open("rb") as file_handle:
            return file_handle.read(8).startswith(b"%PDF-")
    except OSError:
        return False


def build_filename(year: int, paper: int) -> str:
    return f"kcse_math_{year}_paper_{paper}.pdf"


def download_pdf(session: requests.Session, url: str, destination: Path) -> None:
    temp_destination = destination.with_name(f"{destination.name}.part")
    with session.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()
        media_type = content_type.split(";", 1)[0].strip()
        if media_type in BAD_PDF_CONTENT_TYPES:
            raise ValueError(
                f"Downloaded content from {url} has content type {content_type!r} (media type {media_type!r}), which indicates HTML/XML instead of PDF."
            )

        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with temp_destination.open("wb") as file_handle:
                for chunk in response.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        file_handle.write(chunk)
            if not _is_valid_pdf_file(temp_destination):
                with temp_destination.open("rb") as file_handle:
                    header = file_handle.read(16)
                raise ValueError(
                    f"Downloaded content from {url} is not a valid PDF file; header starts with {header!r}."
                )
            temp_destination.replace(destination)
        finally:
            if temp_destination.exists():
                try:
                    temp_destination.unlink()
                except OSError as cleanup_error:
                    logging.warning("Failed to remove temporary file %s: %s", temp_destination, cleanup_error)


def parse_papers(value: str) -> tuple[int, ...]:
    papers: list[int] = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        if not re.fullmatch(r"\d+", token):
            raise ValueError(f"Invalid paper value: {token}")
        paper = int(token)
        if paper not in DEFAULT_PAPERS:
            raise ValueError(f"Unsupported paper value: {paper}. Supported papers: {DEFAULT_PAPERS}")
        papers.append(paper)
    if not papers:
        raise ValueError("No valid paper numbers provided.")
    return tuple(sorted(set(papers)))


def run_hunter(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    manifest_path = Path(args.manifest_path)
    papers = parse_papers(args.papers)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    records: list[PaperRecord] = []

    for year in range(args.start_year, args.end_year + 1):
        for paper in papers:
            query = build_query(year, paper)
            logging.info("Searching: %s", query)

            try:
                results = fetch_search_results(session, query, args.max_results)
                pdf_url = choose_pdf_url(results, year, paper)
            except Exception as exc:
                records.append(
                    PaperRecord(
                        year=year,
                        paper=paper,
                        query=query,
                        source_url=None,
                        local_path=None,
                        status="search_failed",
                        error=str(exc),
                        discovered_at=_now_iso(),
                    )
                )
                continue

            if not pdf_url:
                records.append(
                    PaperRecord(
                        year=year,
                        paper=paper,
                        query=query,
                        source_url=None,
                        local_path=None,
                        status="not_found",
                        error="No PDF links found in search results.",
                        discovered_at=_now_iso(),
                    )
                )
                continue

            destination = output_dir / build_filename(year, paper)
            if destination.exists():
                if not _is_valid_pdf_file(destination):
                    logging.warning("Existing file is not a valid PDF; redownloading %s", destination)
                    destination.unlink()
                else:
                    records.append(
                        PaperRecord(
                            year=year,
                            paper=paper,
                            query=query,
                            source_url=pdf_url,
                            local_path=str(destination),
                            status="exists",
                            error=None,
                            discovered_at=_now_iso(),
                        )
                    )
                    continue

            if args.dry_run:
                records.append(
                    PaperRecord(
                        year=year,
                        paper=paper,
                        query=query,
                        source_url=pdf_url,
                        local_path=str(destination),
                        status="found",
                        error=None,
                        discovered_at=_now_iso(),
                    )
                )
                continue

            try:
                download_pdf(session, pdf_url, destination)
                status = "downloaded"
                error = None
            except Exception as exc:
                status = "download_failed"
                error = str(exc)

            records.append(
                PaperRecord(
                    year=year,
                    paper=paper,
                    query=query,
                    source_url=pdf_url,
                    local_path=str(destination),
                    status=status,
                    error=error,
                    discovered_at=_now_iso(),
                )
            )

            time.sleep(args.delay_seconds)

    manifest = {
        "generated_at": _now_iso(),
        "output_dir": str(output_dir),
        "records": [asdict(record) for record in records],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logging.info("Manifest saved to %s", manifest_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Discover and download KCSE Mathematics Paper PDFs for trend analysis.",
    )
    parser.add_argument("--start-year", type=int, default=DEFAULT_START_YEAR)
    parser.add_argument("--end-year", type=int, default=DEFAULT_END_YEAR)
    parser.add_argument("--papers", default="1,2", help="Comma-separated paper numbers (default: 1,2)")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--manifest-path", default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument("--max-results", type=int, default=12, help="Max search results per query")
    parser.add_argument("--delay-seconds", type=float, default=1.0, help="Delay between downloads")
    parser.add_argument("--dry-run", action="store_true", help="Only discover links without downloading")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if args.start_year > args.end_year:
        logging.error("start-year must be <= end-year")
        return 2

    try:
        return run_hunter(args)
    except Exception as exc:
        logging.error("Paper hunting failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
