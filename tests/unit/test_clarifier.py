from chatppt.app.domain.services.clarifier import Clarifier
from chatppt.app.infra.llm_provider import FakeLLMProvider


def test_clarifier_extracts_structured_spec_from_brief():
    provider = FakeLLMProvider(
        {
            "topic": "Q2 product launch",
            "audience": "executives",
            "use_case": "board update",
            "desired_tone": "confident",
            "expected_duration_minutes": 10,
            "preferred_language": "en",
            "must_include": ["launch goals"],
            "must_avoid": ["engineering jargon"],
            "available_materials": ["launch-notes.md"],
            "approval_mode": "manual_review",
            "missing_info": [],
        }
    )

    result = Clarifier(provider).clarify("Create a board-ready Q2 product launch presentation")

    assert result.clarified_spec.topic == "Q2 product launch"
    assert result.missing_info == []


def test_clarifier_returns_follow_up_questions_when_info_missing():
    provider = FakeLLMProvider(
        {
            "topic": "Hiring update",
            "audience": "",
            "use_case": "status update",
            "desired_tone": "neutral",
            "expected_duration_minutes": 5,
            "preferred_language": "zh",
            "must_include": [],
            "must_avoid": [],
            "available_materials": [],
            "approval_mode": "manual_review",
            "missing_info": ["audience"],
        }
    )

    result = Clarifier(provider).clarify("做一份招聘进展汇报")

    assert result.missing_info == ["audience"]
    assert result.follow_up_questions == ["Who is the intended audience for this presentation?"]
