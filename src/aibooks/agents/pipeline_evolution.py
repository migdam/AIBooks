"""Pipeline Evolution Agent - analyzes logs and improves pipeline over time."""

import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy import func

from .base_agent import BaseAgent, AgentDecision
from ..db.models import GenAIUsageLog, Document


class PipelineEvolutionAgent(BaseAgent):
    """Agent 6: Pipeline Evolution - analyzes performance and suggests improvements."""

    def __init__(self, session):
        """Initialize Pipeline Evolution Agent."""
        super().__init__("pipeline_evolution", session)

    def decide(self, context: Dict[str, Any]) -> AgentDecision:
        """Analyze pipeline performance and suggest improvements.

        Args:
            context: {
                "analysis_period_days": int,
                "min_documents": int
            }

        Returns:
            AgentDecision with improvement suggestions
        """
        days = context.get("analysis_period_days", 7)
        min_docs = context.get("min_documents", 10)

        logger.info(f"Pipeline Evolution analyzing last {days} days")

        # Analyze performance
        analysis = self._analyze_performance(days)

        # Generate improvement suggestions
        suggestions = self._generate_suggestions(analysis, min_docs)

        # Determine if auto-apply is recommended
        auto_apply = self._should_auto_apply(suggestions)

        decision = AgentDecision(
            agent_name=self.name,
            decision_type="pipeline_evolution",
            decision={
                "analysis": analysis,
                "suggestions": suggestions,
                "auto_apply_safe": auto_apply,
                "requires_review": not auto_apply,
            },
            confidence=0.7,
            reasoning=self._explain_evolution(analysis, suggestions),
        )

        logger.info(f"Generated {len(suggestions)} improvement suggestions")

        return decision

    def _analyze_performance(self, days: int) -> Dict[str, Any]:
        """Analyze pipeline performance.

        Args:
            days: Number of days to analyze

        Returns:
            Performance analysis dictionary
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Document statistics
        total_docs = (
            self.session.query(Document)
            .filter(Document.created_at >= start_date)
            .count()
        )

        # Success rate (documents with processed text)
        successful_docs = (
            self.session.query(Document)
            .filter(
                Document.created_at >= start_date,
                Document.processed_text_path.isnot(None),
            )
            .count()
        )

        success_rate = successful_docs / total_docs if total_docs > 0 else 0

        # Cost analysis
        total_cost = (
            self.session.query(func.sum(GenAIUsageLog.cost))
            .filter(GenAIUsageLog.timestamp >= start_date)
            .scalar()
            or 0.0
        )

        avg_cost_per_doc = total_cost / total_docs if total_docs > 0 else 0

        # Token usage
        total_tokens = (
            self.session.query(
                func.sum(GenAIUsageLog.tokens_in + GenAIUsageLog.tokens_out)
            )
            .filter(GenAIUsageLog.timestamp >= start_date)
            .scalar()
            or 0
        )

        # Format distribution
        format_dist = self._get_format_distribution(start_date)

        # Step-wise cost analysis
        step_costs = self._get_step_costs(start_date)

        return {
            "total_documents": total_docs,
            "successful_documents": successful_docs,
            "success_rate": success_rate,
            "total_cost": total_cost,
            "avg_cost_per_document": avg_cost_per_doc,
            "total_tokens": total_tokens,
            "format_distribution": format_dist,
            "step_costs": step_costs,
        }

    def _get_format_distribution(self, start_date: datetime) -> Dict[str, int]:
        """Get distribution of document formats.

        Args:
            start_date: Start date for analysis

        Returns:
            Dictionary mapping format to count
        """
        results = (
            self.session.query(Document.format, func.count(Document.id))
            .filter(Document.created_at >= start_date)
            .group_by(Document.format)
            .all()
        )

        return {format_type: count for format_type, count in results}

    def _get_step_costs(self, start_date: datetime) -> Dict[str, float]:
        """Get costs by processing step.

        Args:
            start_date: Start date for analysis

        Returns:
            Dictionary mapping step to total cost
        """
        results = (
            self.session.query(GenAIUsageLog.step, func.sum(GenAIUsageLog.cost))
            .filter(GenAIUsageLog.timestamp >= start_date)
            .group_by(GenAIUsageLog.step)
            .all()
        )

        return {step: float(cost) for step, cost in results if cost}

    def _generate_suggestions(
        self, analysis: Dict[str, Any], min_docs: int
    ) -> List[Dict[str, Any]]:
        """Generate improvement suggestions.

        Args:
            analysis: Performance analysis
            min_docs: Minimum documents for reliable suggestions

        Returns:
            List of suggestion dictionaries
        """
        suggestions = []

        # Not enough data
        if analysis["total_documents"] < min_docs:
            return [{
                "type": "insufficient_data",
                "priority": "info",
                "suggestion": f"Need at least {min_docs} documents for reliable analysis",
            }]

        # Low success rate
        if analysis["success_rate"] < 0.8:
            suggestions.append({
                "type": "success_rate",
                "priority": "high",
                "suggestion": f"Success rate is low ({analysis['success_rate']:.1%}). "
                            "Consider adjusting failure recovery strategies.",
                "action": "review_failure_patterns",
            })

        # High costs
        if analysis["avg_cost_per_document"] > 0.50:
            suggestions.append({
                "type": "cost_optimization",
                "priority": "medium",
                "suggestion": f"Average cost per document is ${analysis['avg_cost_per_document']:.2f}. "
                            "Consider using cheaper models for routine tasks.",
                "action": "optimize_model_selection",
            })

        # Expensive steps
        step_costs = analysis["step_costs"]
        if step_costs:
            max_cost_step = max(step_costs.items(), key=lambda x: x[1])
            if max_cost_step[1] > analysis["total_cost"] * 0.5:
                suggestions.append({
                    "type": "expensive_step",
                    "priority": "medium",
                    "suggestion": f"Step '{max_cost_step[0]}' accounts for "
                                f"${max_cost_step[1]:.2f} of total cost. "
                                "Consider optimization.",
                    "action": f"optimize_step_{max_cost_step[0]}",
                })

        # Format-specific optimizations
        format_dist = analysis["format_distribution"]
        if format_dist:
            dominant_format = max(format_dist.items(), key=lambda x: x[1])
            if dominant_format[1] > analysis["total_documents"] * 0.5:
                suggestions.append({
                    "type": "format_specialization",
                    "priority": "low",
                    "suggestion": f"Most documents are {dominant_format[0]} "
                                f"({dominant_format[1]} docs). "
                                "Consider format-specific optimizations.",
                    "action": f"optimize_for_{dominant_format[0]}",
                })

        return suggestions

    def _should_auto_apply(self, suggestions: List[Dict[str, Any]]) -> bool:
        """Determine if suggestions can be auto-applied.

        Args:
            suggestions: List of suggestions

        Returns:
            True if safe to auto-apply
        """
        # Don't auto-apply if there are high priority suggestions
        high_priority = [s for s in suggestions if s.get("priority") == "high"]
        if high_priority:
            return False

        # Only auto-apply low priority suggestions
        low_priority = [s for s in suggestions if s.get("priority") == "low"]
        return len(low_priority) > 0 and len(suggestions) == len(low_priority)

    def _explain_evolution(
        self, analysis: Dict[str, Any], suggestions: List[Dict[str, Any]]
    ) -> str:
        """Explain evolution analysis.

        Args:
            analysis: Performance analysis
            suggestions: Improvement suggestions

        Returns:
            Explanation string
        """
        reasons = []

        reasons.append(
            f"Analyzed {analysis['total_documents']} documents "
            f"with {analysis['success_rate']:.1%} success rate"
        )

        reasons.append(
            f"Total cost: ${analysis['total_cost']:.2f} "
            f"(${analysis['avg_cost_per_document']:.2f}/doc)"
        )

        if suggestions:
            high_priority = sum(1 for s in suggestions if s.get("priority") == "high")
            if high_priority > 0:
                reasons.append(f"{high_priority} high-priority improvements identified")

        return ". ".join(reasons)

    def apply_suggestions(self, suggestions: List[Dict[str, Any]]):
        """Apply improvement suggestions.

        Args:
            suggestions: List of suggestions to apply
        """
        for suggestion in suggestions:
            action = suggestion.get("action")

            if not action:
                continue

            logger.info(f"Applying suggestion: {action}")

            # Record as learned pattern
            self.learn(
                pattern_key=f"evolution_{action}",
                pattern_value=json.dumps(suggestion),
                learning_type="evolution",
                success=True,
                context={"priority": suggestion.get("priority")},
            )
