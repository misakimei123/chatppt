from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from chatppt.app.editing.page_regenerator import PageRegenerator


class EditRequest(BaseModel):
    instruction: str


def build_edit_router(get_edit_service, get_generation_store, get_template):
    router = APIRouter()

    @router.post("/edit/{generation_id}")
    def edit_deck(
        generation_id: str,
        request: EditRequest,
        edit_service: PageRegenerator = Depends(get_edit_service),
        generation_store=Depends(get_generation_store),
        template=Depends(get_template),
    ):
        generated = generation_store[generation_id]
        updated = edit_service.apply_edit(generated, request.instruction, template, template.root_path.parent.parent / "artifacts")
        generation_store[generation_id] = updated
        return updated.model_dump(mode="json")

    return router
