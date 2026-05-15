#!/usr/bin/env python3
"""
Test script to verify the extraction functionality.
This is a mock test that demonstrates the JSON output structure.
"""

import json
from datetime import datetime


def generate_sample_output():
    """Generate sample output to verify JSON structure."""
    sample_output = {
        "questions": [
            {
                "number": 1,
                "text": "Solve the equation: 3x² - 12x + 9 = 0",
                "section": "Section I",
                "marks": 2,
                "topic": "Algebra"
            },
            {
                "number": 2,
                "text": "Find the area of a triangle with base 8 cm and height 6 cm",
                "section": "Section I",
                "marks": 3,
                "topic": "Geometry"
            },
            {
                "number": 3,
                "text": "If sin θ = 0.5 and θ is acute, find the value of cos θ",
                "section": "Section I",
                "marks": 2,
                "topic": "Trigonometry"
            },
            {
                "number": 4,
                "text": "A circle has radius 5 cm. Calculate its circumference",
                "section": "Section II",
                "marks": 5,
                "topic": "Geometry"
            },
            {
                "number": 5,
                "text": "Simplify: (3x² + 6x) / 3x",
                "section": "Section II",
                "marks": 6,
                "topic": "Algebra"
            }
        ],
        "total_questions": 5,
        "extraction_metadata": {
            "source_file": "sample_exam.pdf",
            "extraction_date": datetime.now().isoformat() + "Z",
            "model_used": "gemini-2.0-flash",
            "focus": "predictive_trend_analysis",
            "year": 2024,
            "paper": 1
        }
    }
    return sample_output


def main():
    """Test the output structure."""
    print("Generating sample KCSE math questions JSON...")
    sample_data = generate_sample_output()
    
    # Verify JSON structure
    assert isinstance(sample_data, dict), "Output should be a dictionary"
    assert "questions" in sample_data, "Output should contain 'questions' key"
    assert "total_questions" in sample_data, "Output should contain 'total_questions' key"
    assert "extraction_metadata" in sample_data, "Output should contain 'extraction_metadata' key"
    
    # Verify questions structure
    for q in sample_data["questions"]:
        assert "number" in q, "Each question should have a 'number'"
        assert "text" in q, "Each question should have 'text'"
        assert "section" in q, "Each question should have a 'section'"
        assert "marks" in q, "Each question should have 'marks'"
        assert "topic" in q, "Each question should have a 'topic'"

    # Verify metadata structure
    metadata = sample_data["extraction_metadata"]
    assert "focus" in metadata, "Metadata should include predictive focus"
    assert "year" in metadata, "Metadata should include year"
    assert "paper" in metadata, "Metadata should include paper"
    
    print("\n✅ JSON structure validation passed!\n")
    print("Sample Output:")
    print(json.dumps(sample_data, indent=2, ensure_ascii=False))
    
    return sample_data


if __name__ == "__main__":
    main()
