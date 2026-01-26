"""
Book file processors for EPUB and PDF formats.
Uses Docling AI for intelligent PDF layout analysis.
"""

import re
from pathlib import Path
from typing import List, Optional, Callable

# EPUB processing
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

# PDF processing
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
import pymupdf  # For PDF bookmark/outline extraction

from .core import BookData, Chapter, TextCleaner


class EPUBProcessor:
    """Extract and clean chapters from EPUB files."""

    @staticmethod
    def process(file_path: str) -> BookData:
        """Main entry point for EPUB processing."""
        book_data = BookData()
        book_data.source_file = file_path

        # Load EPUB
        book = epub.read_epub(file_path)

        # Extract metadata
        book_data.title = EPUBProcessor._get_metadata(book, 'title')
        book_data.author = EPUBProcessor._get_metadata(book, 'creator')

        # Extract chapters
        chapters = EPUBProcessor._extract_chapters(book)
        book_data.chapters = chapters

        return book_data

    @staticmethod
    def _get_metadata(book: epub.EpubBook, field: str) -> str:
        """Extract metadata field from EPUB."""
        try:
            value = book.get_metadata('DC', field)
            if value:
                return value[0][0] if isinstance(value[0], tuple) else value[0]
        except:
            pass
        return "Unknown"

    @staticmethod
    def _extract_chapters(book: epub.EpubBook) -> List[Chapter]:
        """Extract chapters from EPUB spine."""
        chapters = []
        chapter_id = 1

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Parse HTML content
                soup = BeautifulSoup(item.get_content(), 'html.parser')

                # Extract text
                text = soup.get_text(separator='\n')

                # Clean text aggressively
                text = TextCleaner.clean(text)

                # Skip if empty after cleaning
                if not text or len(text.strip()) < 100:
                    continue

                # Try to find chapter title
                label = EPUBProcessor._extract_title(soup, item)

                chapters.append(Chapter(
                    id=chapter_id,
                    label=label,
                    text=text,
                    style_prompt=""
                ))
                chapter_id += 1

        return chapters

    @staticmethod
    def _extract_title(soup: BeautifulSoup, item) -> str:
        """Attempt to extract chapter title from HTML."""
        # Try h1, h2 tags first
        for tag in ['h1', 'h2', 'h3']:
            heading = soup.find(tag)
            if heading:
                title = heading.get_text().strip()
                if title:
                    return title

        # Fallback to filename
        if hasattr(item, 'file_name'):
            return Path(item.file_name).stem.replace('_', ' ').title()

        return "Untitled Chapter"


