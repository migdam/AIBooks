"""Base agent class for all agentic components."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from ..db.models import AgentLearning


@dataclass
class AgentDecision:
    """Decision made by an agent."""

    agent_name: str
    decision_type: str
    decision: Dict[str, Any]
    confidence: float  # 0.0 to 1.0
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, name: str, session: Session):
        """Initialize agent.

        Args:
            name: Agent name
            session: Database session
        """
        self.name = name
        self.session = session
        logger.info(f"Initialized agent: {name}")

    @abstractmethod
    def decide(self, context: Dict[str, Any]) -> AgentDecision:
        """Make a decision based on context.

        Args:
            context: Context dictionary with relevant information

        Returns:
            AgentDecision object
        """
        pass

    def learn(
        self,
        pattern_key: str,
        pattern_value: str,
        learning_type: str = "pattern",
        success: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Store learned pattern.

        Args:
            pattern_key: Pattern identifier
            pattern_value: Pattern value (can be JSON)
            learning_type: Type of learning (pattern, heuristic, threshold, rule)
            success: Whether this was a successful pattern
            context: Additional context
        """
        # Check if pattern exists
        existing = (
            self.session.query(AgentLearning)
            .filter_by(agent_name=self.name, pattern_key=pattern_key)
            .first()
        )

        if existing:
            # Update existing pattern
            if success:
                existing.success_count += 1
            else:
                existing.failure_count += 1

            # Update confidence score
            total = existing.success_count + existing.failure_count
            existing.confidence_score = existing.success_count / total

            existing.pattern_value = pattern_value
            existing.updated_at = datetime.utcnow()
            existing.last_used_at = datetime.utcnow()

            if context:
                import json
                existing.context_json = json.dumps(context)

        else:
            # Create new pattern
            new_learning = AgentLearning(
                agent_name=self.name,
                learning_type=learning_type,
                pattern_key=pattern_key,
                pattern_value=pattern_value,
                success_count=1 if success else 0,
                failure_count=0 if success else 1,
                confidence_score=1.0 if success else 0.0,
                context_json=None if not context else __import__('json').dumps(context),
                last_used_at=datetime.utcnow(),
            )
            self.session.add(new_learning)

        self.session.commit()

        logger.debug(
            f"Agent {self.name} learned: {pattern_key} = {pattern_value} "
            f"(success={success}, type={learning_type})"
        )

    def recall(
        self, pattern_key: str, min_confidence: float = 0.5
    ) -> Optional[AgentLearning]:
        """Recall a learned pattern.

        Args:
            pattern_key: Pattern identifier
            min_confidence: Minimum confidence threshold

        Returns:
            AgentLearning object or None
        """
        pattern = (
            self.session.query(AgentLearning)
            .filter_by(agent_name=self.name, pattern_key=pattern_key)
            .filter(AgentLearning.confidence_score >= min_confidence)
            .first()
        )

        if pattern:
            # Update last used
            pattern.last_used_at = datetime.utcnow()
            self.session.commit()

        return pattern

    def get_all_patterns(
        self, learning_type: Optional[str] = None, min_confidence: float = 0.5
    ) -> List[AgentLearning]:
        """Get all learned patterns.

        Args:
            learning_type: Filter by learning type
            min_confidence: Minimum confidence threshold

        Returns:
            List of AgentLearning objects
        """
        query = self.session.query(AgentLearning).filter_by(agent_name=self.name)

        if learning_type:
            query = query.filter_by(learning_type=learning_type)

        query = query.filter(AgentLearning.confidence_score >= min_confidence)

        return query.all()

    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics.

        Returns:
            Dictionary with agent statistics
        """
        patterns = self.session.query(AgentLearning).filter_by(agent_name=self.name).all()

        total_patterns = len(patterns)
        total_successes = sum(p.success_count for p in patterns)
        total_failures = sum(p.failure_count for p in patterns)
        avg_confidence = sum(p.confidence_score for p in patterns) / total_patterns if total_patterns > 0 else 0.0

        learning_types = {}
        for pattern in patterns:
            learning_types[pattern.learning_type] = learning_types.get(pattern.learning_type, 0) + 1

        return {
            "agent_name": self.name,
            "total_patterns": total_patterns,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "average_confidence": avg_confidence,
            "learning_types": learning_types,
        }
