from __future__ import annotations

from chatppt.app.domain.models.clarified_spec import ClarifiedSpec, ClarifierOutput
from chatppt.app.infra.llm_provider import LLMProvider


FOLLOW_UP_QUESTION_MAP = {
    "audience": "Who is the intended audience for this presentation?",
    "use_case": "What is the primary use case for this deck?",
    "desired_tone": "What tone should the presentation use?",
    "expected_duration_minutes": "How long should this presentation be?",
}


class Clarifier:
    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def clarify(self, brief: str) -> ClarifierOutput:
        payload = self.provider.generate_structured(
            task_name="clarify",
            prompt=brief,
            schema_name="ClarifiedSpec",
        )
        missing_info = payload.get("missing_info", [])
        spec = ClarifiedSpec.model_validate(
            {
                "topic": payload.get("topic", ""),
                "audience": payload.get("audience", ""),
                "use_case": payload.get("use_case", ""),
                "desired_tone": payload.get("desired_tone", "neutral"),
                "expected_duration_minutes": payload.get("expected_duration_minutes", 8),
                "preferred_language": payload.get("preferred_language", "en"),
                "must_include": payload.get("must_include", []),
                "must_avoid": payload.get("must_avoid", []),
                "available_materials": payload.get("available_materials", []),
                "approval_mode": payload.get("approval_mode", "manual_review"),
            }
        )
        follow_up_questions = [FOLLOW_UP_QUESTION_MAP[item] for item in missing_info if item in FOLLOW_UP_QUESTION_MAP]
        return ClarifierOutput(
            clarified_spec=spec,
            missing_info=missing_info,
            follow_up_questions=follow_up_questions,
        )
