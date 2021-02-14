import os
import os.path
import shutil

from sqlalchemy.orm import selectinload
from starlette.templating import Jinja2Templates

from area import render_area
from areas import render_areas
from branch import render_branch
from fallen_london_chronicler.db import Session
from fallen_london_chronicler.export.base import Exporter
from fallen_london_chronicler.model import Area, Storylet, Branch
from fallen_london_chronicler.web import STATIC_FILES_PATH, CACHED_IMAGES_PATH
from storylet import render_storylet
from templates import make_templates


class HTMLExporter(Exporter):
    def __init__(self, export_dir: str, root_url: str):
        self.export_dir = export_dir
        self.root_url = root_url

    def export_all(self, session: Session) -> str:
        templates = make_templates()
        templates.env.globals["root_url"] = self.root_url
        templates.env.globals["is_export"] = True

        areas = session.query(Area).options(
            selectinload(Area.storylets).selectinload(Storylet.branches)
        ).all()

        os.makedirs(self.export_dir, exist_ok=True)
        index_path = os.path.join(self.export_dir, "index.html")
        with open(index_path, "w") as f:
            areas_template = templates.get_template("areas.html")
            f.write(areas_template.render({**render_areas(areas)}))

        areas_dir = os.path.join(self.export_dir, "area")
        storylets_dir = os.path.join(self.export_dir, "storylet")
        branches_dir = os.path.join(self.export_dir, "branch")
        for area in areas:
            export_area(templates, areas_dir, area)
            for storylet in area.storylets:
                export_storylet(templates, storylets_dir, area, storylet)
                for branch in storylet.branches:
                    export_branch(templates, branches_dir, area, branch)

        static_dir = os.path.join(self.export_dir, "static")
        if os.path.exists(static_dir):
            shutil.rmtree(static_dir)
        shutil.copytree(STATIC_FILES_PATH, static_dir)

        images_dir = os.path.join(self.export_dir, "images")
        if os.path.exists(images_dir):
            shutil.rmtree(images_dir)
        shutil.copytree(CACHED_IMAGES_PATH, images_dir)

        return self.export_dir


def export_area(templates: Jinja2Templates, areas_dir: str, area: Area) -> None:
    area_template = templates.get_template("area.html")
    area_dir = os.path.join(areas_dir, str(area.id))
    os.makedirs(area_dir, exist_ok=True)
    area_path = os.path.join(area_dir, "index.html")
    with open(area_path, "w") as f:
        f.write(area_template.render(render_area(area)))


def export_storylet(
        templates: Jinja2Templates,
        storylets_dir: str,
        area: Area,
        storylet: Storylet,
) -> None:
    storylet_template = templates.get_template("storylet.html")
    area_storylet_dir = os.path.join(
        storylets_dir, str(area.id), str(storylet.id)
    )
    os.makedirs(area_storylet_dir, exist_ok=True)
    storylet_path = os.path.join(area_storylet_dir, "index.html")
    with open(storylet_path, "w") as f:
        f.write(storylet_template.render(render_storylet(area, storylet)))


def export_branch(
        templates: Jinja2Templates,
        branches_dir: str,
        area: Area,
        branch: Branch,
):
    branch_template = templates.get_template("branch.html")
    area_branch_dir = os.path.join(
        branches_dir, str(area.id), str(branch.id)
    )
    os.makedirs(area_branch_dir, exist_ok=True)
    branch_path = os.path.join(area_branch_dir, "index.html")
    with open(branch_path, "w") as f:
        f.write(branch_template.render(render_branch(area, branch)))
