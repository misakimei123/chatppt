from chatppt.app.domain.models.clarified_spec import ClarifiedSpec
from chatppt.app.domain.models.deck_outline import DeckOutline, DeckSection
from chatppt.app.domain.models.evidence_pack import EvidenceFact, EvidencePack, EvidenceSource
from chatppt.app.domain.services.slide_planner import SlidePlanner


def test_slide_planner_attaches_evidence_and_allowed_edit_actions():
    spec = ClarifiedSpec(
        topic="Market expansion",
        audience="leadership",
        use_case="strategy review",
        desired_tone="neutral",
        expected_duration_minutes=8,
        preferred_language="en",
        must_include=[],
        must_avoid=[],
        available_materials=[],
        approval_mode="manual_review",
    )
    outline = DeckOutline(
        deck_objective="Market expansion",
        narrative_arc="problem-solution-impact",
        estimated_slide_count=3,
        sections=[
            DeckSection(section_id="sec-1", title="Context", purpose="title", evidence_refs=[]),
            DeckSection(section_id="sec-2", title="Opportunity", purpose="data", evidence_refs=["fact-1"]),
        ],
    )
    pack = EvidencePack(
        facts=[
            EvidenceFact(
                fact_id="fact-1",
                claim="SEA pipeline grew 55%",
                source=EvidenceSource(
                    source_type="user_upload",
                    title="Expansion memo",
                    uri="file://expansion.md",
                    reliability=0.92,
                ),
            )
        ]
    )

    deck = SlidePlanner().plan(spec, outline, pack)

    assert len(deck.slides) == 2
    assert deck.slides[1].content_blocks[0].evidence_refs == ["fact-1"]
    assert "rewrite_tone" in deck.slides[1].allowed_edit_operations
