"""Tests for parsers and format detection."""

import pytest
from pathlib import Path
import tempfile

from aibooks.parsers.format_detector import FormatDetector, DocumentFormat
from aibooks.parsers.metadata_fusion import MetadataFusion
from aibooks.utils.text_cleaner import TextCleaner


def test_format_detector_extension():
    """Test format detection by extension."""
    detector = FormatDetector()

    assert detector.detect_from_extension(Path("test.pdf")) == DocumentFormat.PDF
    assert detector.detect_from_extension(Path("test.epub")) == DocumentFormat.EPUB
    assert detector.detect_from_extension(Path("test.mobi")) == DocumentFormat.MOBI
    assert detector.detect_from_extension(Path("test.docx")) == DocumentFormat.DOCX
    assert detector.detect_from_extension(Path("test.txt")) == DocumentFormat.TXT


def test_format_detector_content():
    """Test format detection by content."""
    detector = FormatDetector()

    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
        # PDF magic bytes
        f.write(b'%PDF-1.4\n')
        pdf_path = Path(f.name)

    try:
        assert detector.detect_from_content(pdf_path) == DocumentFormat.PDF
    finally:
        pdf_path.unlink()


def test_format_detector_checks():
    """Test format detector helper methods."""
    detector = FormatDetector()

    assert detector.is_ebook(DocumentFormat.EPUB) is True
    assert detector.is_ebook(DocumentFormat.PDF) is False

    assert detector.supports_calibre_metadata(DocumentFormat.EPUB) is True
    assert detector.supports_calibre_metadata(DocumentFormat.TXT) is False

    assert detector.requires_ocr(DocumentFormat.PDF) is True
    assert detector.requires_ocr(DocumentFormat.EPUB) is False


def test_metadata_fusion_field():
    """Test metadata fusion for single field."""
    fusion = MetadataFusion()

    from aibooks.parsers.metadata_fusion import MetadataSource

    sources = [
        MetadataSource("calibre", {"title": "Book Title"}, 0.9),
        MetadataSource("filename", {"title": "book_title"}, 0.4),
    ]

    result = fusion._fuse_field(sources, "title")
    assert result == "Book Title"  # Should pick higher confidence


def test_metadata_fusion_list_field():
    """Test metadata fusion for list fields."""
    fusion = MetadataFusion()

    from aibooks.parsers.metadata_fusion import MetadataSource

    sources = [
        MetadataSource("calibre", {"authors": ["Author One", "Author Two"]}, 0.9),
        MetadataSource("filename", {"authors": ["Author One"]}, 0.4),
    ]

    result = fusion._fuse_list_field(sources, "authors")
    assert "Author One" in result
    assert "Author Two" in result
    assert len(result) == 2  # Should deduplicate


def test_metadata_fusion_filename_extraction():
    """Test extracting metadata from filename."""
    fusion = MetadataFusion()

    # Title - Author pattern
    metadata = fusion.extract_from_filename(Path("The Great Gatsby - F. Scott Fitzgerald.pdf"))
    assert metadata.get("title") == "The Great Gatsby"
    assert "F. Scott Fitzgerald" in metadata.get("authors", [])

    # Title by Author pattern
    metadata = fusion.extract_from_filename(Path("1984 by George Orwell.epub"))
    assert metadata.get("title") == "1984"
    assert "George Orwell" in metadata.get("authors", [])


def test_text_cleaner_hyphenation():
    """Test removing hyphenation at line breaks."""
    cleaner = TextCleaner()

    text = "This is a sen-\ntence with broken words."
    cleaned = cleaner.remove_hyphenation(text)
    assert "sen-\n" not in cleaned
    assert "sentence" in cleaned


def test_text_cleaner_unicode():
    """Test Unicode normalization."""
    cleaner = TextCleaner()

    # Text with encoding issues
    text = "Café\u0301"  # Combining accent
    cleaned = cleaner.normalize_unicode(text)
    assert cleaned is not None


def test_text_cleaner_quotes():
    """Test quote normalization."""
    cleaner = TextCleaner()

    text = ""Smart quotes" and 'smart apostrophes'"
    cleaned = cleaner.normalize_quotes(text)
    assert '"Smart quotes"' in cleaned
    assert "'" in cleaned


def test_text_cleaner_whitespace():
    """Test whitespace normalization."""
    cleaner = TextCleaner()

    text = "Too    many     spaces\n\n\n\nAnd newlines"
    cleaned = cleaner.normalize_whitespace(text)
    assert "    " not in cleaned
    assert "\n\n\n\n" not in cleaned


def test_text_cleaner_full():
    """Test full cleaning pipeline."""
    cleaner = TextCleaner()

    text = """This is a sen-
    tence with "smart quotes" and    extra spaces.



    Page 42

    Another paragraph."""

    cleaned = cleaner.clean(text)
    assert "sen-\n" not in cleaned
    assert '"smart quotes"' in cleaned
    assert "    " not in cleaned
