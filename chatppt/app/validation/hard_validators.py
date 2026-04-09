from __future__ import annotations

from chatppt.app.domain.models.deck_ir import DeckIR
from chatppt.app.domain.models.render_manifest import RenderManifest
from chatppt.app.orchestration.state import ValidationIssue, ValidationReport


class HardValidatorEngine:
    def validate(self, deck: DeckIR, manifest: RenderManifest) -> ValidationReport:
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []
        manifest_by_slide = {item.slide_id: item for item in manifest.slides}

        for slide in deck.slides:
            rendered = manifest_by_slide.get(slide.slide_id)
            content_dimensions = (rendered.placeholder_dimensions.get("content", {}) if rendered else {})
            width = content_dimensions.get("width", 8.0)
            height = content_dimensions.get("height", 3.0)
            capacity = max(int(width * height * 14), 40)
            total_chars = sum(len(block.text) for block in slide.content_blocks)
            if total_chars > capacity:
                errors.append(
                    ValidationIssue(
                        code="text_overflow",
                        message=f"Slide content length {total_chars} exceeds estimated capacity {capacity}.",
                        slide_id=slide.slide_id,
                    )
                )
            if slide.purpose == "data" and not slide.visual_slots:
                warnings.append(
                    ValidationIssue(
                        code="missing_visual",
                        message="Data slide has no visual slot; chart should be added for readability.",
                        slide_id=slide.slide_id,
                        severity="warning",
                    )
                )
        return ValidationReport(passed=not errors, errors=errors, warnings=warnings)
