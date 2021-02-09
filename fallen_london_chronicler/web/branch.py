from typing import Any, Dict

from fastapi import APIRouter
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from starlette.responses import HTMLResponse

from fallen_london_chronicler.db import get_session
from fallen_london_chronicler.model import Area, Branch, OutcomeObservation
from fallen_london_chronicler.web.templates import templated

router = APIRouter()


# noinspection PyUnusedLocal
@router.get("/{area_id}/{branch_id}", response_class=HTMLResponse)
@templated("branch.html")
async def branch_view(request: Request, area_id: int, branch_id: int):
    with get_session() as session:
        area = session.query(Area).get(area_id)
        branch = (
            session.query(Branch).options(
                selectinload(Branch.storylet),
                selectinload(Branch.outcome_observations)
                .selectinload(OutcomeObservation.redirect_branch)
            )
            .get(branch_id)
        )
        return render_branch(area, branch)


def render_branch(area: Area, branch: Branch) -> Dict[str, Any]:
    return {
        "area": area,
        "branch": branch
    }
