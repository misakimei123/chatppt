from __future__ import annotations

from pydantic import BaseModel, Field


class SlideContentBlock(BaseModel):
    block_id: str
    kind: str
    text: str
    evidence_refs: list[str] = Field(default_factory=list)


class VisualSlot(BaseModel):
    slot_id: str
    kind: str
    semantic_description: str


class SlideIR(BaseModel):
    slide_id: str
    section_id: str
    purpose: str
    title: str
    content_blocks: list[SlideContentBlock] = Field(default_factory=list)
    visual_slots: list[VisualSlot] = Field(default_factory=list)
    allowed_edit_operations: list[str] = Field(default_factory=list)


class DeckIR(BaseModel):
    slides: list[SlideIR] = Field(default_factory=list)
