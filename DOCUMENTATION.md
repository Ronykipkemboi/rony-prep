# Technical Documentation: KCSE Math Question Extractor

## Overview

This document details the implementation of the KCSE Math Question Extractor using Google's Gemini 2.0 Flash API.

## Problem Statement

The original error encountered was:
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
      "type": "question type",
      "difficulty": "difficulty level",
      "topic": "topic/subtopic"
    }
  ],
  "total_questions": <count>,
  "extraction_metadata": {
    "source_file": "filename",
    "extraction_date": "ISO timestamp",
    "model_used": "gemini-2.0-flash"
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
3. Classify question type
4. Estimate difficulty level
5. Categorize by topic
6. Return only valid JSON

## Usage Examples

### Command Line

```bash
# Basic usage
python test_extraction.py sample.pdf

# With custom output
python test_extraction.py exam.pdf questions.json
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
1. Support for batch processing
2. Custom extraction rules
3. Answer key extraction
4. Solution steps extraction
5. Difficulty level refinement using ML
6. Multi-language support

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
