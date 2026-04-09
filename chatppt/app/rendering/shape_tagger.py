from __future__ import annotations


class ShapeTagger:
    def tag(self, shape, stable_id: str) -> None:
        try:
            shape.name = stable_id
        except AttributeError:
            # Fallback for shapes that do not expose a writable name property.
            pass
