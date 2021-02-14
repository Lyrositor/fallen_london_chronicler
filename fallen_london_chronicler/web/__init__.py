import os.path

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from . import area
from . import areas
from . import branch
from . import home
from . import storylet

STATIC_FILES_PATH = os.path.join("resources", "static")
CACHED_IMAGES_PATH = os.path.join("resources", "images")


def setup_web(api: FastAPI, serve_cached_images: bool) -> None:
    api.mount(
        "/static", StaticFiles(directory=STATIC_FILES_PATH), name="static"
    )
    if serve_cached_images:
        api.mount(
            "/images",
            StaticFiles(directory=CACHED_IMAGES_PATH),
            name="images"
        )
    api.include_router(home.router, prefix="")
    api.include_router(areas.router, prefix="/areas")
    api.include_router(area.router, prefix="/area")
    api.include_router(branch.router, prefix="/branch")
    api.include_router(storylet.router, prefix="/storylet")
