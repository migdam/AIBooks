"""Format Strategist Agent - determines optimal parsing strategy."""

import json
from pathlib import Path
from typing import Dict, Any
from loguru import logger

from .base_agent import BaseAgent, AgentDecision
from ..parsers.format_detector import DocumentFormat


class FormatStrategistAgent(BaseAgent):
    """Agent 1: Format Strategist - decides optimal parsing strategy."""

    def __init__(self, session):
        """Initialize Format Strategist Agent."""
        super().__init__("format_strategist", session)

    def decide(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide optimal parsing strategy.

        Args:
            context: {
                "file_path": Path,
                "format": DocumentFormat,
                "file_size": int,
                "sample_content": Optional[str]
            }

        Returns:
            AgentDecision with parsing strategy
        """
        file_path = context.get("file_path")
        format_type = context.get("format")
        file_size = context.get("file_size", 0)

        logger.info(f"Format Strategist analyzing: {file_path} ({format_type})")

        # Check for learned patterns
        pattern_key = f"format_strategy_{format_type}"
        learned = self.recall(pattern_key)

        if learned:
            logger.debug(f"Using learned strategy for {format_type}")
            strategy = json.loads(learned.pattern_value)
            confidence = learned.confidence_score
        else:
            # Default strategy based on format
            strategy = self._determine_default_strategy(format_type, file_size)
            confidence = 0.6

        decision = AgentDecision(
            agent_name=self.name,
            decision_type="parsing_strategy",
            decision=strategy,
            confidence=confidence,
            reasoning=self._explain_strategy(strategy, format_type),
        )

        logger.info(f"Strategy: {strategy['primary_method']} (confidence={confidence:.2f})")

        return decision

    def _determine_default_strategy(
        self, format_type: DocumentFormat, file_size: int
    ) -> Dict[str, Any]:
        """Determine default parsing strategy.

        Args:
            format_type: Document format
            file_size: File size in bytes

        Returns:
            Strategy dictionary
        """
        strategy = {
            "primary_method": "docling",
            "enable_ocr": False,
            "enable_vision": True,
            "fallback_methods": [],
            "parallel_extraction": True,
        }

        # PDF strategy
        if format_type == DocumentFormat.PDF:
            strategy["enable_ocr"] = True
            strategy["fallback_methods"] = ["pymupdf", "pypdf"]

            # Large files might need chunking
            if file_size > 50 * 1024 * 1024:  # 50 MB
                strategy["chunk_pages"] = 100
                strategy["parallel_extraction"] = True

        # EPUB strategy
        elif format_type == DocumentFormat.EPUB:
            strategy["primary_method"] = "docling"
            strategy["enable_ocr"] = False
            strategy["fallback_methods"] = ["ebooklib"]

        # MOBI/AZW3 strategy
        elif format_type in {DocumentFormat.MOBI, DocumentFormat.AZW3}:
            strategy["primary_method"] = "calibre_convert"
            strategy["fallback_methods"] = ["docling"]

        # DOCX strategy
        elif format_type == DocumentFormat.DOCX:
            strategy["primary_method"] = "docling"
            strategy["fallback_methods"] = ["python-docx"]

        # Image strategy
        elif format_type == DocumentFormat.IMAGE:
            strategy["primary_method"] = "ocr"
            strategy["enable_ocr"] = True
            strategy["enable_vision"] = True

        # TXT/MD strategy
        elif format_type in {DocumentFormat.TXT, DocumentFormat.MD}:
            strategy["primary_method"] = "direct_read"
            strategy["enable_ocr"] = False

        return strategy

    def _explain_strategy(self, strategy: Dict[str, Any], format_type: DocumentFormat) -> str:
        """Generate reasoning for strategy.

        Args:
            strategy: Strategy dictionary
            format_type: Document format

        Returns:
            Explanation string
        """
        method = strategy["primary_method"]
        ocr = strategy.get("enable_ocr", False)

        reasons = [
            f"Using {method} as primary parser for {format_type}",
        ]

        if ocr:
            reasons.append("OCR enabled due to potential scanned content")

        if strategy.get("fallback_methods"):
            fallbacks = ", ".join(strategy["fallback_methods"])
            reasons.append(f"Fallback methods: {fallbacks}")

        return ". ".join(reasons)

    def report_success(
        self, format_type: DocumentFormat, strategy: Dict[str, Any], success: bool
    ):
        """Report success/failure of strategy.

        Args:
            format_type: Document format
            strategy: Strategy used
            success: Whether parsing succeeded
        """
        pattern_key = f"format_strategy_{format_type}"
        pattern_value = json.dumps(strategy)

        self.learn(
            pattern_key=pattern_key,
            pattern_value=pattern_value,
            learning_type="strategy",
            success=success,
            context={"format": str(format_type)},
        )
