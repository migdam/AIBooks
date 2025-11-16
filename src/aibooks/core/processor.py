"""Main document processor - orchestrates the entire pipeline."""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from ..db.models import Document
from ..db.database import get_db
from ..parsers.format_detector import FormatDetector
from ..parsers.docling_parser import DoclingParser
from ..parsers.calibre_metadata import CalibreMetadataExtractor
from ..parsers.metadata_fusion import MetadataFusion
from ..agents.orchestrator import AgentOrchestrator
from ..utils.hash_utils import calculate_file_hash
from ..utils.text_cleaner import TextCleaner
from ..core.output_generator import OutputGenerator
from ..core.cost_tracker import CostTracker
from ..core.config import get_config


class DocumentProcessor:
    """Main document processing pipeline."""

    def __init__(self, session: Optional[Session] = None):
        """Initialize document processor.

        Args:
            session: Database session (creates new if None)
        """
        self.config = get_config()
        self.db = get_db()
        self.session = session or self.db.get_session()

        # Initialize components
        self.format_detector = FormatDetector()
        self.docling_parser = DoclingParser(
            enable_ocr=self.config.processing.enable_ocr,
            enable_vision=self.config.processing.enable_docling_vision,
        )
        self.calibre_extractor = CalibreMetadataExtractor()
        self.metadata_fusion = MetadataFusion()
        self.text_cleaner = TextCleaner()
        self.output_generator = OutputGenerator()
        self.cost_tracker = CostTracker(self.session)

        # Initialize agent orchestrator
        self.agents = AgentOrchestrator(self.session)

        logger.info("Document Processor initialized")

    def process_document(
        self, file_path: Path, skip_if_duplicate: bool = True
    ) -> Optional[Document]:
        """Process a single document through the complete pipeline.

        Args:
            file_path: Path to document file
            skip_if_duplicate: Skip processing if document already exists

        Returns:
            Document object or None if failed/skipped
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        logger.info(f"Processing document: {file_path.name}")

        try:
            # Step 1: Check for duplicates
            content_hash = calculate_file_hash(file_path)

            if skip_if_duplicate:
                existing = self.session.query(Document).filter_by(content_hash=content_hash).first()
                if existing:
                    logger.info(f"Duplicate found (ID: {existing.id}), skipping")
                    return existing

            # Step 2: Detect format
            format_type = self.format_detector.detect(file_path)
            file_size = file_path.stat().st_size

            logger.info(f"Detected format: {format_type} ({file_size} bytes)")

            # Step 3: Get parsing strategy from Format Strategist Agent
            strategy = self.agents.get_parsing_strategy(
                file_path, str(format_type), file_size
            )

            logger.info(f"Parsing strategy: {strategy['primary_method']}")

            # Step 4: Parse document with Docling
            parsed_doc = self.docling_parser.parse(file_path)

            if not parsed_doc.success:
                logger.error(f"Parsing failed: {parsed_doc.error}")
                # TODO: Trigger failure recovery agent
                return None

            # Step 5: Extract metadata from multiple sources
            calibre_metadata = {}
            if self.format_detector.supports_calibre_metadata(format_type):
                calibre_metadata = self.calibre_extractor.extract_with_fallback(file_path)

            docling_metadata = parsed_doc.metadata
            filename_metadata = self.metadata_fusion.extract_from_filename(file_path)

            # Step 6: Fuse metadata
            fused = self.metadata_fusion.fuse(
                calibre_metadata=calibre_metadata,
                docling_metadata=docling_metadata,
                filename_metadata=filename_metadata,
            )

            # Step 7: Refine metadata with Metadata Intelligence Agent
            metadata_decision = self.agents.refine_metadata(
                calibre_metadata,
                docling_metadata,
                filename_metadata,
                fused.__dict__,
            )

            refined_metadata = metadata_decision["refined_metadata"]

            # Step 8: Assess text quality with Text Quality Agent
            quality_decision = self.agents.assess_text_quality(
                parsed_doc.text, str(format_type), strategy["primary_method"]
            )

            # Step 9: Clean text based on quality assessment
            cleaning_strategy = quality_decision["cleaning_strategy"]
            cleaned_text = self.text_cleaner.clean(
                parsed_doc.text,
                **cleaning_strategy,
            )

            # Step 10: Create document record
            document = Document(
                title=refined_metadata.get("title") or fused.title or file_path.stem,
                author=", ".join(refined_metadata.get("authors") or fused.authors or []),
                isbn=refined_metadata.get("isbn") or fused.isbn,
                publisher=refined_metadata.get("publisher") or fused.publisher,
                publication_date=refined_metadata.get("publication_date") or fused.publication_date,
                series=refined_metadata.get("series") or fused.series,
                series_index=refined_metadata.get("series_index") or fused.series_index,
                tags=json.dumps(refined_metadata.get("tags") or fused.tags or []),
                language=refined_metadata.get("language") or fused.language,
                format=str(format_type),
                source_file=str(file_path),
                content_hash=content_hash,
                chapters_json=json.dumps(parsed_doc.chapters),
                tables_json=json.dumps(parsed_doc.tables),
                metadata_json=json.dumps(refined_metadata),
                docling_json=json.dumps(parsed_doc.metadata),
                words=parsed_doc.words,
                pages=parsed_doc.pages,
            )

            self.session.add(document)
            self.session.flush()  # Get document ID

            # Step 11: Generate output files
            txt_path = self.output_generator.generate_txt(
                document.id,
                document.title,
                cleaned_text,
                refined_metadata,
            )

            md_path = self.output_generator.generate_markdown(
                document.id,
                document.title,
                parsed_doc.markdown,
                refined_metadata,
                parsed_doc.chapters,
            )

            json_path = self.output_generator.generate_json(
                document.id,
                document.title,
                cleaned_text,
                refined_metadata,
                parsed_doc.chapters,
                parsed_doc.tables,
                parsed_doc.figures,
                parsed_doc.metadata,
            )

            document.processed_text_path = str(txt_path)

            # Commit transaction
            self.session.commit()

            logger.info(
                f"Successfully processed document (ID: {document.id}): {document.title}"
            )

            # Report success to agents
            self.agents.report_parsing_success(
                str(format_type),
                strategy,
                success=True,
                quality_score=quality_decision["quality_score"],
            )

            self.agents.report_cleaning_quality(cleaning_strategy, success=True)

            return document

        except Exception as e:
            logger.error(f"Error processing document: {e}", exc_info=True)
            self.session.rollback()
            return None

    def process_batch(
        self, file_paths: list[Path], skip_duplicates: bool = True
    ) -> list[Optional[Document]]:
        """Process multiple documents.

        Args:
            file_paths: List of file paths
            skip_duplicates: Skip duplicate documents

        Returns:
            List of Document objects (None for failed/skipped)
        """
        results = []

        for idx, file_path in enumerate(file_paths, 1):
            logger.info(f"Processing {idx}/{len(file_paths)}: {file_path.name}")

            doc = self.process_document(file_path, skip_if_duplicate=skip_duplicates)
            results.append(doc)

        successful = sum(1 for r in results if r is not None)
        logger.info(f"Batch complete: {successful}/{len(file_paths)} successful")

        return results

    def get_daily_cost_summary(self) -> Dict[str, Any]:
        """Get daily cost summary.

        Returns:
            Cost summary dictionary
        """
        return {
            "daily_spend": self.cost_tracker.get_daily_cost(),
            "cost_by_step": self.cost_tracker.get_cost_by_step(days=1),
        }

    def analyze_pipeline_performance(self, days: int = 7) -> Dict[str, Any]:
        """Analyze pipeline performance.

        Args:
            days: Number of days to analyze

        Returns:
            Performance analysis
        """
        return self.agents.analyze_pipeline_performance(
            analysis_period_days=days,
            min_documents=10,
        )
