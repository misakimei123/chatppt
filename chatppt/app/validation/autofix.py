from __future__ import annotations

from chatppt.app.domain.models.deck_ir import DeckIR


class AutoFixEngine:
    def apply(self, deck: DeckIR) -> DeckIR:
        for slide in deck.slides:
            for block in slide.content_blocks:
                if len(block.text) > 240:
                    block.text = f"{block.text[:237]}..."
        return deck
