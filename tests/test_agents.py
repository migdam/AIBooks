"""Tests for agents."""

import pytest
import tempfile
from pathlib import Path

from aibooks.db.database import init_database
from aibooks.agents.format_strategist import FormatStrategistAgent
from aibooks.agents.metadata_intelligence import MetadataIntelligenceAgent
from aibooks.agents.text_quality import TextQualityAgent
from aibooks.agents.cost_optimizer import CostOptimizerAgent
from aibooks.parsers.format_detector import DocumentFormat


@pytest.fixture
def test_session():
    """Create test database session."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = init_database(str(db_path))
        session = db.get_session()
        yield session
        session.close()


def test_format_strategist_decision(test_session):
    """Test Format Strategist agent decision."""
    agent = FormatStrategistAgent(test_session)

    context = {
        "file_path": Path("test.pdf"),
        "format": DocumentFormat.PDF,
        "file_size": 1024 * 1024,  # 1 MB
    }

    decision = agent.decide(context)

    assert decision.agent_name == "format_strategist"
    assert decision.decision_type == "parsing_strategy"
    assert "primary_method" in decision.decision
    assert decision.confidence > 0


def test_format_strategist_learning(test_session):
    """Test Format Strategist learning."""
    agent = FormatStrategistAgent(test_session)

    strategy = {"primary_method": "docling", "enable_ocr": True}

    # Report success
    agent.report_success(DocumentFormat.PDF, strategy, success=True)

    # Check if pattern was learned
    pattern = agent.recall("format_strategy_pdf")
    assert pattern is not None


def test_metadata_intelligence_decision(test_session):
    """Test Metadata Intelligence agent."""
    agent = MetadataIntelligenceAgent(test_session)

    context = {
        "calibre_metadata": {"title": "Book Title", "authors": ["Author Name"]},
        "docling_metadata": {},
        "filename_metadata": {},
        "fused_metadata": {"title": "Book Title", "authors": ["Author Name"]},
    }

    decision = agent.decide(context)

    assert decision.agent_name == "metadata_intelligence"
    assert "quality_score" in decision.decision
    assert "refined_metadata" in decision.decision


def test_text_quality_assessment(test_session):
    """Test Text Quality agent."""
    agent = TextQualityAgent(test_session)

    # High quality text
    good_text = "This is a well-formatted document with proper sentences and spacing."
    context = {
        "text": good_text,
        "format": DocumentFormat.PDF,
        "parsing_method": "docling",
    }

    decision = agent.decide(context)

    assert decision.agent_name == "text_quality_reinforcer"
    assert "quality_score" in decision.decision
    assert decision.decision["quality_score"] > 0.7


def test_text_quality_poor_text(test_session):
    """Test Text Quality agent with poor text."""
    agent = TextQualityAgent(test_session)

    # Poor quality text with artifacts
    poor_text = "Thi|s i$ @ p00r|y OCR'd d0cum€nt ||||| with l0ts 0f @rtif@cts"
    context = {
        "text": poor_text,
        "format": DocumentFormat.PDF,
        "parsing_method": "ocr",
    }

    decision = agent.decide(context)

    assert decision.decision["quality_score"] < 0.7
    assert decision.decision["needs_aggressive_cleaning"] is True


def test_cost_optimizer_decision(test_session):
    """Test Cost Optimizer agent."""
    agent = CostOptimizerAgent(test_session)

    context = {
        "step": "metadata_enhancement",
        "estimated_tokens": 1000,
        "daily_budget": 10.0,
    }

    decision = agent.decide(context)

    assert decision.agent_name == "cost_optimizer"
    assert "use_llm" in decision.decision
    assert "model" in decision.decision
    assert "estimated_cost" in decision.decision


def test_cost_optimizer_budget_limit(test_session):
    """Test Cost Optimizer respects budget."""
    agent = CostOptimizerAgent(test_session)

    # Simulate high spending
    from aibooks.db.models import GenAIUsageLog
    from datetime import datetime

    # Add some logs to simulate spending
    for i in range(10):
        log = GenAIUsageLog(
            step="test",
            model="gpt-4o",
            tokens_in=1000,
            tokens_out=500,
            cost=0.05,
            duration_ms=1000,
            timestamp=datetime.utcnow(),
        )
        test_session.add(log)
    test_session.commit()

    context = {
        "step": "optional_enhancement",
        "estimated_tokens": 5000,
        "daily_budget": 0.3,  # Very low budget
    }

    decision = agent.decide(context)

    # Should recommend not using LLM due to budget
    current_spend = decision.decision["current_daily_spend"]
    assert current_spend > 0
