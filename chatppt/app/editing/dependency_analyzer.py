from __future__ import annotations

from chatppt.app.editing.edit_parser import EditAction


class DependencyAnalyzer:
    def impacted_slide_indices(self, action: EditAction, slide_count: int) -> list[int]:
        if action.slide_number is None:
            return list(range(slide_count))
        index = max(0, min(slide_count - 1, action.slide_number - 1))
        return [index]
