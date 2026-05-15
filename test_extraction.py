#!/usr/bin/env python3
"""
KCSE Math Questions Extraction Script
Uses google-genai library to extract math questions from documents and output as clean JSON.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    import google.genai as genai
except ImportError:
    print("Error: google-genai is not installed. Please install it with: pip install google-genai")
    sys.exit(1)

API_KEY_ENV_VARS = ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GENAI_API_KEY")
PLACEHOLDER_API_KEYS = {
    "your-api-key-here",
    "your_google_api_key",
    "your-google-api-key",
    "your-api-key",
    "api-key",
    "apikey",
}
INVALID_API_KEY_HINTS = ("api key not valid", "api_key_invalid", "invalid api key")


def _normalize_api_key(value: str) -> str:
    value = value.strip()
    if value.startswith("'") and value.endswith("'") and value.count("'") == 2:
        return value[1:-1].strip()
    if value.startswith('"') and value.endswith('"') and value.count('"') == 2:
        return value[1:-1].strip()
    return value


def _is_placeholder_key(value: str) -> bool:
    normalized = _normalize_api_key(value).lower()
    return normalized in PLACEHOLDER_API_KEYS


def _is_invalid_api_key_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(hint in message for hint in INVALID_API_KEY_HINTS)


class KCSEMathExtractor:
    """Extracts KCSE math questions from documents and outputs structured JSON."""

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
                f"{', '.join(API_KEY_ENV_VARS)} or pass it as an argument."
            )

        self.api_key = _normalize_api_key(raw_key)
        if not self.api_key:
            raise ValueError(
                "Google API key is empty or malformed. Please set one of "
                f"{', '.join(API_KEY_ENV_VARS)} to a valid key."
            )

        if _is_placeholder_key(self.api_key):
            raise ValueError(
                "Google API key is set to a placeholder value. Please replace it with a valid key "
                "from https://aistudio.google.com/app/apikey."
            )

        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.0-flash"

    def extract_questions(self, file_path: str) -> dict:
        """
        Extract KCSE math questions from a document file.
        
        Args:
            file_path: Path to the document file (PDF, image, etc.)
            
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
            Please extract all KCSE (Kenya Certificate of Secondary Education) mathematics questions 
            from this document. For each question, provide:
            
            1. Question number
            2. Question text
            3. Question type (e.g., "multiple choice", "short answer", "problem solving")
            4. Difficulty level (if identifiable: "easy", "medium", "hard")
            5. Topic/subtopic (e.g., "Algebra", "Geometry", "Trigonometry", "Statistics", etc.)
            
            Return the results as a valid JSON array with the following structure:
            {
                "questions": [
                    {
                        "number": 1,
                        "text": "Question text here",
                        "type": "multiple choice",
                        "difficulty": "medium",
                        "topic": "Algebra"
                    },
                    ...
                ],
                "total_questions": <count>,
                "extraction_metadata": {
                    "source_file": "<filename>",
                    "extraction_date": "<ISO timestamp>",
                    "model_used": "gemini-2.0-flash"
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
                        extraction_prompt,
                        {
                            "mime_type": uploaded_file.mime_type,
                            "data": uploaded_file,
                        }
                    ]
                )
            except Exception as exc:
                if _is_invalid_api_key_error(exc):
                    env_list = ", ".join(API_KEY_ENV_VARS)
                    raise ValueError(
                        "Google API key is invalid. Please verify one of "
                        f"{env_list} is set to a valid key from "
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
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to: {output_path}")


def main():
    """Main function to demonstrate usage."""
    # Example usage
    extractor = KCSEMathExtractor()
    
    # Check if a file path was provided as command line argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else "extracted_questions.json"
        
        try:
            questions_data = extractor.extract_questions(file_path)
            extractor.save_json_output(questions_data, output_path)
            
            # Print summary
            print("\n=== Extraction Summary ===")
            print(f"Total questions extracted: {questions_data.get('total_questions', 0)}")
            if questions_data.get('questions'):
                print("\nFirst question preview:")
                print(json.dumps(questions_data['questions'][0], indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"Error during extraction: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python test_extraction.py <file_path> [output_path]")
        print("\nExample: python test_extraction.py sample.pdf extracted_questions.json")
        print("\nEnvironment Variables:")
        print("  GOOGLE_API_KEY - Your Google API key for Gemini access")


if __name__ == "__main__":
    main()