class PDFProcessor:
    """Extract and clean chapters from PDF files using Docling (IBM AI)."""

    # Shared converter instance (models are loaded once and cached)
    _converter = None

    @staticmethod
    def process(file_path: str, progress_callback: Optional[Callable[[str], None]] = None) -> BookData:
        """
        Main entry point for PDF processing.

        Args:
            file_path: Path to the PDF file
            progress_callback: Optional function to call with progress updates

        Returns:
            BookData object with extracted chapters
        """
        book_data = BookData()
        book_data.source_file = file_path

        # Initialize Docling converter (first time only)
        if PDFProcessor._converter is None:
            if progress_callback:
                progress_callback("Loading Docling AI models (first time only)...")

            # Configure pipeline for optimal TTS text extraction
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = False  # Disable OCR unless needed (faster)
            pipeline_options.do_table_structure = False  # Skip tables for audiobooks

            PDFProcessor._converter = DocumentConverter(
                format_options={
                    "pdf": PdfFormatOption(pipeline_options=pipeline_options)
                }
            )

        # Convert PDF to structured markdown
        if progress_callback:
            progress_callback("Analyzing PDF layout with AI...")

        try:
            result = PDFProcessor._converter.convert(file_path)
        except Exception as e:
            raise Exception(f"Failed to process PDF: {str(e)}")

        # Extract metadata
        if progress_callback:
            progress_callback("Extracting metadata...")

        doc_meta = result.document.meta if hasattr(result.document, 'meta') else {}
        book_data.title = doc_meta.get('title', '') or Path(file_path).stem.replace('_', ' ').title()
        book_data.author = doc_meta.get('author', '') or 'Unknown'

        # Try to extract chapters from PDF bookmarks first (most reliable)
        if progress_callback:
            progress_callback("Checking for PDF bookmarks...")

        chapters = PDFProcessor._extract_chapters_from_bookmarks(file_path, progress_callback)

        if chapters:
            if progress_callback:
                progress_callback(f"Found {len(chapters)} chapters from PDF bookmarks")
            book_data.chapters = chapters
        else:
            # Fallback: Parse content structure using Docling
            if progress_callback:
                progress_callback("No bookmarks found, analyzing document structure...")

            # Export to markdown (Docling automatically removes headers/footers)
            markdown_text = result.document.export_to_markdown()

            # Parse markdown into chapters
            if progress_callback:
                progress_callback("Detecting chapters from content...")

            chapters = PDFProcessor._parse_markdown_chapters(markdown_text)
            book_data.chapters = chapters

        return book_data

    @staticmethod
    def _extract_chapters_from_bookmarks(file_path: str, progress_callback: Optional[Callable[[str], None]] = None) -> List[Chapter]:
        """
        Extract chapters from PDF bookmarks/outline (most reliable method).
        Returns empty list if no suitable bookmarks found.
        """
        try:
            pdf_doc = pymupdf.open(file_path)
            toc = pdf_doc.get_toc()

            if not toc:
                pdf_doc.close()
                return []

            # Filter TOC to only top-level entries (level 1)
            chapter_bookmarks = [item for item in toc if item[0] == 1]

            if len(chapter_bookmarks) < 2:
                pdf_doc.close()
                return []

            chapters = []

            for i, bookmark in enumerate(chapter_bookmarks):
                level, title, page_num = bookmark

                # Get the page range for this chapter
                start_page = page_num - 1

                # End page is either the start of next chapter or end of document
                if i + 1 < len(chapter_bookmarks):
                    end_page = chapter_bookmarks[i + 1][2] - 2
                else:
                    end_page = pdf_doc.page_count - 1

                # Extract text from this chapter's pages
                chapter_text = ""
                for page_idx in range(start_page, end_page + 1):
                    if page_idx < 0 or page_idx >= pdf_doc.page_count:
                        continue
                    page = pdf_doc[page_idx]
                    chapter_text += page.get_text()

                # Clean the extracted text
                chapter_text = TextCleaner.clean(chapter_text)

                # Skip if chapter has very little text
                if len(chapter_text.strip()) < 100:
                    continue

                chapters.append(Chapter(
                    id=len(chapters) + 1,
                    label=title.strip(),
                    text=chapter_text.strip(),
                    style_prompt=""
                ))

            pdf_doc.close()

            return chapters if len(chapters) >= 2 else []

        except Exception as e:
            if progress_callback:
                progress_callback(f"Bookmark extraction failed: {str(e)}")
            return []

    @staticmethod
    def _parse_markdown_chapters(markdown_text: str) -> List[Chapter]:
        """Split Docling markdown into chapters."""
        markdown_text = TextCleaner.clean(markdown_text)

        chapters = []
        current_chapter = None
        chapter_id = 1

        lines = markdown_text.split('\n')

        for line in lines:
            header_match = re.match(r'^##\s+(.+)$', line)

            if header_match:
                label = header_match.group(1).strip()

                # Filter out subsection headers
                is_likely_subsection = (
                    label.islower() or
                    (len(label) < 20 and not label[0].isupper())
                )

                if is_likely_subsection:
                    if current_chapter is not None:
                        current_chapter['text'] += line + '\n'
                else:
                    # Save previous chapter
                    if current_chapter and current_chapter['text'].strip():
                        chapters.append(Chapter(
                            id=chapter_id,
                            label=current_chapter['label'],
                            text=current_chapter['text'].strip(),
                            style_prompt=""
                        ))
                        chapter_id += 1

                    # Start new chapter
                    current_chapter = {
                        'label': label,
                        'text': ''
                    }
            else:
                if current_chapter is not None:
                    current_chapter['text'] += line + '\n'

        # Add final chapter
        if current_chapter and current_chapter['text'].strip():
            chapters.append(Chapter(
                id=chapter_id,
                label=current_chapter['label'],
                text=current_chapter['text'].strip(),
                style_prompt=""
            ))

        # Filter out table-only chapters
        filtered_chapters = []
        for chapter in chapters:
            if re.match(r'^Table\s+\d+\.?\d*', chapter.label, re.IGNORECASE):
                continue
            if len(chapter.text.strip()) < 100:
                continue
            filtered_chapters.append(chapter)

        chapters = filtered_chapters

        # Fallback: if no chapters detected
        if not chapters:
            chapters = PDFProcessor._fallback_chapter_detection(markdown_text)

        # Final fallback: single chapter
        if not chapters:
            chapters.append(Chapter(
                id=1,
                label="Full Text",
                text=markdown_text,
                style_prompt=""
            ))

        return chapters

    @staticmethod
    def _fallback_chapter_detection(text: str) -> List[Chapter]:
        """Fallback chapter detection when Docling doesn't find markdown headers."""
        chapters = []
        chapter_id = 1

        chapter_pattern = r'^(?:Chapter|CHAPTER|Ch\.|CH\.)\s+(?:\d+|[IVX]+|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)[:\s]'

        lines = text.split('\n')
        current_chapter = None

        for i, line in enumerate(lines):
            if re.match(chapter_pattern, line.strip()):
                if current_chapter and current_chapter['text'].strip():
                    chapters.append(Chapter(
                        id=chapter_id,
                        label=current_chapter['label'],
                        text=current_chapter['text'].strip(),
                        style_prompt=""
                    ))
                    chapter_id += 1

                label = line.strip()

                if i + 1 < len(lines) and lines[i + 1].strip():
                    next_line = lines[i + 1].strip()
                    if not re.match(chapter_pattern, next_line) and len(next_line) < 100:
                        label += " " + next_line

                current_chapter = {
                    'label': label[:100],
                    'text': ''
                }
            else:
                if current_chapter is not None:
                    current_chapter['text'] += line + '\n'

        if current_chapter and current_chapter['text'].strip():
            chapters.append(Chapter(
                id=chapter_id,
                label=current_chapter['label'],
                text=current_chapter['text'].strip(),
                style_prompt=""
            ))

        return chapters
