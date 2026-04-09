from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from chatppt.app.domain.models.clarified_spec import ClarifierOutput
from chatppt.app.domain.models.deck_ir import DeckIR
from chatppt.app.domain.models.deck_outline import DeckOutline
from chatppt.app.domain.models.evidence_pack import EvidencePack
from chatppt.app.domain.services.clarifier import Clarifier
from chatppt.app.domain.services.deck_outline_planner import DeckOutlinePlanner
from chatppt.app.domain.services.evidence_builder import EvidenceBuilder, SourceDocument
from chatppt.app.domain.services.semantic_reviewer import SemanticReviewer
from chatppt.app.domain.services.slide_planner import SlidePlanner
from chatppt.app.orchestration.state import GenerationArtifacts, ValidationReport
from chatppt.app.rendering.layout_matcher import LayoutMatcher
from chatppt.app.rendering.pptx_renderer import PptxRenderer, RenderOutput
from chatppt.app.rendering.template_loader import TemplateLoader
from chatppt.app.validation.autofix import AutoFixEngine
from chatppt.app.validation.hard_validators import HardValidatorEngine


class GenerationGraphState(TypedDict, total=False):
    brief: str
    documents: list[dict[str, Any]]
    clarifier_output: ClarifierOutput
    evidence_pack: EvidencePack
    outline: DeckOutline
    deck: DeckIR
    render_output: RenderOutput
    validation_report: ValidationReport
    semantic_findings: list


class GenerationOrchestrator:
    def __init__(
        self,
        clarifier: Clarifier,
        evidence_builder: EvidenceBuilder,
        outline_planner: DeckOutlinePlanner,
        slide_planner: SlidePlanner,
        template_loader: TemplateLoader,
        layout_matcher: LayoutMatcher,
        renderer: PptxRenderer,
        validator_engine: HardValidatorEngine,
        template_root: Path,
        artifact_root: Path,
        semantic_reviewer: SemanticReviewer | None = None,
        autofix_engine: AutoFixEngine | None = None,
    ):
        self.clarifier = clarifier
        self.evidence_builder = evidence_builder
        self.outline_planner = outline_planner
        self.slide_planner = slide_planner
        self.template_loader = template_loader
        self.layout_matcher = layout_matcher
        self.renderer = renderer
        self.validator_engine = validator_engine
        self.semantic_reviewer = semantic_reviewer or SemanticReviewer()
        self.autofix_engine = autofix_engine or AutoFixEngine()
        self.template_root = Path(template_root)
        self.artifact_root = Path(artifact_root)
        self.graph = self._build_graph()

    def generate(self, brief: str, documents: list[SourceDocument] | None = None) -> GenerationArtifacts:
        final_state = self.graph.invoke({"brief": brief, "documents": [doc.model_dump() for doc in (documents or [])]})
        clarifier_output = final_state["clarifier_output"]
        if clarifier_output.missing_info:
            raise ValueError(f"Missing information: {clarifier_output.missing_info}")
        render_output = final_state["render_output"]
        return GenerationArtifacts(
            deck=final_state["deck"],
            outline=final_state["outline"],
            evidence_pack=final_state["evidence_pack"],
            manifest=render_output.manifest,
            validation_report=final_state["validation_report"],
            editable_deck_state=render_output.editable_deck_state,
            semantic_findings=final_state["semantic_findings"],
            pptx_path=render_output.pptx_path,
        )

    def _build_graph(self):
        builder = StateGraph(GenerationGraphState)
        builder.add_node("clarify", self._clarify)
        builder.add_node("build_evidence", self._build_evidence)
        builder.add_node("plan_outline", self._plan_outline)
        builder.add_node("plan_slides", self._plan_slides)
        builder.add_node("render", self._render)
        builder.add_node("validate", self._validate)
        builder.add_node("semantic_review", self._semantic_review)

        builder.add_edge(START, "clarify")
        builder.add_conditional_edges(
            "clarify",
            self._route_after_clarify,
            {"need_input": END, "continue": "build_evidence"},
        )
        builder.add_edge("build_evidence", "plan_outline")
        builder.add_edge("plan_outline", "plan_slides")
        builder.add_edge("plan_slides", "render")
        builder.add_edge("render", "validate")
        builder.add_edge("validate", "semantic_review")
        builder.add_edge("semantic_review", END)
        return builder.compile()

    def _clarify(self, state: GenerationGraphState) -> GenerationGraphState:
        return {"clarifier_output": self.clarifier.clarify(state["brief"])}

    def _route_after_clarify(self, state: GenerationGraphState) -> str:
        clarifier_output = state["clarifier_output"]
        return "need_input" if clarifier_output.missing_info else "continue"

    def _build_evidence(self, state: GenerationGraphState) -> GenerationGraphState:
        documents = [SourceDocument.model_validate(item) for item in state.get("documents", [])]
        evidence_pack = self.evidence_builder.build(state["clarifier_output"].clarified_spec, documents)
        return {"evidence_pack": evidence_pack}

    def _plan_outline(self, state: GenerationGraphState) -> GenerationGraphState:
        outline = self.outline_planner.plan(state["clarifier_output"].clarified_spec, state["evidence_pack"])
        return {"outline": outline}

    def _plan_slides(self, state: GenerationGraphState) -> GenerationGraphState:
        deck = self.slide_planner.plan(
            state["clarifier_output"].clarified_spec,
            state["outline"],
            state["evidence_pack"],
        )
        return {"deck": deck}

    def _render(self, state: GenerationGraphState) -> GenerationGraphState:
        template = self.template_loader.load(self.template_root)
        render_output = self.renderer.render(state["deck"], template, self.artifact_root)
        return {"render_output": render_output}

    def _validate(self, state: GenerationGraphState) -> GenerationGraphState:
        validation_report = self.validator_engine.validate(state["deck"], state["render_output"].manifest)
        if not validation_report.passed:
            autofixed_deck = self.autofix_engine.apply(state["deck"].model_copy(deep=True))
            template = self.template_loader.load(self.template_root)
            render_output = self.renderer.render(autofixed_deck, template, self.artifact_root)
            validation_report = self.validator_engine.validate(autofixed_deck, render_output.manifest)
            return {"deck": autofixed_deck, "render_output": render_output, "validation_report": validation_report}
        return {"validation_report": validation_report}

    def _semantic_review(self, state: GenerationGraphState) -> GenerationGraphState:
        findings = self.semantic_reviewer.review(state["deck"], state["evidence_pack"])
        return {"semantic_findings": findings}
