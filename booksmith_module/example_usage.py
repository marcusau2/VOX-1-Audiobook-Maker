"""
Example usage of the BookSmith module for processing books.
This demonstrates the API without any GUI dependencies.
"""

import json
from pathlib import Path
from booksmith_module import EPUBProcessor, PDFProcessor, BookData, TextCleaner


def process_epub(epub_path: str) -> BookData:
    """
    Process an EPUB file and return BookData object.

    Example:
        book_data = process_epub("mybook.epub")
        print(f"Title: {book_data.title}")
        print(f"Chapters: {len(book_data.chapters)}")
    """
    print(f"Processing EPUB: {epub_path}")
    book_data = EPUBProcessor.process(epub_path)
    print(f"✓ Loaded {len(book_data.chapters)} chapters")
    return book_data


def process_pdf(pdf_path: str) -> BookData:
    """
    Process a PDF file and return BookData object.

    Example:
        def progress(msg):
            print(f"  {msg}")

        book_data = process_pdf("mybook.pdf", progress_callback=progress)
    """
    print(f"Processing PDF: {pdf_path}")

    def progress_callback(message: str):
        print(f"  {message}")

    book_data = PDFProcessor.process(pdf_path, progress_callback=progress_callback)
    print(f"✓ Loaded {len(book_data.chapters)} chapters")
    return book_data


def export_manifest(book_data: BookData, output_path: str):
    """
    Export BookData to JSON manifest file.

    The manifest format:
    {
        "title": "Book Title",
        "author": "Author Name",
        "chapters": [
            {
                "id": 1,
                "label": "Chapter 1",
                "style_prompt": "",
                "text": "Chapter text..."
            }
        ]
    }
    """
    manifest = book_data.to_manifest()

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"✓ Exported to {output_path}")


def clean_text_only(raw_text: str) -> str:
    """
    Use just the TextCleaner without file processing.

    Useful if you already have extracted text from another source.
    """
    return TextCleaner.clean(raw_text)


# Example workflow
if __name__ == "__main__":
    # Example 1: Process EPUB
    # book_data = process_epub("path/to/book.epub")

    # Example 2: Process PDF
    # book_data = process_pdf("path/to/book.pdf")

    # Example 3: Filter chapters programmatically
    # for chapter in book_data.chapters:
    #     # Disable chapters you don't want
    #     if "Table of Contents" in chapter.label:
    #         chapter.enabled = False
    #     if "Index" in chapter.label:
    #         chapter.enabled = False

    # Example 4: Export to JSON
    # export_manifest(book_data, "output/book_manifest.json")

    # Example 5: Clean raw text
    # dirty_text = "Page 12\n\nThis is some text with ﬁ ligatures..."
    # clean = clean_text_only(dirty_text)
    # print(clean)

    print("See source code for usage examples")
