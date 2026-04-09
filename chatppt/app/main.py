from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI

from chatppt.app.api.routes_edit import build_edit_router
from chatppt.app.api.routes_generate import build_generate_router
from chatppt.app.api.routes_templates import build_template_router
from chatppt.app.domain.services.clarifier import Clarifier
from chatppt.app.domain.services.deck_outline_planner import DeckOutlinePlanner
from chatppt.app.domain.services.evidence_builder import EvidenceBuilder
from chatppt.app.domain.services.semantic_reviewer import SemanticReviewer
from chatppt.app.domain.services.slide_planner import SlidePlanner
from chatppt.app.editing.dependency_analyzer import DependencyAnalyzer
from chatppt.app.editing.edit_parser import EditParser
from chatppt.app.editing.page_regenerator import PageRegenerator
from chatppt.app.infra.cache import InMemoryCache
from chatppt.app.infra.llm_provider import LLMProvider, UnconfiguredLLMProvider
from chatppt.app.infra.telemetry import Telemetry
from chatppt.app.orchestration.graph import GenerationOrchestrator
from chatppt.app.rendering.layout_matcher import LayoutMatcher
from chatppt.app.rendering.pptx_renderer import PptxRenderer
from chatppt.app.rendering.template_loader import TemplateLoader
from chatppt.app.validation.hard_validators import HardValidatorEngine


def create_app(
    artifact_root: str | Path = "artifacts",
    template_root: str | Path = "templates/default",
    llm_provider: LLMProvider | None = None,
) -> FastAPI:
    app = FastAPI(title="ChatPPT")
    artifact_root = Path(artifact_root)
    template_root = Path(template_root)

    provider = llm_provider or UnconfiguredLLMProvider()
    template_loader = TemplateLoader()
    layout_matcher = LayoutMatcher()
    renderer = PptxRenderer(layout_matcher=layout_matcher)
    validator_engine = HardValidatorEngine()
    orchestrator = GenerationOrchestrator(
        clarifier=Clarifier(provider),
        evidence_builder=EvidenceBuilder(),
        outline_planner=DeckOutlinePlanner(),
        slide_planner=SlidePlanner(),
        template_loader=template_loader,
        layout_matcher=layout_matcher,
        renderer=renderer,
        validator_engine=validator_engine,
        semantic_reviewer=SemanticReviewer(),
        template_root=template_root,
        artifact_root=artifact_root,
    )
    edit_service = PageRegenerator(
        edit_parser=EditParser(),
        dependency_analyzer=DependencyAnalyzer(),
        renderer=renderer,
        layout_matcher=layout_matcher,
        validator_engine=validator_engine,
    )
    template = template_loader.load(template_root)
    cache = InMemoryCache()
    telemetry = Telemetry()
    generation_store: dict[str, object] = {}

    def get_orchestrator() -> GenerationOrchestrator:
        return orchestrator

    def get_edit_service() -> PageRegenerator:
        return edit_service

    def get_generation_store():
        return generation_store

    def get_template():
        return template

    def get_telemetry():
        return telemetry

    app.include_router(build_generate_router(get_orchestrator, get_generation_store, get_telemetry), prefix="/api/v1")
    app.include_router(build_edit_router(get_edit_service, get_generation_store, get_template), prefix="/api/v1")
    app.include_router(build_template_router(get_template), prefix="/api/v1")

    @app.post("/api/v1/generate-and-store")
    def generate_and_store(payload: dict):
        result = orchestrator.generate(payload["brief"], [])
        generation_id = str(uuid4())
        generation_store[generation_id] = result
        telemetry.increment("generation.success")
        cache.set(generation_id, result)
        return {"generation_id": generation_id, "result": result.model_dump(mode="json")}

    return app
