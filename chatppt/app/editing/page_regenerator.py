from __future__ import annotations

from pathlib import Path

from chatppt.app.editing.dependency_analyzer import DependencyAnalyzer
from chatppt.app.editing.edit_parser import EditParser
from chatppt.app.orchestration.state import GenerationArtifacts
from chatppt.app.rendering.layout_matcher import LayoutMatcher
from chatppt.app.rendering.pptx_renderer import PptxRenderer
from chatppt.app.rendering.template_loader import TemplateMeta
from chatppt.app.validation.hard_validators import HardValidatorEngine


class PageRegenerator:
    def __init__(
        self,
        edit_parser: EditParser,
        dependency_analyzer: DependencyAnalyzer,
        renderer: PptxRenderer,
        layout_matcher: LayoutMatcher,
        validator_engine: HardValidatorEngine,
    ):
        self.edit_parser = edit_parser
        self.dependency_analyzer = dependency_analyzer
        self.renderer = renderer
        self.layout_matcher = layout_matcher
        self.validator_engine = validator_engine

    def apply_edit(self, generated: GenerationArtifacts, instruction: str, template: TemplateMeta, artifact_root: Path) -> GenerationArtifacts:
        action = self.edit_parser.parse(instruction)
        if action.action_type == "unsupported":
            raise ValueError(f"Unsupported edit instruction: {instruction}")

        deck = generated.deck.model_copy(deep=True)
        impacted_indices = self.dependency_analyzer.impacted_slide_indices(action, len(deck.slides))
        for index in impacted_indices:
            slide = deck.slides[index]
            if action.action_type == "rewrite_tone" and action.tone:
                slide.title = f"{action.tone.title()}: {slide.title}"

        render_output = self.renderer.render(deck, template, artifact_root)
        validation_report = self.validator_engine.validate(deck, render_output.manifest)
        return GenerationArtifacts(
            deck=deck,
            outline=generated.outline,
            evidence_pack=generated.evidence_pack,
            manifest=render_output.manifest,
            validation_report=validation_report,
            editable_deck_state=render_output.editable_deck_state,
            semantic_findings=generated.semantic_findings,
            pptx_path=render_output.pptx_path,
        )
