"""Database layer for AIBooks."""

from .models import Document, GenAIUsageLog, AgentLearning
from .database import Database, get_db

__all__ = ["Document", "GenAIUsageLog", "AgentLearning", "Database", "get_db"]
