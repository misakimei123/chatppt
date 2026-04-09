from __future__ import annotations

from chatppt.app.domain.models.deck_ir import SlideIR
from chatppt.app.domain.models.render_manifest import LayoutSelection
from chatppt.app.rendering.template_loader import TemplateMeta


class LayoutMatcher:
    def match(self, slide: SlideIR, template: TemplateMeta) -> LayoutSelection:
        best_score = -1.0
        best_layout_name = template.layouts[0].layout_name
        for layout in template.layouts:
            score = 0.2
            if slide.purpose in layout.supported_purposes:
                score += 0.5
            slot_kinds = {slot.kind for slot in slide.visual_slots}
            if slot_kinds and slot_kinds.issubset(set(layout.slot_kinds)):
                score += 0.3
            elif not slot_kinds and not layout.slot_kinds:
                score += 0.2
            if score > best_score:
                best_score = score
                best_layout_name = layout.layout_name
        return LayoutSelection(layout_name=best_layout_name, confidence=min(best_score, 1.0))
