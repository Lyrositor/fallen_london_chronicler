import logging
from collections import defaultdict
from copy import copy
from typing import List, Any, Dict

from fastapi import APIRouter
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from starlette.responses import HTMLResponse

from fallen_london_chronicler.db import get_session
from fallen_london_chronicler.model import Area, Storylet
from fallen_london_chronicler.web.templates import templated

router = APIRouter()


# noinspection PyUnusedLocal
@router.get("/{area_id}", response_class=HTMLResponse)
@templated("area.html")
async def area_view(request: Request, area_id: int):
    with get_session() as session:
        area = (
            session.query(Area).options(selectinload(Area.storylets))
            .get(area_id)
        )
        return render_area(area)


def render_area(area: Area) -> Dict[str, Any]:
    settings = {}
    if area:
        for setting in area.settings:
            settings[setting.id] = dict(
                name=setting.name,
                opportunities=[],
                storylets=[],
            )

        # Add the top-level storylets
        for storylet in build_storylet_order(area.storylets):
            found_valid_setting = False
            for setting in storylet.settings:
                if setting.id in settings:
                    settings[setting.id]["storylets"].append(storylet)
                    found_valid_setting = True
            if not found_valid_setting:
                logging.error(
                    f"Storylet {storylet.id} is not in any valid setting "
                    f"for this area"
                )

        # Add the opportunities
        for storylet in area.storylets:
            if not storylet.is_card:
                continue
            found_valid_setting = False
            for setting in storylet.settings:
                if setting.id in settings:
                    settings[setting.id]["opportunities"].append(storylet)
                    found_valid_setting = True
            if not found_valid_setting:
                logging.error(
                    f"Storylet {storylet.id} is not in any valid setting "
                    f"for this area"
                )
    return {
        "area": area,
        "settings": settings,
    }


def build_storylet_order(storylets: List[Storylet]) -> List[Storylet]:
    must_be_before = defaultdict(list)
    for storylet in storylets:
        for before_storylet in storylet.before:
            if before_storylet in storylets:
                must_be_before[before_storylet].append(storylet)
    ordered_storylets = copy(storylets)

    while True:
        ordered_storylets_before = copy(ordered_storylets)
        for storylet in storylets:
            idx = ordered_storylets.index(storylet)
            max_idx = idx
            for after_storylet in must_be_before[storylet]:
                max_idx = min(max_idx, ordered_storylets.index(after_storylet))
            if max_idx < idx:
                ordered_storylets.insert(max_idx, ordered_storylets.pop(idx))
        if ordered_storylets == ordered_storylets_before:
            break

    return [storylet for storylet in ordered_storylets if storylet.is_top_level]
