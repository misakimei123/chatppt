from __future__ import annotations

import re

from pydantic import BaseModel


class EditAction(BaseModel):
    action_type: str
    slide_number: int | None = None
    tone: str | None = None
    raw_instruction: str


class EditParser:
    def parse(self, instruction: str) -> EditAction:
        lowered = instruction.lower()
        slide_match = re.search(r"slide\s+(\d+)", lowered)
        slide_number = int(slide_match.group(1)) if slide_match else None
        if "conservative" in lowered:
            return EditAction(
                action_type="rewrite_tone",
                slide_number=slide_number,
                tone="conservative",
                raw_instruction=instruction,
            )
        if "aggressive" in lowered:
            return EditAction(
                action_type="rewrite_tone",
                slide_number=slide_number,
                tone="aggressive",
                raw_instruction=instruction,
            )
        return EditAction(action_type="unsupported", slide_number=slide_number, raw_instruction=instruction)
