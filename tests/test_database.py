"""Tests for database models and operations."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import os

from aibooks.db.database import Database, init_database
from aibooks.db.models import Document, GenAIUsageLog, AgentLearning


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = init_database(str(db_path))
        yield db
        # Cleanup happens automatically with tempfile


def test_database_initialization(test_db):
    """Test database initialization."""
    assert test_db.database_path.exists()
    assert test_db.engine is not None


def test_create_document(test_db):
    """Test creating a document."""
    with test_db.session_scope() as session:
        doc = Document(
            title="Test Book",
            author="Test Author",
            isbn="1234567890",
            format="pdf",
            source_file="/path/to/test.pdf",
            content_hash="abc123",
            words=1000,
            pages=10,
        )
        session.add(doc)
        session.commit()

        # Query it back
        retrieved = session.query(Document).filter_by(title="Test Book").first()
        assert retrieved is not None
        assert retrieved.author == "Test Author"
        assert retrieved.isbn == "1234567890"


def test_genai_usage_log(test_db):
    """Test creating GenAI usage log."""
    with test_db.session_scope() as session:
        log = GenAIUsageLog(
            step="metadata_extraction",
            model="gpt-4o-mini",
            tokens_in=100,
            tokens_out=50,
            cost=0.0001,
            duration_ms=500,
            response_status="success",
        )
        session.add(log)
        session.commit()

        # Query it back
        retrieved = session.query(GenAIUsageLog).first()
        assert retrieved is not None
        assert retrieved.model == "gpt-4o-mini"
        assert retrieved.cost == 0.0001


def test_agent_learning(test_db):
    """Test agent learning storage."""
    with test_db.session_scope() as session:
        learning = AgentLearning(
            agent_name="format_strategist",
            learning_type="pattern",
            pattern_key="pdf_strategy",
            pattern_value='{"method": "docling"}',
            success_count=5,
            failure_count=1,
            confidence_score=0.83,
        )
        session.add(learning)
        session.commit()

        # Query it back
        retrieved = session.query(AgentLearning).filter_by(
            agent_name="format_strategist"
        ).first()
        assert retrieved is not None
        assert retrieved.confidence_score == 0.83


def test_document_duplicate_relationship(test_db):
    """Test duplicate document relationship."""
    with test_db.session_scope() as session:
        # Original document
        original = Document(
            title="Original",
            format="pdf",
            source_file="/path/to/original.pdf",
            content_hash="hash1",
        )
        session.add(original)
        session.flush()

        # Duplicate
        duplicate = Document(
            title="Duplicate",
            format="pdf",
            source_file="/path/to/duplicate.pdf",
            content_hash="hash2",
            duplicate_of=original.id,
        )
        session.add(duplicate)
        session.commit()

        # Check relationship
        dup = session.query(Document).filter_by(title="Duplicate").first()
        assert dup.duplicate_of == original.id
        assert dup.original_document.title == "Original"


def test_content_hash_uniqueness(test_db):
    """Test that content_hash must be unique."""
    with test_db.session_scope() as session:
        doc1 = Document(
            title="Doc1",
            format="pdf",
            source_file="/path/1.pdf",
            content_hash="same_hash",
        )
        session.add(doc1)
        session.commit()

    # Try to add another with same hash
    with pytest.raises(Exception):  # Should raise integrity error
        with test_db.session_scope() as session:
            doc2 = Document(
                title="Doc2",
                format="pdf",
                source_file="/path/2.pdf",
                content_hash="same_hash",
            )
            session.add(doc2)
            session.commit()
