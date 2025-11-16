"""LLM cost tracking and calculation utilities."""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger
from sqlalchemy.orm import Session

from ..db.models import GenAIUsageLog


# Model pricing (USD per 1K tokens)
# Updated as of January 2025
MODEL_PRICING = {
    # OpenAI GPT-4
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},

    # OpenAI GPT-3.5
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},

    # Anthropic Claude
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},

    # Default fallback
    "default": {"input": 0.001, "output": 0.002},
}


@dataclass
class CostEstimate:
    """Cost estimate for an LLM call."""

    model: str
    tokens_in: int
    tokens_out: int
    cost_input: float
    cost_output: float
    total_cost: float
    duration_ms: int


class CostTracker:
    """Track and calculate LLM usage costs."""

    def __init__(self, session: Session):
        """Initialize cost tracker.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def calculate_cost(
        self,
        model: str,
        tokens_in: int,
        tokens_out: int,
    ) -> float:
        """Calculate cost for a given model and token usage.

        Args:
            model: Model name
            tokens_in: Input tokens
            tokens_out: Output tokens

        Returns:
            Total cost in USD
        """
        # Normalize model name
        model_key = model.lower()

        # Find matching pricing
        pricing = None
        for key, value in MODEL_PRICING.items():
            if key in model_key:
                pricing = value
                break

        if pricing is None:
            pricing = MODEL_PRICING["default"]
            logger.warning(f"No pricing found for model '{model}', using default pricing")

        # Calculate cost (pricing is per 1K tokens)
        cost_input = (tokens_in / 1000.0) * pricing["input"]
        cost_output = (tokens_out / 1000.0) * pricing["output"]

        return cost_input + cost_output

    def log_usage(
        self,
        document_id: Optional[int],
        step: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        duration_ms: int,
        payload_preview: Optional[str] = None,
        response_status: str = "success",
        full_request_log_path: Optional[str] = None,
    ) -> GenAIUsageLog:
        """Log LLM usage to database.

        Args:
            document_id: Associated document ID
            step: Processing step name
            model: Model name
            tokens_in: Input tokens
            tokens_out: Output tokens
            duration_ms: Duration in milliseconds
            payload_preview: Preview of request payload
            response_status: Status of response
            full_request_log_path: Path to full request log

        Returns:
            Created GenAIUsageLog entry
        """
        cost = self.calculate_cost(model, tokens_in, tokens_out)

        log_entry = GenAIUsageLog(
            document_id=document_id,
            timestamp=datetime.utcnow(),
            step=step,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost,
            duration_ms=duration_ms,
            payload_preview=payload_preview[:500] if payload_preview else None,
            response_status=response_status,
            full_request_log_path=full_request_log_path,
        )

        self.session.add(log_entry)
        self.session.commit()

        logger.debug(
            f"LLM usage logged: step={step}, model={model}, "
            f"tokens={tokens_in}+{tokens_out}, cost=${cost:.4f}, duration={duration_ms}ms"
        )

        return log_entry

    def get_daily_cost(self, date: Optional[datetime] = None) -> float:
        """Get total cost for a specific day.

        Args:
            date: Date to query (defaults to today)

        Returns:
            Total cost in USD
        """
        if date is None:
            date = datetime.utcnow()

        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        result = (
            self.session.query(GenAIUsageLog)
            .filter(
                GenAIUsageLog.timestamp >= start_of_day,
                GenAIUsageLog.timestamp < end_of_day,
            )
            .all()
        )

        total_cost = sum(log.cost or 0.0 for log in result)
        return total_cost

    def get_cost_by_step(self, days: int = 7) -> Dict[str, float]:
        """Get cost breakdown by processing step.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary mapping step name to total cost
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        result = (
            self.session.query(GenAIUsageLog)
            .filter(GenAIUsageLog.timestamp >= start_date)
            .all()
        )

        cost_by_step: Dict[str, float] = {}
        for log in result:
            cost_by_step[log.step] = cost_by_step.get(log.step, 0.0) + (log.cost or 0.0)

        return cost_by_step

    def get_usage_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive usage summary.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with usage statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        result = (
            self.session.query(GenAIUsageLog)
            .filter(GenAIUsageLog.timestamp >= start_date)
            .all()
        )

        total_cost = sum(log.cost or 0.0 for log in result)
        total_tokens_in = sum(log.tokens_in or 0 for log in result)
        total_tokens_out = sum(log.tokens_out or 0 for log in result)
        total_calls = len(result)

        cost_by_model: Dict[str, float] = {}
        for log in result:
            cost_by_model[log.model] = cost_by_model.get(log.model, 0.0) + (log.cost or 0.0)

        return {
            "period_days": days,
            "total_calls": total_calls,
            "total_cost": total_cost,
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
            "cost_by_model": cost_by_model,
            "cost_by_step": self.get_cost_by_step(days),
        }


class TimedLLMCall:
    """Context manager for timing and logging LLM calls."""

    def __init__(
        self,
        tracker: CostTracker,
        step: str,
        model: str,
        document_id: Optional[int] = None,
    ):
        """Initialize timed LLM call.

        Args:
            tracker: CostTracker instance
            step: Processing step name
            model: Model name
            document_id: Associated document ID
        """
        self.tracker = tracker
        self.step = step
        self.model = model
        self.document_id = document_id
        self.start_time = None
        self.tokens_in = 0
        self.tokens_out = 0
        self.status = "success"

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log usage."""
        duration_ms = int((time.time() - self.start_time) * 1000)

        if exc_type is not None:
            self.status = "error"

        self.tracker.log_usage(
            document_id=self.document_id,
            step=self.step,
            model=self.model,
            tokens_in=self.tokens_in,
            tokens_out=self.tokens_out,
            duration_ms=duration_ms,
            response_status=self.status,
        )

        return False  # Don't suppress exceptions

    def set_tokens(self, tokens_in: int, tokens_out: int):
        """Set token counts."""
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
