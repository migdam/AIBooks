"""Cost Optimizer Agent - minimizes LLM costs while maintaining quality."""

import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from .base_agent import BaseAgent, AgentDecision
from ..db.models import GenAIUsageLog


class CostOptimizerAgent(BaseAgent):
    """Agent 4: Cost Optimizer - minimizes LLM costs."""

    def __init__(self, session):
        """Initialize Cost Optimizer Agent."""
        super().__init__("cost_optimizer", session)

    def decide(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide on cost-optimal LLM usage strategy.

        Args:
            context: {
                "step": str,
                "estimated_tokens": int,
                "daily_budget": float,
                "quality_requirements": str
            }

        Returns:
            AgentDecision with cost optimization strategy
        """
        step = context.get("step")
        estimated_tokens = context.get("estimated_tokens", 1000)
        daily_budget = context.get("daily_budget", 10.0)

        logger.info(f"Cost Optimizer analyzing LLM usage for: {step}")

        # Get current daily spending
        current_spend = self._get_daily_spending()

        # Determine if we should use LLM at all
        use_llm = self._should_use_llm(step, current_spend, daily_budget)

        # Select optimal model
        model = self._select_optimal_model(step, estimated_tokens, current_spend, daily_budget)

        # Determine batching strategy
        batching_strategy = self._determine_batching_strategy(step)

        decision = AgentDecision(
            agent_name=self.name,
            decision_type="cost_optimization",
            decision={
                "use_llm": use_llm,
                "model": model,
                "batching_strategy": batching_strategy,
                "current_daily_spend": current_spend,
                "remaining_budget": daily_budget - current_spend,
                "estimated_cost": self._estimate_cost(model, estimated_tokens),
            },
            confidence=0.85,
            reasoning=self._explain_decision(use_llm, model, current_spend, daily_budget),
        )

        logger.info(
            f"Cost decision: use_llm={use_llm}, model={model}, "
            f"spend=${current_spend:.2f}/${daily_budget:.2f}"
        )

        return decision

    def _get_daily_spending(self) -> float:
        """Get total spending today.

        Returns:
            Total cost in USD
        """
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        logs = (
            self.session.query(GenAIUsageLog)
            .filter(GenAIUsageLog.timestamp >= today_start)
            .all()
        )

        total = sum(log.cost or 0.0 for log in logs)
        return total

    def _should_use_llm(self, step: str, current_spend: float, budget: float) -> bool:
        """Determine if LLM should be used for this step.

        Args:
            step: Processing step
            current_spend: Current daily spending
            budget: Daily budget

        Returns:
            True if LLM should be used
        """
        # Check budget
        if current_spend >= budget * 0.95:  # 95% of budget used
            logger.warning(f"Daily budget nearly exhausted: ${current_spend:.2f}/${budget:.2f}")
            return False

        # Check if step requires LLM
        critical_steps = {"metadata_enhancement", "ocr_correction", "quality_check"}

        if step in critical_steps:
            return True

        # Optional steps can be skipped if budget is tight
        if current_spend >= budget * 0.7:  # 70% of budget used
            logger.info(f"Budget tight, skipping optional LLM call for: {step}")
            return False

        return True

    def _select_optimal_model(
        self, step: str, estimated_tokens: int, current_spend: float, budget: float
    ) -> str:
        """Select optimal model for the task.

        Args:
            step: Processing step
            estimated_tokens: Estimated token count
            current_spend: Current daily spending
            budget: Daily budget

        Returns:
            Model name
        """
        # Check learned patterns
        pattern_key = f"model_selection_{step}"
        learned = self.recall(pattern_key)

        if learned and learned.confidence_score > 0.7:
            model = learned.pattern_value
            logger.debug(f"Using learned model for {step}: {model}")
            return model

        # Default model selection based on step
        remaining_budget_pct = (budget - current_spend) / budget if budget > 0 else 0

        # If budget is tight, use cheaper models
        if remaining_budget_pct < 0.3:
            return "gpt-4o-mini"  # Cheapest option

        # Task-specific model selection
        if step in {"metadata_enhancement", "metadata_refinement"}:
            return "gpt-4o-mini"  # Fast and cheap for metadata

        elif step in {"ocr_correction", "text_cleanup"}:
            return "gpt-4o-mini"  # Good for text processing

        elif step in {"quality_analysis", "chapter_detection"}:
            return "gpt-4o"  # Better reasoning for complex tasks

        else:
            return "gpt-4o-mini"  # Default to cheaper model

    def _determine_batching_strategy(self, step: str) -> Dict[str, Any]:
        """Determine optimal batching strategy.

        Args:
            step: Processing step

        Returns:
            Batching strategy
        """
        # Check learned patterns
        pattern_key = f"batching_{step}"
        learned = self.recall(pattern_key)

        if learned:
            try:
                return json.loads(learned.pattern_value)
            except Exception:
                pass

        # Default batching
        return {
            "enabled": True,
            "batch_size": 10,
            "combine_calls": True,
        }

    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Estimate cost for LLM call.

        Args:
            model: Model name
            tokens: Total tokens (input + output)

        Returns:
            Estimated cost in USD
        """
        # Simplified cost estimation (input:output ratio assumed 3:1)
        input_tokens = int(tokens * 0.75)
        output_tokens = int(tokens * 0.25)

        from ..core.cost_tracker import MODEL_PRICING

        pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])

        cost_in = (input_tokens / 1000.0) * pricing["input"]
        cost_out = (output_tokens / 1000.0) * pricing["output"]

        return cost_in + cost_out

    def _explain_decision(
        self, use_llm: bool, model: str, current_spend: float, budget: float
    ) -> str:
        """Explain cost optimization decision.

        Args:
            use_llm: Whether to use LLM
            model: Selected model
            current_spend: Current spending
            budget: Daily budget

        Returns:
            Explanation string
        """
        reasons = []

        remaining = budget - current_spend
        pct_used = (current_spend / budget * 100) if budget > 0 else 0

        reasons.append(f"Budget: ${current_spend:.2f}/${budget:.2f} ({pct_used:.0f}% used)")

        if use_llm:
            reasons.append(f"Selected {model} as optimal model")
        else:
            reasons.append("Skipping LLM to preserve budget")

        if remaining < 1.0:
            reasons.append("Low remaining budget, using cheapest options")

        return ". ".join(reasons)

    def report_model_performance(
        self, step: str, model: str, cost: float, quality_score: float, success: bool
    ):
        """Report model performance for learning.

        Args:
            step: Processing step
            model: Model used
            cost: Actual cost
            quality_score: Quality of output (0-1)
            success: Whether task succeeded
        """
        # Learn model selection
        pattern_key = f"model_selection_{step}"

        self.learn(
            pattern_key=pattern_key,
            pattern_value=model,
            learning_type="model_selection",
            success=success and quality_score > 0.7,
            context={
                "step": step,
                "cost": cost,
                "quality": quality_score,
            },
        )
