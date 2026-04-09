from __future__ import annotations

from pydantic import BaseModel

from chatppt.app.domain.models.clarified_spec import ClarifiedSpec
from chatppt.app.domain.models.evidence_pack import (
    EvidenceFact,
    EvidencePack,
    EvidenceSource,
    EvidenceSuggestion,
)


class SourceDocument(BaseModel):
    title: str
    uri: str
    content: str
    source_type: str = "user_upload"


class EvidenceBuilder:
    def build(self, spec: ClarifiedSpec, documents: list[SourceDocument] | None = None) -> EvidencePack:
        documents = documents or []
        facts: list[EvidenceFact] = []
        suggestions: list[EvidenceSuggestion] = []
        for doc_index, document in enumerate(documents, start=1):
            source = EvidenceSource(
                source_type=document.source_type,
                title=document.title,
                uri=document.uri,
                reliability=0.9 if document.source_type == "user_upload" else 0.75,
            )
            for line in [line.strip() for line in document.content.splitlines() if line.strip()]:
                if line.startswith("FACT:"):
                    claim = line.removeprefix("FACT:").strip()
                    facts.append(EvidenceFact(fact_id=f"fact-{len(facts) + 1}", claim=claim, source=source))
                elif line.startswith("SUGGESTION:"):
                    suggestion = line.removeprefix("SUGGESTION:").strip()
                    suggestions.append(
                        EvidenceSuggestion(
                            suggestion_id=f"suggestion-{len(suggestions) + 1}",
                            text=suggestion,
                            rationale=f"Derived from source {doc_index}: {document.title}",
                        )
                    )
        if not documents:
            for item in spec.must_include:
                suggestions.append(
                    EvidenceSuggestion(
                        suggestion_id=f"suggestion-{len(suggestions) + 1}",
                        text=f"Include a slide about {item}.",
                        rationale="Derived from explicit user requirement.",
                    )
                )
        constraints = [f"Avoid: {item}" for item in spec.must_avoid] + [
            f"Must include: {item}" for item in spec.must_include
        ]
        return EvidencePack(facts=facts, suggestions=suggestions, constraints=constraints)
