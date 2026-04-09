from fastapi.testclient import TestClient

from chatppt.app.main import create_app
from chatppt.app.infra.llm_provider import FakeLLMProvider


def test_generate_endpoint_returns_artifact_metadata(tmp_path):
    app = create_app(
        artifact_root=tmp_path,
        template_root="tests/fixtures/templates/default",
        llm_provider=FakeLLMProvider(
            {
                "topic": "Q2 launch",
                "audience": "executives",
                "use_case": "board update",
                "desired_tone": "confident",
                "expected_duration_minutes": 8,
                "preferred_language": "en",
                "must_include": ["launch goals"],
                "must_avoid": [],
                "available_materials": [],
                "approval_mode": "manual_review",
                "missing_info": [],
            }
        ),
    )

    response = TestClient(app).post(
        "/api/v1/generate",
        json={"brief": "Create a board-ready Q2 launch deck", "documents": []},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["validation_report"]["passed"] is True
    assert payload["editable_deck_state"]["slides"][0]["slide_id"] == "slide-1"
