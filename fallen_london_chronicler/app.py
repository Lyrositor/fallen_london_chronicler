import webbrowser

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from fallen_london_chronicler.api import submit
from fallen_london_chronicler.config import config
from fallen_london_chronicler.db import engine
from fallen_london_chronicler.images import get_or_cache_image, ImageType
from fallen_london_chronicler.web import setup_web

APP_TITLE = "Fallen London Chronicler"


def setup_api(api: FastAPI) -> None:
    api.include_router(submit.router, prefix="/api/submit", tags=["submit"])


def setup_db():
    from fallen_london_chronicler import model
    model.Base.metadata.create_all(engine)


def create_app() -> FastAPI:
    api = FastAPI(
        title=APP_TITLE, version=config.app_version, debug=config.debug
    )
    api.add_middleware(SessionMiddleware, secret_key=config.session_secret)
    setup_api(api)
    setup_web(api, config.serve_cached_images)
    setup_db()
    return api


app = create_app()


@app.on_event("startup")
def on_startup():
    get_or_cache_image(ImageType.ICON_SMALL, "question")
    if not config.debug:
        webbrowser.open(config.root_url, 2)
