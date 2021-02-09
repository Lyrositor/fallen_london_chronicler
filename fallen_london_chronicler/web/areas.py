from typing import List, Any, Dict

from fastapi import APIRouter
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from starlette.responses import HTMLResponse

from fallen_london_chronicler.db import get_session
from fallen_london_chronicler.model import Area
from fallen_london_chronicler.web.templates import templated

router = APIRouter()


# noinspection PyUnusedLocal
@router.get("/", response_class=HTMLResponse)
@templated("areas.html")
async def areas_view(request: Request):
    with get_session() as session:
        areas = session.query(Area).options(selectinload(Area.storylets)).all()
        return {
            "areas": areas
        }


def render_areas(areas: List[Area]) -> Dict[str, Any]:
    return {
        "areas": areas
    }
