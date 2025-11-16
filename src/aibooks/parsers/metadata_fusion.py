"""Metadata fusion from multiple sources."""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class MetadataSource:
    """Metadata from a single source with confidence."""

    source: str  # calibre, docling, filename, llm
    data: Dict[str, Any]
    confidence: float = 0.5  # 0.0 to 1.0


@dataclass
class FusedMetadata:
    """Fused metadata from multiple sources."""

    title: Optional[str] = None
    authors: Optional[List[str]] = None
    publisher: Optional[str] = None
    publication_date: Optional[str] = None
    isbn: Optional[str] = None
    tags: Optional[List[str]] = None
    series: Optional[str] = None
    series_index: Optional[float] = None
    language: Optional[str] = None

    # Source tracking
    sources: List[MetadataSource] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)


class MetadataFusion:
    """Fuse metadata from multiple sources."""

    # Source priority (higher = more trusted)
    SOURCE_PRIORITY = {
        "calibre": 0.9,
        "docling": 0.7,
        "llm": 0.8,
        "filename": 0.4,
        "heuristic": 0.3,
    }

    # Common filename patterns
    TITLE_AUTHOR_PATTERNS = [
        r"^(.+?)\s*-\s*(.+?)(?:\.\w+)?$",  # Title - Author.ext
        r"^(.+?)\s*by\s+(.+?)(?:\.\w+)?$",  # Title by Author.ext
        r"^(.+?)\s*\((.+?)\)(?:\.\w+)?$",  # Title (Author).ext
    ]

    ISBN_PATTERN = re.compile(
        r"(?:ISBN(?:-1[03])?:?\s*)?(?=[-0-9 ]{10,}$|[-0-9X ]{10,}$)"
        r"(?:97[89][-\s]?)?[0-9]{1,5}[-\s]?[0-9]+[-\s]?[0-9]+[-\s]?[0-9X]"
    )

    def __init__(self):
        """Initialize metadata fusion."""
        pass

    def fuse(
        self,
        calibre_metadata: Optional[Dict[str, Any]] = None,
        docling_metadata: Optional[Dict[str, Any]] = None,
        filename_metadata: Optional[Dict[str, Any]] = None,
        llm_metadata: Optional[Dict[str, Any]] = None,
    ) -> FusedMetadata:
        """Fuse metadata from multiple sources.

        Args:
            calibre_metadata: Metadata from Calibre
            docling_metadata: Metadata from Docling
            filename_metadata: Metadata from filename heuristics
            llm_metadata: Metadata from LLM inference

        Returns:
            FusedMetadata object
        """
        sources = []

        if calibre_metadata:
            sources.append(
                MetadataSource(
                    source="calibre",
                    data=calibre_metadata,
                    confidence=self.SOURCE_PRIORITY["calibre"],
                )
            )

        if docling_metadata:
            sources.append(
                MetadataSource(
                    source="docling",
                    data=docling_metadata,
                    confidence=self.SOURCE_PRIORITY["docling"],
                )
            )

        if filename_metadata:
            sources.append(
                MetadataSource(
                    source="filename",
                    data=filename_metadata,
                    confidence=self.SOURCE_PRIORITY["filename"],
                )
            )

        if llm_metadata:
            sources.append(
                MetadataSource(
                    source="llm",
                    data=llm_metadata,
                    confidence=self.SOURCE_PRIORITY["llm"],
                )
            )

        # Fuse each field
        fused = FusedMetadata(sources=sources)

        fused.title = self._fuse_field(sources, "title")
        fused.authors = self._fuse_list_field(sources, "authors")
        fused.publisher = self._fuse_field(sources, "publisher")
        fused.publication_date = self._fuse_field(sources, "publication_date")
        fused.isbn = self._fuse_isbn(sources)
        fused.tags = self._fuse_list_field(sources, "tags")
        fused.series = self._fuse_field(sources, "series")
        fused.series_index = self._fuse_numeric_field(sources, "series_index")
        fused.language = self._fuse_field(sources, "language")

        # Calculate confidence scores
        fused.confidence_scores = self._calculate_confidence_scores(sources)

        return fused

    def _fuse_field(self, sources: List[MetadataSource], field: str) -> Optional[str]:
        """Fuse a single field from multiple sources.

        Args:
            sources: List of metadata sources
            field: Field name

        Returns:
            Fused field value
        """
        candidates = []

        for source in sources:
            value = source.data.get(field)
            if value:
                # Handle list values
                if isinstance(value, list):
                    value = value[0] if value else None

                if value:
                    candidates.append((value, source.confidence))

        if not candidates:
            return None

        # Sort by confidence (descending)
        candidates.sort(key=lambda x: x[1], reverse=True)

        # Return highest confidence value
        return candidates[0][0]

    def _fuse_list_field(
        self, sources: List[MetadataSource], field: str
    ) -> Optional[List[str]]:
        """Fuse a list field from multiple sources.

        Args:
            sources: List of metadata sources
            field: Field name

        Returns:
            Fused list of values
        """
        all_values = []

        for source in sources:
            value = source.data.get(field)
            if value:
                if isinstance(value, list):
                    all_values.extend(value)
                elif isinstance(value, str):
                    # Split by common separators
                    values = [v.strip() for v in value.replace("&", ",").split(",")]
                    all_values.extend(values)

        if not all_values:
            return None

        # Deduplicate while preserving order
        seen = set()
        unique_values = []
        for value in all_values:
            if value and value not in seen:
                seen.add(value)
                unique_values.append(value)

        return unique_values if unique_values else None

    def _fuse_numeric_field(
        self, sources: List[MetadataSource], field: str
    ) -> Optional[float]:
        """Fuse a numeric field from multiple sources.

        Args:
            sources: List of metadata sources
            field: Field name

        Returns:
            Fused numeric value
        """
        candidates = []

        for source in sources:
            value = source.data.get(field)
            if value is not None:
                try:
                    numeric_value = float(value)
                    candidates.append((numeric_value, source.confidence))
                except (ValueError, TypeError):
                    continue

        if not candidates:
            return None

        # Sort by confidence
        candidates.sort(key=lambda x: x[1], reverse=True)

        return candidates[0][0]

    def _fuse_isbn(self, sources: List[MetadataSource]) -> Optional[str]:
        """Fuse ISBN with validation.

        Args:
            sources: List of metadata sources

        Returns:
            Validated ISBN
        """
        isbn = self._fuse_field(sources, "isbn")

        if isbn:
            # Validate and normalize ISBN
            isbn = self._normalize_isbn(isbn)

        return isbn

    def _normalize_isbn(self, isbn: str) -> Optional[str]:
        """Normalize and validate ISBN.

        Args:
            isbn: Raw ISBN string

        Returns:
            Normalized ISBN or None if invalid
        """
        # Remove hyphens and spaces
        isbn = isbn.replace("-", "").replace(" ", "")

        # Validate length
        if len(isbn) == 10 or len(isbn) == 13:
            # Could add checksum validation here
            return isbn

        return None

    def _calculate_confidence_scores(
        self, sources: List[MetadataSource]
    ) -> Dict[str, float]:
        """Calculate confidence scores for fused metadata.

        Args:
            sources: List of metadata sources

        Returns:
            Dictionary of field confidence scores
        """
        scores = {}

        # For each field, calculate weighted average of source confidences
        fields = ["title", "authors", "publisher", "publication_date", "isbn"]

        for field in fields:
            total_confidence = 0.0
            count = 0

            for source in sources:
                if source.data.get(field):
                    total_confidence += source.confidence
                    count += 1

            scores[field] = total_confidence / count if count > 0 else 0.0

        return scores

    def extract_from_filename(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from filename using heuristics.

        Args:
            file_path: Path to file

        Returns:
            Dictionary of extracted metadata
        """
        metadata = {}

        filename = file_path.stem  # Filename without extension

        # Try common patterns
        for pattern in self.TITLE_AUTHOR_PATTERNS:
            match = re.match(pattern, filename, re.IGNORECASE)
            if match:
                metadata["title"] = match.group(1).strip()
                metadata["authors"] = [match.group(2).strip()]
                break

        # If no match, use filename as title
        if "title" not in metadata:
            metadata["title"] = filename

        # Look for ISBN in filename
        isbn_match = self.ISBN_PATTERN.search(filename)
        if isbn_match:
            metadata["isbn"] = self._normalize_isbn(isbn_match.group(0))

        # Look for year
        year_match = re.search(r"\b(19|20)\d{2}\b", filename)
        if year_match:
            metadata["publication_date"] = year_match.group(0)

        logger.debug(f"Extracted filename metadata: {metadata}")

        return metadata
