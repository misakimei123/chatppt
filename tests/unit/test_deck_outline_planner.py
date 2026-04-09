from chatppt.app.domain.models.clarified_spec import ClarifiedSpec
from chatppt.app.domain.models.evidence_pack import EvidenceFact, EvidencePack, EvidenceSource
from chatppt.app.domain.services.deck_outline_planner import DeckOutlinePlanner


def test_outline_planner_builds_storyline_and_respects_duration():
    spec = ClarifiedSpec(
        topic="Growth review",
        audience="board",
        use_case="board update",
        desired_tone="confident",
        expected_duration_minutes=6,
        preferred_language="en",
        must_include=["key metrics"],
        must_avoid=[],
        available_materials=[],
        approval_mode="manual_review",
    )
    pack = EvidencePack(
        facts=[
            EvidenceFact(
                claim="Pipeline grew 42%",
                source=EvidenceSource(
                    source_type="user_upload",
                    title="Revops sheet",
                    uri="file://revops.csv",
                    reliability=0.9,
                ),
            )
        ]
    )

    outline = DeckOutlinePlanner().plan(spec, pack)

    assert outline.deck_objective == "Growth review"
    assert outline.estimated_slide_count <= 8
    assert outline.sections[0].purpose == "title"
