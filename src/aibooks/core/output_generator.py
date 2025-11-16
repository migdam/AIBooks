"""Output file generators for different formats."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from ..core.config import get_config


class OutputGenerator:
    """Generate output files in various formats."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize output generator.

        Args:
            output_dir: Output directory (defaults to config value)
        """
        config = get_config()
        self.output_dir = output_dir or config.paths.output_dir

        # Ensure output directories exist
        (self.output_dir / "txt").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "md").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "json").mkdir(parents=True, exist_ok=True)

    def generate_txt(
        self, document_id: int, title: str, text: str, metadata: Optional[Dict] = None
    ) -> Path:
        """Generate plain text output.

        Args:
            document_id: Document ID
            title: Document title
            text: Document text
            metadata: Optional metadata to include as header

        Returns:
            Path to generated file
        """
        filename = self._sanitize_filename(f"{document_id}_{title}.txt")
        output_path = self.output_dir / "txt" / filename

        content = []

        # Add metadata header
        if metadata:
            content.append("=" * 80)
            content.append(f"Title: {metadata.get('title', 'Unknown')}")
            if metadata.get("authors"):
                content.append(f"Author(s): {', '.join(metadata['authors'])}")
            if metadata.get("publication_date"):
                content.append(f"Published: {metadata['publication_date']}")
            if metadata.get("isbn"):
                content.append(f"ISBN: {metadata['isbn']}")
            content.append("=" * 80)
            content.append("")

        content.append(text)

        output_path.write_text("\n".join(content), encoding="utf-8")

        logger.info(f"Generated TXT output: {output_path}")
        return output_path

    def generate_markdown(
        self,
        document_id: int,
        title: str,
        markdown: str,
        metadata: Optional[Dict] = None,
        chapters: Optional[list] = None,
    ) -> Path:
        """Generate Markdown output with structure.

        Args:
            document_id: Document ID
            title: Document title
            markdown: Markdown content
            metadata: Optional metadata
            chapters: Optional chapter information

        Returns:
            Path to generated file
        """
        filename = self._sanitize_filename(f"{document_id}_{title}.md")
        output_path = self.output_dir / "md" / filename

        content = []

        # Metadata as YAML front matter
        if metadata:
            content.append("---")
            content.append(f"title: \"{metadata.get('title', 'Unknown')}\"")
            if metadata.get("authors"):
                content.append(f"authors: {metadata['authors']}")
            if metadata.get("publication_date"):
                content.append(f"date: {metadata['publication_date']}")
            if metadata.get("isbn"):
                content.append(f"isbn: {metadata['isbn']}")
            if metadata.get("tags"):
                content.append(f"tags: {metadata['tags']}")
            content.append("---")
            content.append("")

        # Table of contents if chapters available
        if chapters:
            content.append("## Table of Contents")
            content.append("")
            for idx, chapter in enumerate(chapters, 1):
                content.append(f"{idx}. [{chapter['title']}](#chapter-{idx})")
            content.append("")

        # Main content
        content.append(markdown)

        output_path.write_text("\n".join(content), encoding="utf-8")

        logger.info(f"Generated Markdown output: {output_path}")
        return output_path

    def generate_json(
        self,
        document_id: int,
        title: str,
        text: str,
        metadata: Dict[str, Any],
        chapters: Optional[list] = None,
        tables: Optional[list] = None,
        figures: Optional[list] = None,
        docling_output: Optional[Dict] = None,
    ) -> Path:
        """Generate structured JSON output.

        Args:
            document_id: Document ID
            title: Document title
            text: Document text
            metadata: Document metadata
            chapters: Chapter structure
            tables: Extracted tables
            figures: Extracted figures
            docling_output: Raw Docling output

        Returns:
            Path to generated file
        """
        filename = self._sanitize_filename(f"{document_id}_{title}.json")
        output_path = self.output_dir / "json" / filename

        output_data = {
            "document_id": document_id,
            "metadata": metadata,
            "text": text,
            "word_count": len(text.split()),
            "chapters": chapters or [],
            "tables": tables or [],
            "figures": figures or [],
        }

        # Optionally include raw Docling output
        if docling_output:
            output_data["docling_raw"] = docling_output

        output_path.write_text(
            json.dumps(output_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info(f"Generated JSON output: {output_path}")
        return output_path

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to remove invalid characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")

        # Limit length
        if len(filename) > 200:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            filename = f"{name[:195]}.{ext}"

        return filename
