from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ClarifiedSpec(BaseModel):
    topic: str
    audience: str
    use_case: str
    desired_tone: str
    expected_duration_minutes: int = Field(ge=1, le=60)
    preferred_language: str = "en"
    must_include: list[str] = Field(default_factory=list)
    must_avoid: list[str] = Field(default_factory=list)
    available_materials: list[str] = Field(default_factory=list)
    approval_mode: Literal["auto", "manual_review"] = "manual_review"


class ClarifierOutput(BaseModel):
    clarified_spec: ClarifiedSpec
    missing_info: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
