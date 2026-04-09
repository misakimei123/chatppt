"""
End-to-end integration test for ChatPPT generation flow.

This test verifies the complete generation pipeline with mocked LLM responses.
"""

from pathlib import Path

import pytest

from chatppt.app.domain.models.clarified_spec import ClarifiedSpec
from chatppt.app.domain.models.evidence_pack import EvidenceFact, EvidencePack, EvidenceSource, EvidenceSuggestion
from chatppt.app.domain.services.clarifier import Clarifier
from chatppt.app.domain.services.deck_outline_planner import DeckOutlinePlanner
from chatppt.app.domain.services.evidence_builder import EvidenceBuilder, SourceDocument
from chatppt.app.domain.services.slide_planner import SlidePlanner
from chatppt.app.infra.llm_provider import FakeLLMProvider
from chatppt.app.orchestration.graph import GenerationOrchestrator
from chatppt.app.rendering.layout_matcher import LayoutMatcher
from chatppt.app.rendering.pptx_renderer import PptxRenderer
from chatppt.app.rendering.template_loader import TemplateLoader
from chatppt.app.validation.hard_validators import HardValidatorEngine


@pytest.fixture
def mock_llm_provider():
    """Create a FakeLLMProvider with realistic mock responses."""
    return FakeLLMProvider(
        {
            "clarify": {
                "topic": "Q2 Product Launch",
                "audience": "executives",
                "use_case": "board update",
                "desired_tone": "confident",
                "expected_duration_minutes": 8,
                "preferred_language": "en",
                "must_include": ["launch goals", "market analysis"],
                "must_avoid": ["technical jargon"],
                "available_materials": [],
                "approval_mode": "manual_review",
                "missing_info": [],
            }
        }
    )


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for artifacts and templates."""
    artifact_root = tmp_path / "artifacts"
    template_root = tmp_path / "templates" / "default"
    template_root.mkdir(parents=True)
    
    # Create minimal template structure
    (template_root / "meta.json").write_text('{"template_id": "test", "display_name": "Test Template", "layouts": []}')
    (template_root / "brand_rules.json").write_text('{}')
    
    return artifact_root, template_root


def test_full_generation_flow(mock_llm_provider, temp_dirs):
    """Test complete generation flow from brief to PPTX."""
    artifact_root, template_root = temp_dirs
    
    orchestrator = GenerationOrchestrator(
        clarifier=Clarifier(mock_llm_provider),
        evidence_builder=EvidenceBuilder(),
        outline_planner=DeckOutlinePlanner(),
        slide_planner=SlidePlanner(),
        template_loader=TemplateLoader(),
        layout_matcher=LayoutMatcher(),
        renderer=PptxRenderer(),
        validator_engine=HardValidatorEngine(),
        semantic_reviewer=None,
        template_root=template_root,
        artifact_root=artifact_root,
    )
    
    brief = "Create a board-ready Q2 product launch deck"
    result = orchestrator.generate(brief)
    
    # Verify generation succeeded
    assert result.deck is not None
    assert len(result.deck.slides) > 0
    assert result.validation_report.passed is True
    assert result.pptx_path.exists()


def test_evidence_builder_with_documents(temp_dirs):
    """Test EvidenceBuilder with uploaded documents."""
    artifact_root, template_root = temp_dirs
    
    builder = EvidenceBuilder(enable_cache=False)
    
    spec = ClarifiedSpec(
        topic="AI Trends",
        audience="researchers",
        use_case="conference presentation",
        desired_tone="professional",
        expected_duration_minutes=15,
        preferred_language="en",
        must_include=["recent developments"],
        must_avoid=[],
        available_materials=[],
        approval_mode="manual_review",
    )
    
    documents = [
        SourceDocument(
            title="AI Research Paper",
            uri="file:///papers/ai_trends.pdf",
            content="FACT: Transformer models dominate NLP\nFACT: LLMs show emergent capabilities\nSUGGESTION: Include ethical considerations",
            source_type="user_upload",
        )
    ]
    
    evidence_pack = builder.build(spec, documents)
    
    # Verify facts extracted from documents
    assert len(evidence_pack.facts) == 2
    assert evidence_pack.facts[0].claim == "Transformer models dominate NLP"
    assert evidence_pack.facts[0].source.source_type == "user_upload"
    assert evidence_pack.facts[0].source.reliability == 0.9
    
    # Verify suggestions extracted
    assert len(evidence_pack.suggestions) >= 1
    assert any("ethical considerations" in s.text for s in evidence_pack.suggestions)


def test_evidence_builder_caching():
    """Test EvidenceBuilder caching mechanism."""
    builder = EvidenceBuilder(enable_cache=True)
    
    spec = ClarifiedSpec(
        topic="Cached Topic",
        audience="test",
        use_case="test",
        desired_tone="neutral",
        expected_duration_minutes=5,
        preferred_language="en",
        must_include=[],
        must_avoid=[],
        available_materials=[],
        approval_mode="manual_review",
    )
    
    # First call - should build from scratch
    pack1 = builder.build(spec)
    
    # Second call - should hit cache
    pack2 = builder.build(spec)
    
    # Verify cache hit (same object or equivalent)
    assert pack1.facts == pack2.facts
    assert pack1.suggestions == pack2.suggestions


def test_evidence_pack_includes_search_queries():
    """Test that EvidencePack tracks search queries."""
    builder = EvidenceBuilder(enable_cache=False)
    
    spec = ClarifiedSpec(
        topic="Market Research",
        audience="investors",
        use_case="pitch deck",
        desired_tone="persuasive",
        expected_duration_minutes=10,
        preferred_language="en",
        must_include=["market size"],
        must_avoid=[],
        available_materials=[],
        approval_mode="manual_review",
    )
    
    evidence_pack = builder.build(spec)
    
    # Verify search_queries field exists (even if empty when no web search)
    assert hasattr(evidence_pack, 'search_queries')
    assert isinstance(evidence_pack.search_queries, list)


def test_qwen_provider_initialization():
    """Test QwenProvider can be initialized with various configurations."""
    from chatppt.app.infra.llm_provider import QwenProvider
    
    # Test with environment variables (defaults)
    provider1 = QwenProvider()
    assert provider1.model is not None
    assert provider1.base_url is not None
    
    # Test with explicit configuration
    provider2 = QwenProvider(
        api_key="test-key",
        base_url="https://test.api.com/v1",
        model="test-model",
        max_retries=5,
        timeout=60.0,
    )
    assert provider2.api_key == "test-key"
    assert provider2.model == "test-model"
    assert provider2.max_retries == 5


def test_qwen_provider_structured_generation():
    """Test QwenProvider generate_structured method signature."""
    from chatppt.app.infra.llm_provider import QwenProvider
    
    provider = QwenProvider(api_key="test-key")
    
    # Verify method exists and has correct signature
    assert hasattr(provider, 'generate_structured')
    assert callable(provider.generate_structured)
    
    # Note: Actual API call would fail without valid key, but we're testing interface
    try:
        result = provider.generate_structured(
            task_name="test_task",
            prompt="Test prompt",
            schema_name="TestSchema",
        )
        # If it doesn't raise an error, result should be dict (or empty dict on parse failure)
        assert isinstance(result, dict)
    except RuntimeError as e:
        # Expected when API call fails due to invalid key
        assert "Failed" in str(e) or "error" in str(e).lower()
