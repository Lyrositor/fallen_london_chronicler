import logging
import webbrowser

from fastapi import FastAPI
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.middleware.sessions import SessionMiddleware

from fallen_london_chronicler.api import submit
from fallen_london_chronicler.config import config
from fallen_london_chronicler.db import engine, get_session
from fallen_london_chronicler.images import get_or_cache_image, ImageType
from fallen_london_chronicler.model import User
from fallen_london_chronicler.web import setup_web

APP_TITLE = "Fallen London Chronicler"


def setup_api(api: FastAPI) -> None:
    api.include_router(submit.router, prefix="/api/submit", tags=["submit"])


def setup_db():
    from fallen_london_chronicler import model
    model.Base.metadata.create_all(engine)
    # Create a default admin user in case one doesn't exist
    # The user will not be usable unless config.require_api_key is false
    with get_session() as session:
        if not config.require_api_key and not User.get_by_api_key(session, ""):
            user = User.create(session, "Administrator", True)
            user.api_key = ""
            logging.info(
                "Created default administrator user with empty API key"
            )


def setup_monitoring(api: FastAPI) -> None:
    if config.sentry_dsn:
        try:
            import sentry_sdk
            sentry_sdk.init(config.sentry_dsn)
            api.add_middleware(SentryAsgiMiddleware)
        except ModuleNotFoundError:
            logging.warning(
                "Sentry integration not found, error reporting is disabled"
            )


def patch_fastapi() -> None:
    """
    Fixes a bug in FastAPI's error handling.
    """
    import html
    import inspect
    import traceback
    from starlette.middleware.errors import JS, ServerErrorMiddleware, STYLES, \
        TEMPLATE

    def generate_html(self, exc: Exception, limit: int = 7) -> str:
        traceback_obj = traceback.TracebackException.from_exception(
            exc, capture_locals=True
        )
        frames = inspect.getinnerframes(
            exc.__traceback__, limit  # type: ignore
        )

        exc_html = ""
        is_collapsed = False
        for frame in reversed(frames):
            exc_html += self.generate_frame_html(frame, is_collapsed)
            is_collapsed = True

        # escape error class and text
        error = (
            f"{html.escape(traceback_obj.exc_type.__name__)}: "
            f"{html.escape(str(traceback_obj))}")

        return TEMPLATE.format(styles=STYLES, js=JS, error=error,
                               exc_html=exc_html)

    ServerErrorMiddleware.generate_html = generate_html


def create_app() -> FastAPI:
    patch_fastapi()
    api = FastAPI(
        title=APP_TITLE, version=config.app_version, debug=config.debug
    )
    setup_monitoring(api)
    api.add_middleware(SessionMiddleware, secret_key=config.session_secret)
    setup_api(api)
    setup_web(api, config.serve_cached_images)
    setup_db()
    return api


app = create_app()


@app.on_event("startup")
def on_startup():
    get_or_cache_image(ImageType.ICON, "question")
    if not config.debug:
        webbrowser.open(config.root_url, 2)
