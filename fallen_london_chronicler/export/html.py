import os
import os.path
import shutil
from typing import Any

from sqlalchemy.orm import selectinload

from area import render_area
from areas import render_areas
from branch import render_branch
from fallen_london_chronicler.db import Session
from fallen_london_chronicler.export.base import Exporter
from fallen_london_chronicler.model import Area, Storylet, Branch
from fallen_london_chronicler.web import STATIC_FILES_PATH
from storylet import render_storylet
from templates import templates


class HTMLExporter(Exporter):
    def __init__(self, export_dir: str, root_url: str):
        self.export_dir = export_dir
        self.root_url = root_url

    def export_all(self, session: Session) -> str:
        areas = session.query(Area).options(
            selectinload(Area.storylets).selectinload(Storylet.branches)
        ).all()

        context = {"root_url": self.root_url, "is_export": True}

        os.makedirs(self.export_dir, exist_ok=True)
        index_path = os.path.join(self.export_dir, "index.html")
        with open(index_path, "w") as f:
            areas_template = templates.get_template("areas.html")
            f.write(areas_template.render({**render_areas(areas), **context}))

        areas_dir = os.path.join(self.export_dir, "area")
        storylets_dir = os.path.join(self.export_dir, "storylet")
        branches_dir = os.path.join(self.export_dir, "branch")
        for area in areas:
            export_area(areas_dir, area, **context)
            for storylet in area.storylets:
                export_storylet(storylets_dir, area, storylet, **context)
                for branch in storylet.branches:
                    export_branch(branches_dir, area, branch, **context)

        static_dir = os.path.join(self.export_dir, "static")
        if os.path.exists(static_dir):
            shutil.rmtree(static_dir)
        shutil.copytree(STATIC_FILES_PATH, static_dir)

        return self.export_dir


def export_area(areas_dir: str, area: Area, **context: Any) -> None:
    area_template = templates.get_template("area.html")
    area_dir = os.path.join(areas_dir, str(area.id))
    os.makedirs(area_dir, exist_ok=True)
    area_path = os.path.join(area_dir, "index.html")
    with open(area_path, "w") as f:
        f.write(area_template.render({**render_area(area), **context}))


def export_storylet(
        storylets_dir: str, area: Area, storylet: Storylet, **context: Any
) -> None:
    storylet_template = templates.get_template("storylet.html")
    area_storylet_dir = os.path.join(
        storylets_dir, str(area.id), str(storylet.id)
    )
    os.makedirs(area_storylet_dir, exist_ok=True)
    storylet_path = os.path.join(area_storylet_dir, "index.html")
    with open(storylet_path, "w") as f:
        f.write(
            storylet_template.render(
                {**render_storylet(area, storylet), **context}
            )
        )


def export_branch(
        branches_dir: str, area: Area, branch: Branch, **context: Any
):
    branch_template = templates.get_template("branch.html")
    area_branch_dir = os.path.join(
        branches_dir, str(area.id), str(branch.id)
    )
    os.makedirs(area_branch_dir, exist_ok=True)
    branch_path = os.path.join(area_branch_dir, "index.html")
    with open(branch_path, "w") as f:
        f.write(
            branch_template.render(
                {**render_branch(area, branch), **context}
            )
        )
