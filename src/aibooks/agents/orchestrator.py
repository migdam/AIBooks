"""Agent orchestrator - coordinates all agents using LangGraph."""

from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger
from sqlalchemy.orm import Session

from .format_strategist import FormatStrategistAgent
from .metadata_intelligence import MetadataIntelligenceAgent
from .text_quality import TextQualityAgent
from .cost_optimizer import CostOptimizerAgent
from .failure_recovery import FailureRecoveryAgent
from .pipeline_evolution import PipelineEvolutionAgent


class AgentOrchestrator:
    """Coordinates all agents in the document processing pipeline."""

    def __init__(self, session: Session):
        """Initialize agent orchestrator.

        Args:
            session: Database session
        """
        self.session = session

        # Initialize all agents
        self.format_strategist = FormatStrategistAgent(session)
        self.metadata_intelligence = MetadataIntelligenceAgent(session)
        self.text_quality = TextQualityAgent(session)
        self.cost_optimizer = CostOptimizerAgent(session)
        self.failure_recovery = FailureRecoveryAgent(session)
        self.pipeline_evolution = PipelineEvolutionAgent(session)

        logger.info("Agent Orchestrator initialized with 6 agents")

    def get_parsing_strategy(
        self, file_path: Path, format_type: str, file_size: int
    ) -> Dict[str, Any]:
        """Get optimal parsing strategy from Format Strategist.

        Args:
            file_path: Path to document
            format_type: Document format
            file_size: File size in bytes

        Returns:
            Parsing strategy dictionary
        """
        context = {
            "file_path": file_path,
            "format": format_type,
            "file_size": file_size,
        }

        decision = self.format_strategist.decide(context)
        return decision.decision

    def refine_metadata(
        self,
        calibre_metadata: Dict[str, Any],
        docling_metadata: Dict[str, Any],
        filename_metadata: Dict[str, Any],
        fused_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Refine metadata using Metadata Intelligence agent.

        Args:
            calibre_metadata: Metadata from Calibre
            docling_metadata: Metadata from Docling
            filename_metadata: Metadata from filename
            fused_metadata: Already fused metadata

        Returns:
            Refined metadata with quality assessment
        """
        context = {
            "calibre_metadata": calibre_metadata,
            "docling_metadata": docling_metadata,
            "filename_metadata": filename_metadata,
            "fused_metadata": fused_metadata,
        }

        decision = self.metadata_intelligence.decide(context)
        return decision.decision

    def assess_text_quality(
        self, text: str, format_type: str, parsing_method: str
    ) -> Dict[str, Any]:
        """Assess text quality and get cleaning strategy.

        Args:
            text: Extracted text
            format_type: Document format
            parsing_method: Method used for parsing

        Returns:
            Quality assessment and cleaning strategy
        """
        context = {
            "text": text,
            "format": format_type,
            "parsing_method": parsing_method,
        }

        decision = self.text_quality.decide(context)
        return decision.decision

    def optimize_llm_usage(
        self, step: str, estimated_tokens: int, daily_budget: float
    ) -> Dict[str, Any]:
        """Get cost-optimized LLM usage strategy.

        Args:
            step: Processing step
            estimated_tokens: Estimated token count
            daily_budget: Daily budget in USD

        Returns:
            Cost optimization decision
        """
        context = {
            "step": step,
            "estimated_tokens": estimated_tokens,
            "daily_budget": daily_budget,
        }

        decision = self.cost_optimizer.decide(context)
        return decision.decision

    def handle_failure(
        self,
        error: str,
        error_type: str,
        file_path: Path,
        format_type: str,
        previous_attempts: list,
        original_strategy: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle parsing failure and get recovery strategy.

        Args:
            error: Error message
            error_type: Type of error
            file_path: Path to document
            format_type: Document format
            previous_attempts: Previous recovery attempts
            original_strategy: Original parsing strategy

        Returns:
            Recovery strategy
        """
        context = {
            "error": error,
            "error_type": error_type,
            "file_path": file_path,
            "format": format_type,
            "previous_attempts": previous_attempts,
            "original_strategy": original_strategy,
        }

        decision = self.failure_recovery.decide(context)
        return decision.decision

    def analyze_pipeline_performance(
        self, analysis_period_days: int = 7, min_documents: int = 10
    ) -> Dict[str, Any]:
        """Analyze pipeline performance and get improvement suggestions.

        Args:
            analysis_period_days: Number of days to analyze
            min_documents: Minimum documents for reliable analysis

        Returns:
            Performance analysis and suggestions
        """
        context = {
            "analysis_period_days": analysis_period_days,
            "min_documents": min_documents,
        }

        decision = self.pipeline_evolution.decide(context)
        return decision.decision

    def report_parsing_success(
        self,
        format_type: str,
        strategy: Dict[str, Any],
        success: bool,
        quality_score: float,
    ):
        """Report parsing outcome to Format Strategist for learning.

        Args:
            format_type: Document format
            strategy: Strategy used
            success: Whether parsing succeeded
            quality_score: Quality of output (0-1)
        """
        self.format_strategist.report_success(format_type, strategy, success)

    def report_metadata_quality(
        self, field: str, predicted_value: Any, actual_value: Any, match: bool
    ):
        """Report metadata prediction accuracy.

        Args:
            field: Metadata field
            predicted_value: Predicted value
            actual_value: Actual value
            match: Whether values match
        """
        self.metadata_intelligence.report_metadata_accuracy(
            field, predicted_value, actual_value, match
        )

    def report_cleaning_quality(self, strategy: Dict[str, Any], success: bool):
        """Report text cleaning outcome.

        Args:
            strategy: Cleaning strategy used
            success: Whether cleaning improved quality
        """
        self.text_quality.report_cleaning_success(strategy, success)

    def report_llm_performance(
        self, step: str, model: str, cost: float, quality_score: float, success: bool
    ):
        """Report LLM performance for cost optimization.

        Args:
            step: Processing step
            model: Model used
            cost: Actual cost
            quality_score: Quality of output (0-1)
            success: Whether task succeeded
        """
        self.cost_optimizer.report_model_performance(
            step, model, cost, quality_score, success
        )

    def report_recovery_outcome(
        self, error_type: str, strategy: Dict[str, Any], success: bool
    ):
        """Report failure recovery outcome.

        Args:
            error_type: Type of error
            strategy: Recovery strategy used
            success: Whether recovery succeeded
        """
        self.failure_recovery.report_recovery_outcome(error_type, strategy, success)
