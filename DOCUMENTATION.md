# Technical Documentation: KCSE Predictive Strategy Engine

## Overview

This document details the implementation of the KCSE Predictive Strategy Engine using Google's Gemini 2.0 Flash API to extract metadata for trend analysis and probability reporting.

## Problem Statement

The repository now focuses on a predictive strategy engine that extracts topic, section, and marks metadata to estimate exam probabilities. Along the way, the original technical issue encountered was:
```
TypeError: upload() got an unexpected keyword argument path
```

This occurred because the google-genai library API changed in recent versions.

## Solution Implemented

### 1. API Parameter Fix

**Before (Incorrect):**
```python
uploaded_file = genai.files.upload(path=file_path)
```

**After (Correct):**
```python
uploaded_file = genai.files.upload(file=file_path)
```

The latest google-genai library (≥0.3.0) uses `file=` parameter instead of `path=`.

### 2. Model Update

Changed from older models to:
```python
self.model = "gemini-2.0-flash"
```

**Gemini 2.0 Flash Benefits:**
- Faster response times (50% faster than 1.5 Flash)
- Better accuracy for document analysis
- Optimal for educational content extraction
- Lower latency for real-time applications

### 3. JSON Output Structure

The extractor produces structured JSON with:

```json
{
  "questions": [
    {
      "number": 1,
      "text": "Question text",
      "section": "Section I",
      "marks": 2,
      "topic": "topic/subtopic"
    }
  ],
  "total_questions": <count>,
  "extraction_metadata": {
    "source_file": "filename",
    "extraction_date": "ISO timestamp",
    "model_used": "gemini-2.0-flash",
    "focus": "predictive_trend_analysis",
    "year": 2024,
    "paper": 1
  }
}
```

### 4. Key Features

#### Error Handling
- File existence validation
- API key validation
- JSON parsing with markdown removal
- Comprehensive error messages

#### Resource Management
- Automatic cleanup of uploaded files
- Proper file handle management
- Resource release after processing

#### Supported Formats
- PDF documents
- Image files (PNG, JPG, JPEG, GIF, WebP, HEIC)

#### Predictive Pipeline
- **Paper Hunter** (`paper_hunter.py`) discovers and downloads KCSE Math Paper 1 & 2 PDFs (2015-2024).
- **Batch Extraction** (`test_extraction.py`) processes every downloaded file from the manifest.
- **Probability Report** (`probability_report.py`) summarizes topic frequency across the last 10 years.

## Implementation Details

### File Upload Flow

1. **Initialize Client**
   - Configure genai with API key
   - Set model to gemini-2.0-flash

2. **Upload File**
   ```python
   uploaded_file = genai.files.upload(file=file_path)
   ```

3. **Process Content**
   - Send extraction prompt to Gemini
   - Include uploaded file reference
   - Request JSON output

4. **Parse Response**
   - Handle markdown formatting removal
   - Parse JSON response
   - Validate structure

5. **Cleanup**
   - Delete uploaded file
   - Release resources

### Question Extraction Prompt

The prompt instructs the AI to:
1. Identify each KCSE math question
2. Extract question text
3. Identify the section
4. Extract the marks/weight
5. Categorize by topic
6. Avoid solving questions and return only valid JSON

## Usage Examples

### Command Line

```bash
# Basic usage
python test_extraction.py sample.pdf

# With custom output
python test_extraction.py exam.pdf questions.json

# Bulk pipeline: discover, extract, and report
python paper_hunter.py --output-dir downloads/kcse_papers --manifest-path downloads/kcse_papers_manifest.json
python test_extraction.py downloads/kcse_papers_manifest.json extracted_outputs/
python probability_report.py extracted_outputs --output probability_report.json
```

### Python API

```python
from test_extraction import KCSEMathExtractor

extractor = KCSEMathExtractor()
data = extractor.extract_questions("sample.pdf")
extractor.save_json_output(data, "output.json")
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| google-genai | ≥0.3.0 | Gemini API client |
| requests | ≥2.32.3 | Web requests for paper discovery |
| beautifulsoup4 | ≥4.12.3 | HTML parsing for search results |
| Python | ≥3.8 | Runtime environment |

## Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| GOOGLE_API_KEY | Authentication for Gemini API | Yes |

## Performance Characteristics

- **Upload Speed**: Depends on file size and connection
- **Processing Time**: Typically 5-15 seconds per document
- **Output Size**: ~2-5KB per 100 questions
- **API Cost**: Varies based on usage tier

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "API key not found" | GOOGLE_API_KEY not set | Set environment variable |
| "API key not valid" | Invalid or placeholder key | Replace with a valid key from Google AI Studio and ensure Gemini API is enabled |
| "File not found" | Invalid file path | Verify file exists |
| "TypeError: upload()" | Using old API syntax | Update google-genai package |
| "Invalid JSON" | Malformed response | Check API quota and limits |

## Testing

Run the output structure test:
```bash
python test_output_structure.py
```

This validates the JSON schema and output format.

## Future Enhancements

Potential improvements:
1. Topic taxonomy refinement for more granular trends
2. Custom extraction rules per section
3. Answer key alignment for accuracy checks
4. Trend visualization dashboards
5. Multi-language support

## References

- [Google Generative AI Python SDK](https://github.com/googleapis/python-genai)
- [Gemini 2.0 Documentation](https://ai.google.dev/docs)
- [File Upload API](https://ai.google.dev/docs/files)

## Version History

### v1.0.0 (2026-05-15)
- Initial release with Gemini 2.0 Flash support
- Fixed upload() API parameter
- Clean JSON output for KCSE questions
- Automatic file cleanup
- Comprehensive error handling

### v1.1.0 (2026-05-15)
- Predictive strategy focus with topic/section/marks metadata
- Paper Hunter discovery pipeline
- Probability report generation for trend analysis
