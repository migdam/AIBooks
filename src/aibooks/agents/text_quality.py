"""Text Quality Reinforcer Agent - evaluates and improves text quality."""

import re
from typing import Dict, Any
from loguru import logger

from .base_agent import BaseAgent, AgentDecision


class TextQualityAgent(BaseAgent):
    """Agent 3: Text Quality Reinforcer - evaluates and improves extracted text."""

    def __init__(self, session):
        """Initialize Text Quality Agent."""
        super().__init__("text_quality_reinforcer", session)

        # Compile quality check patterns
        self.ocr_artifact_pattern = re.compile(r'[|]{2,}|[_]{3,}|[@#$%]{2,}')
        self.broken_hyphen_pattern = re.compile(r'\w+-\s*\n\s*\w+')
        self.excessive_whitespace_pattern = re.compile(r'\s{3,}')

    def decide(self, context: Dict[str, Any]) -> AgentDecision:
        """Evaluate text quality and determine cleaning strategy.

        Args:
            context: {
                "text": str,
                "format": DocumentFormat,
                "parsing_method": str,
                "sample_size": Optional[int]
            }

        Returns:
            AgentDecision with quality assessment and cleaning strategy
        """
        text = context.get("text", "")
        parsing_method = context.get("parsing_method", "unknown")

        logger.info("Text Quality Agent analyzing text quality")

        # Analyze text quality
        quality_metrics = self._analyze_quality(text)

        # Determine cleaning strategy
        cleaning_strategy = self._determine_cleaning_strategy(quality_metrics)

        # Calculate overall quality score
        quality_score = self._calculate_quality_score(quality_metrics)

        decision = AgentDecision(
            agent_name=self.name,
            decision_type="text_quality_assessment",
            decision={
                "quality_metrics": quality_metrics,
                "cleaning_strategy": cleaning_strategy,
                "quality_score": quality_score,
                "needs_aggressive_cleaning": quality_score < 0.6,
            },
            confidence=0.8,
            reasoning=self._explain_quality(quality_metrics, quality_score),
        )

        logger.info(
            f"Text quality score: {quality_score:.2f}, "
            f"Cleaning strategy: {cleaning_strategy['level']}"
        )

        return decision

    def _analyze_quality(self, text: str) -> Dict[str, Any]:
        """Analyze text quality metrics.

        Args:
            text: Text to analyze

        Returns:
            Dictionary of quality metrics
        """
        if not text:
            return {
                "ocr_artifacts": 0,
                "broken_hyphens": 0,
                "excessive_whitespace": 0,
                "avg_word_length": 0,
                "numeric_ratio": 0,
                "special_char_ratio": 0,
            }

        # Count various issues
        ocr_artifacts = len(self.ocr_artifact_pattern.findall(text[:10000]))
        broken_hyphens = len(self.broken_hyphen_pattern.findall(text[:10000]))
        excessive_whitespace = len(self.excessive_whitespace_pattern.findall(text[:10000]))

        # Calculate text statistics
        words = text.split()
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0

        # Character type ratios
        total_chars = len(text)
        numeric_chars = sum(1 for c in text if c.isdigit())
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())

        numeric_ratio = numeric_chars / total_chars if total_chars > 0 else 0
        special_char_ratio = special_chars / total_chars if total_chars > 0 else 0

        return {
            "ocr_artifacts": ocr_artifacts,
            "broken_hyphens": broken_hyphens,
            "excessive_whitespace": excessive_whitespace,
            "avg_word_length": avg_word_length,
            "numeric_ratio": numeric_ratio,
            "special_char_ratio": special_char_ratio,
            "total_words": len(words),
        }

    def _calculate_quality_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score.

        Args:
            metrics: Quality metrics

        Returns:
            Quality score (0.0 to 1.0)
        """
        score = 1.0

        # Penalize for issues (per 1000 words)
        words = max(metrics["total_words"], 1)
        normalization = 1000.0 / words

        # OCR artifacts penalty
        ocr_penalty = min(metrics["ocr_artifacts"] * normalization * 0.1, 0.3)
        score -= ocr_penalty

        # Broken hyphens penalty
        hyphen_penalty = min(metrics["broken_hyphens"] * normalization * 0.05, 0.2)
        score -= hyphen_penalty

        # Excessive whitespace penalty
        whitespace_penalty = min(metrics["excessive_whitespace"] * normalization * 0.02, 0.1)
        score -= whitespace_penalty

        # Special character ratio penalty (if too high)
        if metrics["special_char_ratio"] > 0.1:
            score -= min((metrics["special_char_ratio"] - 0.1) * 2, 0.2)

        # Word length check (OCR often produces very short or very long "words")
        if metrics["avg_word_length"] < 3 or metrics["avg_word_length"] > 15:
            score -= 0.1

        return max(score, 0.0)

    def _determine_cleaning_strategy(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Determine text cleaning strategy.

        Args:
            metrics: Quality metrics

        Returns:
            Cleaning strategy dictionary
        """
        quality_score = self._calculate_quality_score(metrics)

        strategy = {
            "remove_hyphenation": True,
            "normalize_unicode": True,
            "normalize_quotes": True,
            "normalize_whitespace": True,
            "remove_page_numbers": True,
            "remove_ocr_artifacts": False,
            "remove_headers_footers": False,
            "level": "basic",
        }

        # Moderate cleaning for medium quality
        if quality_score < 0.8:
            strategy["remove_ocr_artifacts"] = True
            strategy["remove_headers_footers"] = True
            strategy["level"] = "moderate"

        # Aggressive cleaning for low quality
        if quality_score < 0.6:
            strategy["aggressive_ocr_cleanup"] = True
            strategy["llm_assisted_cleanup"] = True
            strategy["level"] = "aggressive"

        return strategy

    def _explain_quality(self, metrics: Dict[str, Any], quality_score: float) -> str:
        """Explain quality assessment.

        Args:
            metrics: Quality metrics
            quality_score: Overall quality score

        Returns:
            Explanation string
        """
        reasons = []

        if quality_score >= 0.8:
            reasons.append("High quality text with minimal issues")
        elif quality_score >= 0.6:
            reasons.append("Moderate quality text requiring standard cleaning")
        else:
            reasons.append("Low quality text requiring aggressive cleaning")

        if metrics["ocr_artifacts"] > 10:
            reasons.append(f"Detected {metrics['ocr_artifacts']} OCR artifacts")

        if metrics["broken_hyphens"] > 5:
            reasons.append(f"Found {metrics['broken_hyphens']} broken hyphenations")

        if metrics["special_char_ratio"] > 0.1:
            reasons.append("High special character ratio indicating noise")

        return ". ".join(reasons)

    def report_cleaning_success(self, strategy: Dict[str, Any], success: bool):
        """Report success of cleaning strategy.

        Args:
            strategy: Cleaning strategy used
            success: Whether cleaning improved text quality
        """
        import json

        pattern_key = f"cleaning_strategy_{strategy['level']}"
        pattern_value = json.dumps(strategy)

        self.learn(
            pattern_key=pattern_key,
            pattern_value=pattern_value,
            learning_type="strategy",
            success=success,
            context={"level": strategy["level"]},
        )
