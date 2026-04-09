from __future__ import annotations

from fastapi import APIRouter, Depends


def build_template_router(get_template):
    router = APIRouter()

    @router.get("/templates")
    def list_templates(template=Depends(get_template)):
        return {
            "templates": [
                {
                    "template_id": template.template_id,
                    "display_name": template.display_name,
                    "layouts": [layout.layout_name for layout in template.layouts],
                }
            ]
        }

    return router
