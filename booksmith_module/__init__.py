"""
BookSmith Module - TTS Pre-Processing for Audiobook Pipelines

Extracted from BookSmith GUI application for integration into vox-1.
Provides clean text extraction from EPUB/PDF files optimized for TTS models.
"""

from .core import TextCleaner, BookData, Chapter
from .processors import EPUBProcessor, PDFProcessor

__all__ = [
    'TextCleaner',
    'BookData',
    'Chapter',
    'EPUBProcessor',
    'PDFProcessor'
]

__version__ = '1.0.0'
