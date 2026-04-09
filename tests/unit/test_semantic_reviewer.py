from chatppt.app.domain.models.deck_ir import DeckIR, SlideIR, SlideContentBlock
from chatppt.app.domain.models.evidence_pack import EvidencePack
from chatppt.app.domain.services.semantic_reviewer import SemanticReviewer


def test_semantic_reviewer_flags_unsupported_conclusion():
    deck = DeckIR(
        slides=[
            SlideIR(
                slide_id="slide-1",
                section_id="sec-1",
                purpose="summary",
                title="Conclusion",
                content_blocks=[
                    SlideContentBlock(
                        block_id="b1",
                        kind="callout",
                        text="We have already won the market.",
                        evidence_refs=[],
                    )
                ],
                visual_slots=[],
                allowed_edit_operations=["rewrite_tone"],
            )
        ]
    )

    findings = SemanticReviewer().review(deck, EvidencePack())

    assert findings[0].severity == "warning"
    assert findings[0].code == "unsupported_claim"
