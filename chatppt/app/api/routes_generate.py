from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from chatppt.app.domain.services.evidence_builder import SourceDocument
from chatppt.app.orchestration.graph import GenerationOrchestrator


class GenerateRequest(BaseModel):
    brief: str
    documents: list[SourceDocument] = Field(default_factory=list)


def build_generate_router(get_orchestrator, get_generation_store, get_telemetry):
    router = APIRouter()

    @router.post("/generate")
    def generate_deck(
        request: GenerateRequest,
        orchestrator: GenerationOrchestrator = Depends(get_orchestrator),
        generation_store=Depends(get_generation_store),
        telemetry=Depends(get_telemetry),
    ):
        result = orchestrator.generate(request.brief, request.documents)
        generation_id = f"gen-{len(generation_store) + 1}"
        generation_store[generation_id] = result
        telemetry.increment("generation.success")
        return {"generation_id": generation_id, **result.model_dump(mode="json")}

    return router
