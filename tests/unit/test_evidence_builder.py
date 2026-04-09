from chatppt.app.domain.models.clarified_spec import ClarifiedSpec
from chatppt.app.domain.services.evidence_builder import EvidenceBuilder, SourceDocument


def test_evidence_builder_separates_supported_facts_from_suggestions():
    spec = ClarifiedSpec(
        topic="Fundraising update",
        audience="investors",
        use_case="pitch",
        desired_tone="confident",
        expected_duration_minutes=8,
        preferred_language="en",
        must_include=[],
        must_avoid=[],
        available_materials=[],
        approval_mode="manual_review",
    )
    documents = [
        SourceDocument(
            title="Metrics memo",
            uri="file://metrics.md",
            content=(
                "FACT: ARR reached $2.4M in March.\n"
                "FACT: Net revenue retention is 118%.\n"
                "SUGGESTION: Emphasize durable expansion revenue."
            ),
            source_type="user_upload",
        )
    ]

    pack = EvidenceBuilder().build(spec, documents)

    assert [fact.claim for fact in pack.facts] == [
        "ARR reached $2.4M in March.",
        "Net revenue retention is 118%.",
    ]
    assert [suggestion.text for suggestion in pack.suggestions] == [
        "Emphasize durable expansion revenue."
    ]
