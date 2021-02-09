import webbrowser

from fastapi import FastAPI

from fallen_london_chronicler.api import submit
from fallen_london_chronicler.config import config
from fallen_london_chronicler.db import engine
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
    setup_api(api)
    setup_web(api)
    setup_db()
    return api


app = create_app()


@app.on_event("startup")
def on_startup():
    if not config.debug:
        webbrowser.open(config.root_url, 2)