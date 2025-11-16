"""Docling-based document parser."""

from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import ConversionStatus
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
    DOCLING_AVAILABLE = True
except ImportError:
    logger.warning("Docling not available - parser will be limited")
    DOCLING_AVAILABLE = False

from ..utils.text_cleaner import clean_text


@dataclass
class ParsedDocument:
    """Parsed document result."""

    text: str
    markdown: str
    metadata: Dict[str, Any]
    chapters: list[Dict[str, Any]]
    tables: list[Dict[str, Any]]
    figures: list[Dict[str, Any]]
    pages: int
    words: int
    success: bool
    error: Optional[str] = None


class DoclingParser:
    """Document parser using Docling."""

    def __init__(self, enable_ocr: bool = True, enable_vision: bool = True):
        """Initialize Docling parser.

        Args:
            enable_ocr: Enable OCR for scanned documents
            enable_vision: Enable vision model for better layout understanding
        """
        if not DOCLING_AVAILABLE:
            raise ImportError("Docling is not installed. Install with: pip install docling")

        self.enable_ocr = enable_ocr
        self.enable_vision = enable_vision

        # Configure pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = enable_ocr
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

        # Initialize converter
        self.converter = DocumentConverter(
            allowed_formats=[
                ".pdf",
                ".docx",
                ".pptx",
                ".html",
                ".jpg",
                ".png",
                ".tiff",
            ],
            pdf_backend=PyPdfiumDocumentBackend,
            pdf_pipeline_options=pipeline_options,
        )

        logger.info(f"Docling parser initialized (OCR={enable_ocr}, Vision={enable_vision})")

    def parse(self, file_path: Path) -> ParsedDocument:
        """Parse document using Docling.

        Args:
            file_path: Path to document

        Returns:
            ParsedDocument with extracted content
        """
        if not file_path.exists():
            return ParsedDocument(
                text="",
                markdown="",
                metadata={},
                chapters=[],
                tables=[],
                figures=[],
                pages=0,
                words=0,
                success=False,
                error=f"File not found: {file_path}",
            )

        try:
            logger.info(f"Parsing document with Docling: {file_path.name}")

            # Convert document
            result = self.converter.convert(str(file_path))

            # Check conversion status
            if result.status != ConversionStatus.SUCCESS:
                return ParsedDocument(
                    text="",
                    markdown="",
                    metadata={},
                    chapters=[],
                    tables=[],
                    figures=[],
                    pages=0,
                    words=0,
                    success=False,
                    error=f"Conversion failed with status: {result.status}",
                )

            # Extract text
            text = result.document.export_to_text()
            markdown = result.document.export_to_markdown()

            # Extract metadata
            metadata = self._extract_metadata(result)

            # Extract chapters
            chapters = self._extract_chapters(result)

            # Extract tables
            tables = self._extract_tables(result)

            # Extract figures
            figures = self._extract_figures(result)

            # Calculate statistics
            pages = metadata.get("pages", 0)
            words = len(text.split())

            # Clean text
            cleaned_text = clean_text(text)

            logger.info(
                f"Successfully parsed {file_path.name}: "
                f"{pages} pages, {words} words, "
                f"{len(chapters)} chapters, {len(tables)} tables"
            )

            return ParsedDocument(
                text=cleaned_text,
                markdown=markdown,
                metadata=metadata,
                chapters=chapters,
                tables=tables,
                figures=figures,
                pages=pages,
                words=words,
                success=True,
            )

        except Exception as e:
            logger.error(f"Error parsing document with Docling: {e}", exc_info=True)
            return ParsedDocument(
                text="",
                markdown="",
                metadata={},
                chapters=[],
                tables=[],
                figures=[],
                pages=0,
                words=0,
                success=False,
                error=str(e),
            )

    def _extract_metadata(self, result) -> Dict[str, Any]:
        """Extract metadata from Docling result.

        Args:
            result: Docling conversion result

        Returns:
            Dictionary of metadata
        """
        metadata = {}

        try:
            doc = result.document

            # Basic metadata
            if hasattr(doc, "metadata"):
                meta = doc.metadata
                metadata["title"] = getattr(meta, "title", None)
                metadata["author"] = getattr(meta, "author", None)
                metadata["subject"] = getattr(meta, "subject", None)
                metadata["keywords"] = getattr(meta, "keywords", None)
                metadata["creator"] = getattr(meta, "creator", None)
                metadata["producer"] = getattr(meta, "producer", None)
                metadata["creation_date"] = getattr(meta, "creation_date", None)
                metadata["modification_date"] = getattr(meta, "modification_date", None)

            # Page count
            if hasattr(doc, "pages"):
                metadata["pages"] = len(doc.pages)

        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")

        return metadata

    def _extract_chapters(self, result) -> list[Dict[str, Any]]:
        """Extract chapters from Docling result.

        Args:
            result: Docling conversion result

        Returns:
            List of chapter dictionaries
        """
        chapters = []

        try:
            doc = result.document

            # Look for headings to identify chapters
            current_chapter = None
            chapter_content = []

            for item in doc.iterate_items():
                if hasattr(item, "label") and "heading" in item.label.lower():
                    # Save previous chapter
                    if current_chapter:
                        chapters.append({
                            "title": current_chapter,
                            "content": "\n".join(chapter_content),
                            "level": 1,  # Could extract from heading level
                        })

                    # Start new chapter
                    current_chapter = item.text
                    chapter_content = []
                elif current_chapter:
                    chapter_content.append(item.text)

            # Save last chapter
            if current_chapter:
                chapters.append({
                    "title": current_chapter,
                    "content": "\n".join(chapter_content),
                    "level": 1,
                })

        except Exception as e:
            logger.warning(f"Error extracting chapters: {e}")

        return chapters

    def _extract_tables(self, result) -> list[Dict[str, Any]]:
        """Extract tables from Docling result.

        Args:
            result: Docling conversion result

        Returns:
            List of table dictionaries
        """
        tables = []

        try:
            doc = result.document

            for idx, table in enumerate(doc.tables):
                tables.append({
                    "index": idx,
                    "caption": getattr(table, "caption", None),
                    "data": table.export_to_dataframe().to_dict() if hasattr(table, "export_to_dataframe") else {},
                    "markdown": table.export_to_markdown() if hasattr(table, "export_to_markdown") else "",
                })

        except Exception as e:
            logger.warning(f"Error extracting tables: {e}")

        return tables

    def _extract_figures(self, result) -> list[Dict[str, Any]]:
        """Extract figures from Docling result.

        Args:
            result: Docling conversion result

        Returns:
            List of figure dictionaries
        """
        figures = []

        try:
            doc = result.document

            for idx, figure in enumerate(doc.pictures):
                figures.append({
                    "index": idx,
                    "caption": getattr(figure, "caption", None),
                    "description": getattr(figure, "description", None),
                })

        except Exception as e:
            logger.warning(f"Error extracting figures: {e}")

        return figures
