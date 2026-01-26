# BookSmith Module

TTS-optimized text extraction from EPUB/PDF files. Zero GUI dependencies.

## Quick Start

```python
from booksmith_module import EPUBProcessor, PDFProcessor

# Process a book
book_data = EPUBProcessor.process("book.epub")
# or
book_data = PDFProcessor.process("book.pdf")

# Export to JSON
manifest = book_data.to_manifest()
```

## What It Does

1. **Extracts text** from EPUB/PDF files
2. **Cleans aggressively** - removes page numbers, headers, footers, ligatures, invisible chars
3. **Splits into chapters** automatically
4. **Optimized for TTS** - text is ready for Qwen3-TTS, CosyVoice, etc.

## Installation

```bash
pip install -r requirements.txt
```

## Key Features

- **PDF Processing:** Uses Docling AI (IBM Research) for intelligent layout analysis
- **EPUB Processing:** Parses HTML structure with chapter detection
- **7-Stage Cleaning:** Encoding repair, artifact removal, ligature fixes, whitespace normalization
- **No GUI:** Pure processing logic for pipeline integration

## API

### Process Files

```python
from booksmith_module import EPUBProcessor, PDFProcessor

# EPUB
book_data = EPUBProcessor.process("path/to/book.epub")

# PDF with progress tracking
def progress(msg):
    print(msg)

book_data = PDFProcessor.process("path/to/book.pdf", progress_callback=progress)
```

### Access Data

```python
print(book_data.title)      # Book title
print(book_data.author)     # Author name
print(book_data.chapters)   # List of Chapter objects

for chapter in book_data.chapters:
    print(chapter.label)    # "Chapter 1"
    print(chapter.text)     # Clean text, TTS-ready
    chapter.enabled = False # Disable if unwanted
```

### Export Manifest

```python
manifest = book_data.to_manifest()
# Returns: {"title": "...", "author": "...", "chapters": [...]}

import json
with open("output.json", 'w') as f:
    json.dump(manifest, f, indent=2)
```

### Clean Text Only

```python
from booksmith_module import TextCleaner

clean_text = TextCleaner.clean("Dirty text with ﬁ ligatures...")
```

## JSON Output Format

```json
{
  "title": "Book Title",
  "author": "Author Name",
  "chapters": [
    {
      "id": 1,
      "label": "Chapter 1",
      "style_prompt": "",
      "text": "Chapter content..."
    }
  ]
}
```

## Dependencies

- `docling` - IBM AI for PDF layout analysis
- `ebooklib` - EPUB parsing
- `beautifulsoup4` - HTML parsing
- `ftfy` - Unicode normalization
- `pymupdf` - PDF bookmark extraction

## Performance

- **First PDF:** Downloads AI models (~200MB, one-time)
- **Subsequent:** Fast processing (~5-15s per book)
- **GPU:** Automatic CUDA acceleration if available

## License

MIT
