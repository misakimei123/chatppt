from __future__ import annotations

from pydantic import BaseModel, Field


class EditableSlideState(BaseModel):
    slide_id: str
    layout_name: str
    allowed_edit_operations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    external_edit_detected: bool = False


class EditableDeckState(BaseModel):
    slides: list[EditableSlideState] = Field(default_factory=list)
