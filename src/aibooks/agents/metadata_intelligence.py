"""Metadata Intelligence Agent - fuses and refines metadata."""

import json
from typing import Dict, Any, Optional
from loguru import logger

from .base_agent import BaseAgent, AgentDecision


class MetadataIntelligenceAgent(BaseAgent):
    """Agent 2: Metadata Intelligence - fuses and improves metadata."""

    def __init__(self, session):
        """Initialize Metadata Intelligence Agent."""
        super().__init__("metadata_intelligence", session)

    def decide(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide on best metadata from multiple sources.

        Args:
            context: {
                "calibre_metadata": Dict,
                "docling_metadata": Dict,
                "filename_metadata": Dict,
                "llm_metadata": Optional[Dict],
                "fused_metadata": Dict
            }

        Returns:
            AgentDecision with refined metadata
        """
        fused = context.get("fused_metadata", {})

        logger.info("Metadata Intelligence analyzing metadata quality")

        # Assess metadata quality
        quality_score = self._assess_metadata_quality(fused)

        # Determine if LLM enhancement is needed
        needs_llm = quality_score < 0.7

        # Check for learned patterns for this type of metadata
        improvements = self._apply_learned_patterns(fused)

        decision = AgentDecision(
            agent_name=self.name,
            decision_type="metadata_refinement",
            decision={
                "refined_metadata": improvements,
                "quality_score": quality_score,
                "needs_llm_enhancement": needs_llm,
                "missing_fields": self._identify_missing_fields(fused),
            },
            confidence=quality_score,
            reasoning=self._explain_assessment(fused, quality_score),
        )

        logger.info(
            f"Metadata quality: {quality_score:.2f}, "
            f"LLM enhancement: {'needed' if needs_llm else 'not needed'}"
        )

        return decision

    def _assess_metadata_quality(self, metadata: Dict[str, Any]) -> float:
        """Assess quality of metadata.

        Args:
            metadata: Metadata dictionary

        Returns:
            Quality score (0.0 to 1.0)
        """
        # Key fields and their weights
        field_weights = {
            "title": 0.3,
            "authors": 0.2,
            "isbn": 0.15,
            "publisher": 0.1,
            "publication_date": 0.1,
            "language": 0.05,
            "series": 0.05,
            "tags": 0.05,
        }

        score = 0.0

        for field, weight in field_weights.items():
            value = metadata.get(field)

            if value:
                # Field exists
                field_score = weight

                # Bonus for high-quality values
                if field == "title" and len(str(value)) > 3:
                    field_score = weight
                elif field == "authors" and isinstance(value, list) and len(value) > 0:
                    field_score = weight
                elif field == "isbn" and len(str(value)) in {10, 13}:
                    field_score = weight
                else:
                    field_score = weight * 0.8  # Partial credit

                score += field_score

        return min(score / sum(field_weights.values()), 1.0)

    def _identify_missing_fields(self, metadata: Dict[str, Any]) -> list[str]:
        """Identify missing critical fields.

        Args:
            metadata: Metadata dictionary

        Returns:
            List of missing field names
        """
        critical_fields = ["title", "authors", "publication_date", "language"]
        missing = []

        for field in critical_fields:
            if not metadata.get(field):
                missing.append(field)

        return missing

    def _apply_learned_patterns(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Apply learned patterns to improve metadata.

        Args:
            metadata: Current metadata

        Returns:
            Improved metadata
        """
        improved = metadata.copy()

        # Get all learned patterns
        patterns = self.get_all_patterns(min_confidence=0.6)

        for pattern in patterns:
            # Apply pattern based on type
            if pattern.learning_type == "correction":
                # Apply known corrections
                try:
                    correction = json.loads(pattern.pattern_value)
                    if correction.get("field") in improved:
                        # Apply correction logic
                        pass
                except Exception as e:
                    logger.warning(f"Error applying pattern: {e}")

        return improved

    def _explain_assessment(self, metadata: Dict[str, Any], quality_score: float) -> str:
        """Explain metadata assessment.

        Args:
            metadata: Metadata dictionary
            quality_score: Quality score

        Returns:
            Explanation string
        """
        reasons = []

        if quality_score >= 0.8:
            reasons.append("High quality metadata with all critical fields")
        elif quality_score >= 0.6:
            reasons.append("Moderate quality metadata with some missing fields")
        else:
            reasons.append("Low quality metadata requiring enhancement")

        missing = self._identify_missing_fields(metadata)
        if missing:
            reasons.append(f"Missing fields: {', '.join(missing)}")

        if metadata.get("isbn"):
            reasons.append("ISBN available for verification")

        return ". ".join(reasons)

    def report_metadata_accuracy(
        self, field: str, predicted_value: Any, actual_value: Any, match: bool
    ):
        """Report accuracy of metadata prediction.

        Args:
            field: Metadata field name
            predicted_value: Predicted value
            actual_value: Actual/verified value
            match: Whether values match
        """
        pattern_key = f"metadata_accuracy_{field}"
        pattern_value = json.dumps(
            {"predicted": str(predicted_value), "actual": str(actual_value)}
        )

        self.learn(
            pattern_key=pattern_key,
            pattern_value=pattern_value,
            learning_type="accuracy",
            success=match,
            context={"field": field},
        )
