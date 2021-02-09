from typing import Any, Dict

from fastapi import APIRouter
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from starlette.responses import HTMLResponse

from fallen_london_chronicler.db import get_session
from fallen_london_chronicler.model import Storylet, Branch, Area
from fallen_london_chronicler.web.templates import templated

router = APIRouter()


# noinspection PyUnusedLocal
@router.get("/{area_id}/{storylet_id}", response_class=HTMLResponse)
@templated("storylet.html")
async def storylet_view(request: Request, area_id: int, storylet_id: int):
    with get_session() as session:
        area = session.query(Area).get(area_id)
        storylet = session.query(Storylet)\
            .options(
            selectinload(Storylet.areas),
            selectinload(Storylet.branches).selectinload(Branch.observations)
        ).get(storylet_id)
        return {
            "area": area,
            "storylet": storylet
        }


def render_storylet(area: Area, storylet: Storylet) -> Dict[str, Any]:
    return {
        "area": area,
        "storylet": storylet
    }
