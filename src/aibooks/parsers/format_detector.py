"""Document format detection."""

import mimetypes
from enum import Enum
from pathlib import Path
from typing import Optional
import magic


class DocumentFormat(str, Enum):
    """Supported document formats."""

    PDF = "pdf"
    EPUB = "epub"
    MOBI = "mobi"
    AZW3 = "azw3"
    DOCX = "docx"
    DOC = "doc"
    RTF = "rtf"
    TXT = "txt"
    HTML = "html"
    MD = "md"
    IMAGE = "image"
    UNKNOWN = "unknown"


class FormatDetector:
    """Detect document format from file."""

    # Extension to format mapping
    EXTENSION_MAP = {
        ".pdf": DocumentFormat.PDF,
        ".epub": DocumentFormat.EPUB,
        ".mobi": DocumentFormat.MOBI,
        ".azw3": DocumentFormat.AZW3,
        ".azw": DocumentFormat.AZW3,
        ".docx": DocumentFormat.DOCX,
        ".doc": DocumentFormat.DOC,
        ".rtf": DocumentFormat.RTF,
        ".txt": DocumentFormat.TXT,
        ".text": DocumentFormat.TXT,
        ".html": DocumentFormat.HTML,
        ".htm": DocumentFormat.HTML,
        ".md": DocumentFormat.MD,
        ".markdown": DocumentFormat.MD,
        ".jpg": DocumentFormat.IMAGE,
        ".jpeg": DocumentFormat.IMAGE,
        ".png": DocumentFormat.IMAGE,
        ".tiff": DocumentFormat.IMAGE,
        ".tif": DocumentFormat.IMAGE,
    }

    # MIME type to format mapping
    MIME_MAP = {
        "application/pdf": DocumentFormat.PDF,
        "application/epub+zip": DocumentFormat.EPUB,
        "application/x-mobipocket-ebook": DocumentFormat.MOBI,
        "application/vnd.amazon.ebook": DocumentFormat.AZW3,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentFormat.DOCX,
        "application/msword": DocumentFormat.DOC,
        "application/rtf": DocumentFormat.RTF,
        "text/plain": DocumentFormat.TXT,
        "text/html": DocumentFormat.HTML,
        "text/markdown": DocumentFormat.MD,
        "image/jpeg": DocumentFormat.IMAGE,
        "image/png": DocumentFormat.IMAGE,
        "image/tiff": DocumentFormat.IMAGE,
    }

    def __init__(self):
        """Initialize format detector."""
        # Initialize mimetypes
        mimetypes.init()

    def detect_from_extension(self, file_path: Path) -> DocumentFormat:
        """Detect format from file extension.

        Args:
            file_path: Path to file

        Returns:
            Detected DocumentFormat
        """
        extension = file_path.suffix.lower()
        return self.EXTENSION_MAP.get(extension, DocumentFormat.UNKNOWN)

    def detect_from_mime(self, file_path: Path) -> DocumentFormat:
        """Detect format from MIME type.

        Args:
            file_path: Path to file

        Returns:
            Detected DocumentFormat
        """
        try:
            # Try python-magic first (more accurate)
            mime_type = magic.from_file(str(file_path), mime=True)
        except Exception:
            # Fallback to mimetypes
            mime_type, _ = mimetypes.guess_type(str(file_path))

        if mime_type:
            return self.MIME_MAP.get(mime_type, DocumentFormat.UNKNOWN)

        return DocumentFormat.UNKNOWN

    def detect_from_content(self, file_path: Path) -> DocumentFormat:
        """Detect format from file content (magic bytes).

        Args:
            file_path: Path to file

        Returns:
            Detected DocumentFormat
        """
        try:
            with open(file_path, "rb") as f:
                header = f.read(16)

            # PDF
            if header.startswith(b"%PDF"):
                return DocumentFormat.PDF

            # EPUB (ZIP archive with specific structure)
            if header.startswith(b"PK\x03\x04"):
                # Could be EPUB, DOCX, or other ZIP-based format
                # Read more to differentiate
                with open(file_path, "rb") as f:
                    content = f.read(1024)
                    if b"mimetypeapplication/epub+zip" in content:
                        return DocumentFormat.EPUB
                    elif b"word/" in content:
                        return DocumentFormat.DOCX

            # MOBI
            if header[60:68] == b"BOOKMOBI":
                return DocumentFormat.MOBI

            # RTF
            if header.startswith(b"{\\rtf"):
                return DocumentFormat.RTF

            # HTML
            if b"<html" in header.lower() or b"<!doctype" in header.lower():
                return DocumentFormat.HTML

            # Image formats
            if header.startswith(b"\xff\xd8\xff"):  # JPEG
                return DocumentFormat.IMAGE
            if header.startswith(b"\x89PNG"):  # PNG
                return DocumentFormat.IMAGE
            if header.startswith(b"II*\x00") or header.startswith(b"MM\x00*"):  # TIFF
                return DocumentFormat.IMAGE

        except Exception:
            pass

        return DocumentFormat.UNKNOWN

    def detect(self, file_path: Path) -> DocumentFormat:
        """Detect format using multiple methods.

        Args:
            file_path: Path to file

        Returns:
            Detected DocumentFormat
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Try extension first (fastest)
        fmt = self.detect_from_extension(file_path)
        if fmt != DocumentFormat.UNKNOWN:
            return fmt

        # Try content detection (most accurate)
        fmt = self.detect_from_content(file_path)
        if fmt != DocumentFormat.UNKNOWN:
            return fmt

        # Try MIME type (fallback)
        fmt = self.detect_from_mime(file_path)

        return fmt

    def is_ebook(self, fmt: DocumentFormat) -> bool:
        """Check if format is an ebook format.

        Args:
            fmt: Document format

        Returns:
            True if ebook format
        """
        return fmt in {DocumentFormat.EPUB, DocumentFormat.MOBI, DocumentFormat.AZW3}

    def supports_calibre_metadata(self, fmt: DocumentFormat) -> bool:
        """Check if format supports Calibre metadata extraction.

        Args:
            fmt: Document format

        Returns:
            True if Calibre can extract metadata
        """
        return fmt in {
            DocumentFormat.EPUB,
            DocumentFormat.MOBI,
            DocumentFormat.AZW3,
            DocumentFormat.PDF,
        }

    def requires_ocr(self, fmt: DocumentFormat) -> bool:
        """Check if format may require OCR.

        Args:
            fmt: Document format

        Returns:
            True if OCR may be needed
        """
        return fmt in {DocumentFormat.PDF, DocumentFormat.IMAGE}
