from pathlib import Path

from chatppt.app.domain.services.clarifier import Clarifier
from chatppt.app.domain.services.deck_outline_planner import DeckOutlinePlanner
from chatppt.app.domain.services.evidence_builder import EvidenceBuilder
from chatppt.app.domain.services.slide_planner import SlidePlanner
from chatppt.app.infra.llm_provider import FakeLLMProvider
from chatppt.app.orchestration.graph import GenerationOrchestrator
from chatppt.app.rendering.layout_matcher import LayoutMatcher
from chatppt.app.rendering.pptx_renderer import PptxRenderer
from chatppt.app.rendering.template_loader import TemplateLoader
from chatppt.app.validation.hard_validators import HardValidatorEngine


def test_orchestrator_generates_editable_deck(tmp_path):
    provider = FakeLLMProvider(
        {
            "topic": "Q2 launch",
            "audience": "executives",
            "use_case": "board update",
            "desired_tone": "confident",
            "expected_duration_minutes": 8,
            "preferred_language": "en",
            "must_include": ["launch goals"],
            "must_avoid": [],
            "available_materials": [],
            "approval_mode": "manual_review",
            "missing_info": [],
        }
    )
    orchestrator = GenerationOrchestrator(
        clarifier=Clarifier(provider),
        evidence_builder=EvidenceBuilder(),
        outline_planner=DeckOutlinePlanner(),
        slide_planner=SlidePlanner(),
        template_loader=TemplateLoader(),
        layout_matcher=LayoutMatcher(),
        renderer=PptxRenderer(),
        validator_engine=HardValidatorEngine(),
        template_root=Path("tests/fixtures/templates/default"),
        artifact_root=tmp_path,
    )

    result = orchestrator.generate("Create a board-ready Q2 launch deck")

    assert result.validation_report.passed is True
    assert result.editable_deck_state.slides[0].slide_id == "slide-1"
