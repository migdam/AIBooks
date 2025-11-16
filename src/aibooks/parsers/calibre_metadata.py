"""Calibre metadata extraction using ebook-meta."""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from loguru import logger

from ..core.config import get_config


@dataclass
class CalibreMetadata:
    """Calibre extracted metadata."""

    title: Optional[str] = None
    authors: Optional[list[str]] = None
    author_sort: Optional[str] = None
    publisher: Optional[str] = None
    publication_date: Optional[str] = None
    isbn: Optional[str] = None
    tags: Optional[list[str]] = None
    series: Optional[str] = None
    series_index: Optional[float] = None
    language: Optional[str] = None
    comments: Optional[str] = None
    rating: Optional[float] = None
    identifier_isbn: Optional[str] = None
    identifier_amazon: Optional[str] = None
    identifier_goodreads: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class CalibreMetadataExtractor:
    """Extract metadata using Calibre's ebook-meta tool."""

    def __init__(self, calibre_path: Optional[Path] = None):
        """Initialize Calibre metadata extractor.

        Args:
            calibre_path: Path to ebook-meta binary
        """
        config = get_config()
        self.calibre_path = calibre_path or config.paths.calibre_path

        # Check if calibre is available
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if Calibre is available.

        Returns:
            True if ebook-meta is available
        """
        try:
            result = subprocess.run(
                [str(self.calibre_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Calibre not available: {e}")
            return False

    def extract(self, file_path: Path) -> Optional[CalibreMetadata]:
        """Extract metadata from ebook.

        Args:
            file_path: Path to ebook file

        Returns:
            CalibreMetadata object or None if extraction failed
        """
        if not self.available:
            logger.warning("Calibre not available, skipping metadata extraction")
            return None

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        try:
            # Run ebook-meta
            result = subprocess.run(
                [str(self.calibre_path), str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                logger.error(f"ebook-meta failed: {result.stderr}")
                return None

            # Parse output
            metadata = self._parse_output(result.stdout)
            logger.info(f"Extracted Calibre metadata for: {file_path.name}")

            return metadata

        except subprocess.TimeoutExpired:
            logger.error(f"Calibre metadata extraction timed out for: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error extracting Calibre metadata: {e}")
            return None

    def _parse_output(self, output: str) -> CalibreMetadata:
        """Parse ebook-meta output.

        Args:
            output: Raw output from ebook-meta

        Returns:
            CalibreMetadata object
        """
        metadata = CalibreMetadata()

        lines = output.split("\n")
        for line in lines:
            line = line.strip()
            if not line or ":" not in line:
                continue

            key, _, value = line.partition(":")
            key = key.strip().lower()
            value = value.strip()

            if not value:
                continue

            # Map Calibre fields to our metadata
            if key == "title":
                metadata.title = value
            elif key == "author(s)":
                # Authors can be comma or ampersand separated
                authors = [a.strip() for a in value.replace("&", ",").split(",")]
                metadata.authors = authors
            elif key == "author sort":
                metadata.author_sort = value
            elif key == "publisher":
                metadata.publisher = value
            elif key == "published":
                metadata.publication_date = value
            elif key == "tags":
                tags = [t.strip() for t in value.split(",")]
                metadata.tags = tags
            elif key == "series":
                metadata.series = value
            elif key == "series index":
                try:
                    metadata.series_index = float(value)
                except ValueError:
                    pass
            elif key == "languages":
                # Take first language
                langs = [l.strip() for l in value.split(",")]
                if langs:
                    metadata.language = langs[0]
            elif key == "comments":
                metadata.comments = value
            elif key == "rating":
                try:
                    metadata.rating = float(value)
                except ValueError:
                    pass
            elif key.startswith("identifier"):
                # Extract ISBN and other identifiers
                identifier_type = key.replace("identifier:", "").strip()
                if "isbn" in identifier_type.lower():
                    metadata.isbn = value
                    metadata.identifier_isbn = value
                elif "amazon" in identifier_type.lower():
                    metadata.identifier_amazon = value
                elif "goodreads" in identifier_type.lower():
                    metadata.identifier_goodreads = value

        return metadata

    def extract_with_fallback(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata with fallback to empty dict.

        Args:
            file_path: Path to ebook file

        Returns:
            Dictionary of metadata
        """
        metadata = self.extract(file_path)
        if metadata:
            return metadata.to_dict()
        return {}
