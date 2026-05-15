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
                "type": "short answer",
                "difficulty": "medium",
                "topic": "Algebra"
            },
            {
                "number": 2,
                "text": "Find the area of a triangle with base 8 cm and height 6 cm",
                "type": "short answer",
                "difficulty": "easy",
                "topic": "Geometry"
            },
            {
                "number": 3,
                "text": "If sin θ = 0.5 and θ is acute, find the value of cos θ",
                "type": "multiple choice",
                "difficulty": "medium",
                "topic": "Trigonometry"
            },
            {
                "number": 4,
                "text": "A circle has radius 5 cm. Calculate its circumference",
                "type": "short answer",
                "difficulty": "easy",
                "topic": "Geometry"
            },
            {
                "number": 5,
                "text": "Simplify: (3x² + 6x) / 3x",
                "type": "short answer",
                "difficulty": "easy",
                "topic": "Algebra"
            }
        ],
        "total_questions": 5,
        "extraction_metadata": {
            "source_file": "sample_exam.pdf",
            "extraction_date": datetime.now().isoformat() + "Z",
            "model_used": "gemini-2.0-flash"
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
        assert "type" in q, "Each question should have a 'type'"
        assert "difficulty" in q, "Each question should have 'difficulty'"
        assert "topic" in q, "Each question should have a 'topic'"
    
    print("\n✅ JSON structure validation passed!\n")
    print("Sample Output:")
    print(json.dumps(sample_data, indent=2, ensure_ascii=False))
    
    return sample_data


if __name__ == "__main__":
    main()
