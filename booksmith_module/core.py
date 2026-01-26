"""
Core data models and text cleaning engine for BookSmith.
Pure Python with no GUI dependencies - ready for pipeline integration.
"""

import re
import ftfy
import unicodedata
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Chapter:
    """Represents a single chapter/section of a book."""
    id: int
    label: str
    text: str
    style_prompt: str = ""
    enabled: bool = True


class BookData:
    """Central data store for a processed book."""

    def __init__(self):
        self.title: str = ""
        self.author: str = ""
        self.chapters: List[Chapter] = []
        self.source_file: str = ""

    def to_manifest(self) -> Dict:
        """Generate JSON manifest with only enabled chapters (renumbered sequentially)."""
        enabled_chapters = [ch for ch in self.chapters if ch.enabled]

        return {
            "title": self.title,
            "author": self.author,
            "chapters": [
                {
                    "id": idx,
                    "label": ch.label,
                    "style_prompt": ch.style_prompt,
                    "text": ch.text
                }
                for idx, ch in enumerate(enabled_chapters, start=1)
            ]
        }


class TextCleaner:
    """
    Aggressive text sanitization for LLM-based TTS models.

    Qwen3-TTS/CosyVoice are sensitive to:
    - Page numbers and headers (can trigger repetition loops)
    - HTML entities and invisible characters (hallucination triggers)
    - Ligatures and special unicode (breaks tokenization)
    - Footnote markers and reference symbols (interpreted as prompts)
    """

    @staticmethod
    def clean(text: str) -> str:
        """Master cleaning pipeline."""
        if not text:
            return ""

        # Stage 1: Fix encoding issues (mojibake, broken UTF-8)
        text = ftfy.fix_text(text)

        # Stage 2: Normalize unicode (NFC form for consistent rendering)
        text = unicodedata.normalize('NFC', text)

        # Stage 3: Remove common PDF/EPUB artifacts
        text = TextCleaner._remove_page_numbers(text)
        text = TextCleaner._remove_headers_footers(text)
        text = TextCleaner._fix_ligatures(text)

        # Stage 4: Remove tables (unreadable for TTS)
        text = TextCleaner._remove_tables(text)

        # Stage 5: Clean HTML entities and invisible characters
        text = TextCleaner._remove_html_artifacts(text)
        text = TextCleaner._remove_invisible_chars(text)

        # Stage 6: Normalize whitespace (critical for TTS chunking)
        text = TextCleaner._normalize_whitespace(text)

        # Stage 7: Remove potential prompt injections
        text = TextCleaner._remove_control_sequences(text)

        return text.strip()

    @staticmethod
    def _remove_page_numbers(text: str) -> str:
        """Remove common page number patterns."""
        patterns = [
            r'^\s*Page\s+\d+\s*$',           # "Page 12"
            r'^\s*-\s*\d+\s*-\s*$',          # "- 12 -"
            r'^\s*\d+\s*$',                  # Standalone numbers on lines
            r'\[\s*\d+\s*\]',                # "[12]"
            r'^\s*\d+\s*\|',                 # "12 |"
        ]
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE)
        return text

    @staticmethod
    def _remove_headers_footers(text: str) -> str:
        """Remove repeated header/footer content."""
        # Remove lines that are all caps (often headers)
        text = re.sub(r'^[A-Z\s]{20,}$', '', text, flags=re.MULTILINE)

        # Remove copyright notices
        text = re.sub(r'©.*?All rights reserved\.?', '', text, flags=re.IGNORECASE)

        return text

    @staticmethod
    def _fix_ligatures(text: str) -> str:
        """
        Replace typographic ligatures with normal characters.
        Critical: TTS models may not handle these properly.
        """
        ligature_map = {
            'ﬁ': 'fi',
            'ﬂ': 'fl',
            'ﬀ': 'ff',
            'ﬃ': 'ffi',
            'ﬄ': 'ffl',
            'ﬆ': 'st',
            'Ꜳ': 'AA',
            'ꜳ': 'aa',
        }
        for ligature, replacement in ligature_map.items():
            text = text.replace(ligature, replacement)
        return text

    @staticmethod
    def _remove_tables(text: str) -> str:
        """Remove markdown tables and table-like content."""
        # Remove markdown tables (with header separators)
        table_pattern = r'\|[^\n]*\|\s*\n\s*\|[-:|\s]+\|[\s\S]*?(?=\n\n|\n[^|]|\Z)'
        text = re.sub(table_pattern, '\n', text, flags=re.MULTILINE)

        # Remove standalone table rows
        text = re.sub(r'^\s*\|[^\n]+\|\s*$', '', text, flags=re.MULTILINE)

        # Remove table caption patterns
        text = re.sub(r'^Table\s+\d+\.?\d*[:\s]+.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)

        return text

    @staticmethod
    def _remove_html_artifacts(text: str) -> str:
        """Clean HTML entities and tags."""
        # Decode HTML entities
        import html
        text = html.unescape(text)

        # Remove any remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove common EPUB metadata artifacts
        text = re.sub(r'\{[^}]*calibre[^}]*\}', '', text, flags=re.IGNORECASE)

        return text

    @staticmethod
    def _remove_invisible_chars(text: str) -> str:
        """Remove zero-width and non-printable characters."""
        invisible_chars = [
            '\u200B',  # Zero-width space
            '\u200C',  # Zero-width non-joiner
            '\u200D',  # Zero-width joiner
            '\uFEFF',  # Zero-width no-break space (BOM)
            '\u00AD',  # Soft hyphen
        ]
        for char in invisible_chars:
            text = text.replace(char, '')

        # Remove other control characters except newlines/tabs
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

        return text

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Normalize whitespace for consistent TTS chunking."""
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)

        # Replace multiple newlines with double newline (paragraph breaks)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove trailing whitespace from lines
        text = '\n'.join(line.rstrip() for line in text.split('\n'))

        return text

    @staticmethod
    def _remove_control_sequences(text: str) -> str:
        """Remove patterns that might be interpreted as system prompts."""
        # Remove markdown-style annotations
        text = re.sub(r'\[NOTE:.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[INSTRUCTION:.*?\]', '', text, flags=re.IGNORECASE)

        # Remove excessive punctuation (!!!!, ????)
        text = re.sub(r'([!?.])\1{3,}', r'\1', text)

        return text
