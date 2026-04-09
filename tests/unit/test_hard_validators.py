from chatppt.app.domain.models.deck_ir import DeckIR, SlideIR, SlideContentBlock
from chatppt.app.domain.models.render_manifest import LayoutSelection, RenderManifest, RenderedSlide
from chatppt.app.validation.hard_validators import HardValidatorEngine


def test_hard_validators_flag_overflow_using_placeholder_dimensions():
    deck = DeckIR(
        slides=[
            SlideIR(
                slide_id="slide-1",
                section_id="sec-1",
                purpose="summary",
                title="Summary",
                content_blocks=[
                    SlideContentBlock(
                        block_id="b1",
                        kind="bullet",
                        text="A very long paragraph " * 20,
                    )
                ],
                visual_slots=[],
                allowed_edit_operations=["rewrite_tone"],
            )
        ]
    )
    manifest = RenderManifest(
        slides=[
            RenderedSlide(
                slide_id="slide-1",
                layout=LayoutSelection(layout_name="title_content", confidence=0.8),
                placeholder_map={"content": "b1"},
                placeholder_dimensions={"content": {"width": 4.0, "height": 1.0}},
                warnings=[],
            )
        ]
    )

    report = HardValidatorEngine().validate(deck, manifest)

    assert report.passed is False
    assert any(issue.code == "text_overflow" for issue in report.errors)
