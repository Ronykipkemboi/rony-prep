# KCSE Math Questions Extractor

A Python utility to extract KCSE (Kenya Certificate of Secondary Education) mathematics questions from documents using Google's Gemini 2.0 Flash API. The extracted questions are output as clean, structured JSON.

## Features

- ✅ **Fixed upload() API call** - Uses correct `file=` parameter (not `path=`)
- ✅ **Gemini 2.0 Flash** - Latest Google Gemini model for fast, accurate extraction
- ✅ **Structured JSON output** - Clean JSON format with question metadata
- ✅ **Automatic file cleanup** - Uploaded files are automatically deleted after processing
- ✅ **Error handling** - Comprehensive error handling and user feedback

## Problem Fixed

### Previous Issue
```python
# ❌ INCORRECT - This causes TypeError
uploaded_file = genai.files.upload(path=file_path)
# TypeError: upload() got an unexpected keyword argument path
```

### Current Implementation
```python
# ✅ CORRECT - Using file= parameter
uploaded_file = genai.files.upload(file=file_path)
```

The latest google-genai library (≥0.3.0) changed the API to use `file=` instead of `path=`.

## Installation

1. Clone this repository:
```bash
git clone https://github.com/Ronykipkemboi/rony-prep.git
cd rony-prep
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Google API key:
```bash
export GOOGLE_API_KEY="your-google-api-key-here"
```

You can get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

Optionally, copy `.env.example` to `.env` and set `GOOGLE_API_KEY` there (the script loads it automatically).

## Usage

### Basic Usage

```bash
python test_extraction.py <document_path> [output_path]
```

### Examples

```bash
# Extract from PDF and save to default output file
python test_extraction.py sample_questions.pdf

# Extract from PDF and specify custom output file
python test_extraction.py sample_questions.pdf my_questions.json

# Extract from image
python test_extraction.py exam_scan.jpg extracted_math_questions.json
```

### Using as a Module

```python
from test_extraction import KCSEMathExtractor

# Initialize extractor
extractor = KCSEMathExtractor(api_key="your-api-key")

# Extract questions
questions_data = extractor.extract_questions("sample.pdf")

# Save to JSON
extractor.save_json_output(questions_data, "output.json")

# Access extracted questions
print(f"Found {questions_data['total_questions']} questions")
for question in questions_data['questions']:
    print(f"Q{question['number']}: {question['text']}")
```

## Output Format

The script outputs a JSON file with the following structure:

```json
{
  "questions": [
    {
      "number": 1,
      "text": "Solve the equation 2x + 5 = 13",
      "type": "short answer",
      "difficulty": "easy",
      "topic": "Algebra"
    },
    {
      "number": 2,
      "text": "Find the area of a circle with radius 7 cm",
      "type": "short answer",
      "difficulty": "medium",
      "topic": "Geometry"
    }
  ],
  "total_questions": 2,
  "extraction_metadata": {
    "source_file": "sample.pdf",
    "extraction_date": "2024-05-15T16:55:00Z",
    "model_used": "gemini-2.0-flash"
  }
}
```

## Supported File Types

- PDF documents
- PNG, JPG, JPEG images
- GIF images
- WebP images
- HEIC/HEIF images

## Key Changes from Previous Version

1. **API Parameter**: Changed `path=` to `file=` in the upload() call
2. **Model Update**: Uses `gemini-2.0-flash` instead of older models
3. **JSON Output**: Structured JSON output with metadata for better integration
4. **Error Handling**: Improved error messages and graceful failure handling
5. **Resource Cleanup**: Automatic deletion of uploaded files

## Troubleshooting

### "API key not found" Error
Make sure you've set the `GOOGLE_API_KEY` environment variable:
```bash
export GOOGLE_API_KEY="your-key"
python test_extraction.py sample.pdf
```

### "API key not valid" Error
Your key is missing, expired, or still set to the placeholder value. Fix it by:
1. Updating `.env` or your shell to use a real key (not `your-api-key-here`)
2. Regenerating the key in Google AI Studio if needed
3. Ensuring the Gemini API is enabled for your project

### "File not found" Error
Ensure the file path is correct and the file exists:
```bash
# Check if file exists
ls -la sample.pdf
```

### "Invalid JSON response" Error
The API might have returned an error. Check:
1. Your API key is valid and has Gemini API enabled
2. The file is readable and in a supported format
3. Your quota hasn't been exceeded

## Requirements

- Python 3.8+
- google-genai ≥0.3.0
- Valid Google API key with Gemini access

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.
