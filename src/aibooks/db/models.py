"""SQLAlchemy database models for AIBooks."""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    ForeignKey,
    DateTime,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Document(Base):
    """Document metadata and processing information."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Metadata
    title = Column(String(500), nullable=True)
    author = Column(String(500), nullable=True)
    isbn = Column(String(20), nullable=True, index=True)
    publisher = Column(String(300), nullable=True)
    publication_date = Column(String(50), nullable=True)
    series = Column(String(300), nullable=True)
    series_index = Column(Float, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array as text
    language = Column(String(10), nullable=True)

    # File information
    format = Column(String(20), nullable=False, index=True)
    source_file = Column(String(1000), nullable=False)
    content_hash = Column(String(64), nullable=False, unique=True, index=True)

    # Processed content
    chapters_json = Column(Text, nullable=True)  # JSON structure
    tables_json = Column(Text, nullable=True)  # JSON structure
    metadata_json = Column(Text, nullable=True)  # Full combined metadata
    docling_json = Column(Text, nullable=True)  # Raw Docling output
    processed_text_path = Column(String(1000), nullable=True)

    # Statistics
    words = Column(Integer, nullable=True)
    pages = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Deduplication
    duplicate_of = Column(Integer, ForeignKey("documents.id"), nullable=True)

    # Relationships
    original_document = relationship("Document", remote_side=[id], backref="duplicates")
    usage_logs = relationship("GenAIUsageLog", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_author_title", "author", "title"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', author='{self.author}')>"


class GenAIUsageLog(Base):
    """Log of all LLM/GenAI API calls with cost and time tracking."""

    __tablename__ = "genai_usage_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True, index=True)

    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    duration_ms = Column(Integer, nullable=True)

    # LLM details
    step = Column(String(100), nullable=False, index=True)  # metadata, cleanup, agent_decision, etc.
    model = Column(String(100), nullable=False)

    # Token usage
    tokens_in = Column(Integer, nullable=True)
    tokens_out = Column(Integer, nullable=True)

    # Cost
    cost = Column(Float, nullable=True)

    # Request/Response
    payload_preview = Column(Text, nullable=True)  # First 500 chars
    response_status = Column(String(50), nullable=True)  # success, error, timeout
    full_request_log_path = Column(String(1000), nullable=True)  # Path to detailed log

    # Relationships
    document = relationship("Document", back_populates="usage_logs")

    __table_args__ = (
        Index("idx_timestamp_step", "timestamp", "step"),
        Index("idx_model_timestamp", "model", "timestamp"),
    )

    def __repr__(self):
        return f"<GenAIUsageLog(id={self.id}, step='{self.step}', model='{self.model}', cost={self.cost})>"


class AgentLearning(Base):
    """Agent learning memory - stores patterns, heuristics, and learned behaviors."""

    __tablename__ = "agent_learning"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Agent information
    agent_name = Column(String(100), nullable=False, index=True)  # format_strategist, metadata_intelligence, etc.
    learning_type = Column(String(100), nullable=False, index=True)  # pattern, heuristic, threshold, rule

    # Pattern details
    pattern_key = Column(String(200), nullable=False)  # e.g., "pdf_ocr_threshold", "filename_metadata_regex"
    pattern_value = Column(Text, nullable=False)  # JSON or text value

    # Performance metrics
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.5)  # 0.0 to 1.0

    # Context
    context_json = Column(Text, nullable=True)  # Additional context as JSON

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_agent_pattern", "agent_name", "pattern_key"),
        Index("idx_learning_type", "learning_type"),
        Index("idx_confidence", "confidence_score"),
        UniqueConstraint("agent_name", "pattern_key", name="uq_agent_pattern"),
    )

    def __repr__(self):
        return f"<AgentLearning(id={self.id}, agent='{self.agent_name}', pattern='{self.pattern_key}')>"
