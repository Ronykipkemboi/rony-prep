#!/usr/bin/env python3
"""
KCSE Predictive Strategy Extraction Script
Uses google-genai to extract question metadata for trend analysis.
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    import google.genai as genai
    from google.genai import types
except ImportError:
    print("Error: google-genai is not installed. Please install it with: pip install google-genai")
    sys.exit(1)

API_KEY_ENV_VARS = ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GENAI_API_KEY")
API_KEY_ENV_LIST = ", ".join(API_KEY_ENV_VARS)
BATCH_EXTRACTION_DELAY_SECONDS = 30
PLACEHOLDER_API_KEYS = {
    "your-api-key-here",
    "your-api-key",
    "your_api_key",
    "yourapikey",
    "api-key",
    "apikey",
}
PLACEHOLDER_PREFIXES = ("your", "replace", "enter", "add", "insert")
PLACEHOLDER_TOKENS = {"api", "key", "apikey"}
INVALID_API_KEY_HINTS = (
    "api key not valid",
    "api_key_invalid",
    "invalid api key",
    "authentication failed",
    "unauthorized",
    "invalid credentials",
)


def _normalize_api_key(value: str) -> str:
    value = value.strip()
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1].strip()
    return value


def _is_placeholder_key(value: str) -> bool:
    normalized = _normalize_api_key(value).lower()
    if normalized in PLACEHOLDER_API_KEYS:
        return True

    tokens = normalized.replace("-", "_").split("_")
    if tokens and tokens[0] in PLACEHOLDER_PREFIXES:
        return any(token in PLACEHOLDER_TOKENS for token in tokens)

    return False


def _has_invalid_api_key_reason(details: object) -> bool:
    if not details:
        return False
    if isinstance(details, dict):
        return details.get("reason") == "API_KEY_INVALID"
    if isinstance(details, (list, tuple)):
        return any(_has_invalid_api_key_reason(detail) for detail in details)
    return getattr(details, "reason", None) == "API_KEY_INVALID"


def _is_invalid_api_key_error(exc: Exception) -> bool:
    for attr in ("error_details", "details", "errors"):
        if _has_invalid_api_key_reason(getattr(exc, attr, None)):
            return True

    message = str(exc).lower()
    return any(hint in message for hint in INVALID_API_KEY_HINTS)


class KCSEMathExtractor:
    """Extracts KCSE math questions metadata for predictive trend analysis."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the extractor with Google Genai client.
        
        Args:
            api_key: Google API key. If None, uses GOOGLE_API_KEY env variable.
        """
        raw_key = api_key
        if not raw_key:
            for env_var in API_KEY_ENV_VARS:
                raw_key = os.getenv(env_var)
                if raw_key:
                    break

        if not raw_key:
            raise ValueError(
                "Google API key not found. Please set one of "
                f"{API_KEY_ENV_LIST} or pass it as an argument."
            )

        self.api_key = _normalize_api_key(raw_key)
        if not self.api_key:
            raise ValueError(
                "Google API key is empty, whitespace-only, or contains only quotes. "
                f"Please set one of {API_KEY_ENV_LIST} to a valid key."
            )

        if _is_placeholder_key(self.api_key):
            raise ValueError(
                "Google API key is set to a placeholder value. Please replace it with a valid key "
                "from https://aistudio.google.com/app/apikey."
            )

        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.0-flash"

    def extract_questions(
        self,
        file_path: str,
        *,
        year: Optional[int] = None,
        paper: Optional[int] = None,
        source_url: Optional[str] = None,
    ) -> dict:
        """
        Extract KCSE math questions from a document file.
        
        Args:
            file_path: Path to the document file (PDF, image, etc.)
            year: Optional year of the paper for metadata.
            paper: Optional paper number for metadata.
            source_url: Optional source URL for metadata.
            
        Returns:
            Dictionary containing extracted questions in JSON format
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Upload the file using the correct file= parameter
        print(f"Uploading file: {file_path}")
        
        # Use file= parameter instead of path= (this is the fix for the TypeError)
        uploaded_file = self.client.files.upload(file=file_path)
        print(f"File uploaded successfully: {uploaded_file.name}")

        try:
            # Create the extraction prompt
            extraction_prompt = """
            Extract KCSE (Kenya Certificate of Secondary Education) mathematics questions for trend analysis.
            Do NOT solve any questions. Focus only on metadata.

            For each question, provide:
            1. Question number
            2. Question text
            3. Section (e.g., "Section I", "Section II")
            4. Marks/weight (numeric marks assigned to the question)
            5. Topic/subtopic (e.g., "Algebra", "Geometry", "Trigonometry", "Statistics")

            Return the results as valid JSON with the following structure:
            {
                "questions": [
                    {
                        "number": 1,
                        "text": "Question text here",
                        "section": "Section I",
                        "marks": 2,
                        "topic": "Algebra"
                    }
                ],
                "total_questions": <count>,
                "extraction_metadata": {
                    "source_file": "<filename>",
                    "extraction_date": "<ISO timestamp>",
                    "model_used": "gemini-2.0-flash",
                    "focus": "predictive_trend_analysis"
                }
            }

            IMPORTANT: Return ONLY valid JSON. Do not include any markdown formatting or explanation text.
            """

            # Call the API with the uploaded file
            print("Processing with Gemini 2.0 Flash...")
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_text(text=extraction_prompt),
                                types.Part.from_uri(
                                    file_uri=uploaded_file.uri,
                                    mime_type=uploaded_file.mime_type,
                                ),
                            ],
                        )
                    ],
                )
            except Exception as exc:
                if _is_invalid_api_key_error(exc):
                    raise ValueError(
                        "Google API key is invalid. Please verify one of "
                        f"{API_KEY_ENV_LIST} is set to a valid key from "
                        "https://aistudio.google.com/app/apikey."
                    ) from exc
                raise

            # Parse the response as JSON
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON response
            questions_data = json.loads(response_text)

            metadata = questions_data.setdefault("extraction_metadata", {})
            metadata.setdefault("model_used", self.model)
            metadata["source_file"] = file_path.name
            metadata["extraction_date"] = datetime.now(timezone.utc).isoformat()
            metadata["focus"] = "predictive_trend_analysis"
            if year is not None:
                metadata["year"] = year
            if paper is not None:
                metadata["paper"] = paper
            if source_url:
                metadata["source_url"] = source_url

            if "total_questions" not in questions_data:
                questions_data["total_questions"] = len(questions_data.get("questions", []))

            print(f"Successfully extracted {questions_data.get('total_questions', 0)} questions")
            return questions_data

        finally:
            # Clean up: delete the uploaded file
            print(f"Cleaning up: deleting uploaded file {uploaded_file.name}")
            self.client.files.delete(name=uploaded_file.name)

    def save_json_output(self, data: dict, output_path: str) -> None:
        """
        Save extracted questions to a JSON file.
        
        Args:
            data: Dictionary containing extracted questions
            output_path: Path where to save the JSON file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to: {output_path}")


@dataclass
class ExtractionTarget:
    path: Path
    year: Optional[int] = None
    paper: Optional[int] = None
    source_url: Optional[str] = None


SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic", ".heif"}


def _parse_year_paper_from_name(path: Path) -> tuple[Optional[int], Optional[int]]:
    match = re.search(r"(20\d{2}).*paper[\s_-]?([12])", path.stem, re.IGNORECASE)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def _load_manifest(manifest_path: Path) -> list[ExtractionTarget]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = data.get("records", [])
    targets: list[ExtractionTarget] = []
    for record in records:
        status = record.get("status")
        local_path = record.get("local_path")
        if status not in {"downloaded", "exists"} or not local_path:
            continue
        path = Path(local_path)
        if not path.exists():
            continue
        targets.append(
            ExtractionTarget(
                path=path,
                year=record.get("year"),
                paper=record.get("paper"),
                source_url=record.get("source_url"),
            )
        )
    return targets


def _load_directory(input_dir: Path) -> list[ExtractionTarget]:
    targets: list[ExtractionTarget] = []
    for file_path in sorted(input_dir.glob("**/*")):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        year, paper = _parse_year_paper_from_name(file_path)
        targets.append(ExtractionTarget(path=file_path, year=year, paper=paper))
    return targets


def _output_path_for_target(output_dir: Path, target: ExtractionTarget) -> Path:
    if target.year and target.paper:
        filename = f"kcse_math_{target.year}_paper_{target.paper}.json"
    else:
        filename = f"{target.path.stem}.json"
    return output_dir / filename


def run_batch(extractor: KCSEMathExtractor, targets: list[ExtractionTarget], output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    for index, target in enumerate(targets):
        try:
            data = extractor.extract_questions(
                str(target.path),
                year=target.year,
                paper=target.paper,
                source_url=target.source_url,
            )
            output_path = _output_path_for_target(output_dir, target)
            extractor.save_json_output(data, str(output_path))
            results.append(
                {
                    "input_path": str(target.path),
                    "output_path": str(output_path),
                    "status": "success",
                }
            )
        except Exception as exc:
            results.append(
                {
                    "input_path": str(target.path),
                    "output_path": None,
                    "status": "failed",
                    "error": str(exc),
                }
            )
        if index + 1 < len(targets):
            time.sleep(BATCH_EXTRACTION_DELAY_SECONDS)
    summary = {
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "total_files": len(targets),
        "successes": len([r for r in results if r["status"] == "success"]),
        "failures": len([r for r in results if r["status"] == "failed"]),
        "results": results,
    }
    summary_path = output_dir / "batch_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Batch summary saved to: {summary_path}")
    return summary


def main():
    """Main function to demonstrate usage."""
    extractor = KCSEMathExtractor()

    if len(sys.argv) <= 1:
        print("Usage: python test_extraction.py <file|directory|manifest.json> [output_path]")
        print("Examples:")
        print("  python test_extraction.py sample.pdf extracted_questions.json")
        print("  python test_extraction.py downloads/kcse_papers extracted_outputs/")
        print("  python test_extraction.py downloads/kcse_papers_manifest.json extracted_outputs/")
        print("\nEnvironment Variables:")
        print("  GOOGLE_API_KEY - Your Google API key for Gemini access")
        sys.exit(0)

    input_path = Path(sys.argv[1])
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        if input_path.is_dir():
            targets = _load_directory(input_path)
            output_dir = Path(output_path) if output_path else Path("extracted_outputs")
            run_batch(extractor, targets, output_dir)
        elif input_path.suffix.lower() == ".json":
            data = json.loads(input_path.read_text(encoding="utf-8"))
            if "records" in data:
                targets = _load_manifest(input_path)
                output_dir = Path(output_path) if output_path else Path("extracted_outputs")
                run_batch(extractor, targets, output_dir)
            else:
                raise ValueError("JSON input is not a valid paper manifest.")
        else:
            output_file = output_path or "extracted_questions.json"
            questions_data = extractor.extract_questions(str(input_path))
            extractor.save_json_output(questions_data, output_file)

            print("\n=== Extraction Summary ===")
            print(f"Total questions extracted: {questions_data.get('total_questions', 0)}")
            if questions_data.get("questions"):
                print("\nFirst question preview:")
                print(json.dumps(questions_data["questions"][0], indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error during extraction: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
