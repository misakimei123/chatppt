from pathlib import Path

from chatppt.app.domain.models.deck_ir import DeckIR, SlideIR, SlideContentBlock, VisualSlot
from chatppt.app.rendering.layout_matcher import LayoutMatcher
from chatppt.app.rendering.template_loader import TemplateLoader


def test_layout_matcher_prefers_data_layout_for_chart_slides():
    template = TemplateLoader().load(Path("tests/fixtures/templates/default"))
    deck = DeckIR(
        slides=[
            SlideIR(
                slide_id="slide-1",
                section_id="sec-1",
                purpose="data",
                title="Quarterly metrics",
                content_blocks=[SlideContentBlock(block_id="b1", kind="stat", text="Revenue +35%")],
                visual_slots=[VisualSlot(slot_id="v1", kind="chart", semantic_description="Revenue trend")],
                allowed_edit_operations=["rewrite_tone"],
            )
        ]
    )

    match = LayoutMatcher().match(deck.slides[0], template)

    assert match.layout_name == "data_chart"
    assert match.confidence > 0.5
