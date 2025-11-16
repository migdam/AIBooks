"""Failure Recovery Agent - handles parsing failures and retries."""

import json
from typing import Dict, Any, List, Optional
from loguru import logger

from .base_agent import BaseAgent, AgentDecision


class FailureRecoveryAgent(BaseAgent):
    """Agent 5: Failure Recovery - handles failures and determines recovery strategy."""

    def __init__(self, session):
        """Initialize Failure Recovery Agent."""
        super().__init__("failure_recovery", session)

    def decide(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide on failure recovery strategy.

        Args:
            context: {
                "error": str,
                "error_type": str,
                "file_path": Path,
                "format": DocumentFormat,
                "previous_attempts": List[Dict],
                "original_strategy": Dict
            }

        Returns:
            AgentDecision with recovery strategy
        """
        error = context.get("error", "unknown")
        error_type = context.get("error_type", "unknown")
        attempts = context.get("previous_attempts", [])
        original_strategy = context.get("original_strategy", {})

        logger.warning(f"Failure Recovery analyzing error: {error_type}")

        # Check for learned recovery patterns
        pattern_key = f"recovery_{error_type}"
        learned = self.recall(pattern_key)

        if learned:
            logger.info(f"Using learned recovery strategy for: {error_type}")
            recovery_strategy = json.loads(learned.pattern_value)
            confidence = learned.confidence_score
        else:
            recovery_strategy = self._determine_recovery_strategy(
                error_type, attempts, original_strategy
            )
            confidence = 0.6

        # Determine if recovery should be attempted
        should_retry = self._should_retry(attempts, recovery_strategy)

        decision = AgentDecision(
            agent_name=self.name,
            decision_type="failure_recovery",
            decision={
                "recovery_strategy": recovery_strategy,
                "should_retry": should_retry,
                "max_retries_reached": len(attempts) >= 3,
                "fallback_method": recovery_strategy.get("fallback_method"),
            },
            confidence=confidence,
            reasoning=self._explain_recovery(error_type, recovery_strategy, attempts),
        )

        logger.info(
            f"Recovery strategy: {recovery_strategy.get('approach')}, "
            f"retry={should_retry}"
        )

        return decision

    def _determine_recovery_strategy(
        self, error_type: str, attempts: List[Dict], original_strategy: Dict
    ) -> Dict[str, Any]:
        """Determine recovery strategy based on error type.

        Args:
            error_type: Type of error
            attempts: Previous recovery attempts
            original_strategy: Original parsing strategy

        Returns:
            Recovery strategy dictionary
        """
        strategy = {
            "approach": "retry",
            "fallback_method": None,
            "modifications": [],
        }

        # OCR-related failures
        if "ocr" in error_type.lower() or "tesseract" in error_type.lower():
            strategy["approach"] = "switch_ocr"
            strategy["fallback_method"] = "ocr_only"
            strategy["modifications"] = [
                {"setting": "ocr_engine", "value": "docling_vision"},
                {"setting": "dpi", "value": 300},
            ]

        # Memory/timeout errors
        elif "memory" in error_type.lower() or "timeout" in error_type.lower():
            strategy["approach"] = "chunk_processing"
            strategy["modifications"] = [
                {"setting": "chunk_size", "value": 50},
                {"setting": "parallel", "value": False},
            ]

        # File format errors
        elif "format" in error_type.lower() or "corrupt" in error_type.lower():
            strategy["approach"] = "alternative_parser"
            strategy["fallback_method"] = "pymupdf"
            strategy["modifications"] = [
                {"setting": "parser", "value": "pymupdf"},
            ]

        # Permission/access errors
        elif "permission" in error_type.lower() or "access" in error_type.lower():
            strategy["approach"] = "abort"
            strategy["fallback_method"] = None

        # DRM errors
        elif "drm" in error_type.lower() or "encrypted" in error_type.lower():
            strategy["approach"] = "abort"
            strategy["fallback_method"] = None

        # Unknown errors - try simpler approach
        else:
            strategy["approach"] = "simplify"
            strategy["fallback_method"] = "text_only"
            strategy["modifications"] = [
                {"setting": "enable_ocr", "value": False},
                {"setting": "enable_vision", "value": False},
                {"setting": "tables", "value": False},
            ]

        return strategy

    def _should_retry(self, attempts: List[Dict], strategy: Dict[str, Any]) -> bool:
        """Determine if retry should be attempted.

        Args:
            attempts: Previous attempts
            strategy: Proposed recovery strategy

        Returns:
            True if retry should be attempted
        """
        # Max 3 retries
        if len(attempts) >= 3:
            logger.warning("Max retries reached, giving up")
            return False

        # Don't retry if strategy is abort
        if strategy.get("approach") == "abort":
            return False

        # Don't retry if same strategy was already tried
        for attempt in attempts:
            if attempt.get("strategy") == strategy:
                logger.debug("Strategy already tried, skipping")
                return False

        return True

    def _explain_recovery(
        self, error_type: str, strategy: Dict[str, Any], attempts: List[Dict]
    ) -> str:
        """Explain recovery decision.

        Args:
            error_type: Error type
            strategy: Recovery strategy
            attempts: Previous attempts

        Returns:
            Explanation string
        """
        reasons = []

        reasons.append(f"Error type: {error_type}")
        reasons.append(f"Recovery approach: {strategy['approach']}")

        if len(attempts) > 0:
            reasons.append(f"Previous attempts: {len(attempts)}")

        if strategy.get("fallback_method"):
            reasons.append(f"Fallback method: {strategy['fallback_method']}")

        if strategy.get("modifications"):
            mod_count = len(strategy["modifications"])
            reasons.append(f"Applying {mod_count} strategy modifications")

        return ". ".join(reasons)

    def report_recovery_outcome(
        self, error_type: str, strategy: Dict[str, Any], success: bool
    ):
        """Report recovery outcome for learning.

        Args:
            error_type: Error type
            strategy: Recovery strategy used
            success: Whether recovery succeeded
        """
        pattern_key = f"recovery_{error_type}"
        pattern_value = json.dumps(strategy)

        self.learn(
            pattern_key=pattern_key,
            pattern_value=pattern_value,
            learning_type="recovery",
            success=success,
            context={"error_type": error_type},
        )

        logger.info(
            f"Recorded recovery outcome for {error_type}: "
            f"{'success' if success else 'failure'}"
        )
