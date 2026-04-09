from pydantic import ValidationError

from chatppt.app.domain.models.evidence_pack import EvidenceFact, EvidencePack, EvidenceSource


def test_evidence_fact_requires_source():
    try:
        EvidenceFact(claim="Revenue grew 30%")
    except ValidationError as exc:
        assert "source" in str(exc)
    else:
        raise AssertionError("EvidenceFact should require a source")


def test_evidence_pack_serializes_fact_and_constraints():
    pack = EvidencePack(
        facts=[
            EvidenceFact(
                claim="Revenue grew 30%",
                source=EvidenceSource(
                    source_type="user_upload",
                    title="Q4 board report",
                    uri="file://board-report.md",
                    reliability=0.9,
                ),
            )
        ],
        constraints=["Use concise language"],
    )

    dumped = pack.model_dump()
    assert dumped["facts"][0]["claim"] == "Revenue grew 30%"
    assert dumped["constraints"] == ["Use concise language"]
