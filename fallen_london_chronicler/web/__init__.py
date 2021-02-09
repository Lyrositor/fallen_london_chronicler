import os.path

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from . import area
from . import areas
from . import branch
from . import home
from . import storylet

STATIC_FILES_PATH = os.path.join("resources", "static")


def setup_web(api: FastAPI) -> None:
    api.mount(
        "/static", StaticFiles(directory=STATIC_FILES_PATH), name="static"
    )
    api.include_router(home.router, prefix="")
    api.include_router(areas.router, prefix="/areas")
    api.include_router(area.router, prefix="/area")
    api.include_router(branch.router, prefix="/branch")
    api.include_router(storylet.router, prefix="/storylet")
