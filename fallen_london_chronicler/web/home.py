import os.path

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import HTMLResponse

from fallen_london_chronicler.config import config
from fallen_london_chronicler.db import engine, get_session
from fallen_london_chronicler.model import Base
from fallen_london_chronicler.web.templates import templated

router = APIRouter()

USERSCRIPT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../../resources", "userscript.js"
)


# noinspection PyUnusedLocal
@router.get("/", response_class=HTMLResponse)
@templated("home.html")
async def areas(request: Request):
    with open(USERSCRIPT_PATH) as f:
        userscript = f.read()
    return {
        "userscript": userscript
    }


@router.post("/reset",)
async def reset():
    for tbl in reversed(Base.metadata.sorted_tables):
        engine.execute(tbl.delete())
    return {
        "success": True
    }


@router.post("/export_html")
async def export_html():
    from fallen_london_chronicler.export.html import HTMLExporter
    with get_session() as session:
        exporter = HTMLExporter(
            export_dir=config.html_export_path,
            root_url=config.html_export_url
        )
        path = exporter.export_all(session)
    return {
        "success": True,
        "path": path
    }


@router.post("/export_google_docs")
async def export_google_docs():
    from fallen_london_chronicler.export.google_docs import GoogleDocsExporter
    with get_session() as session:
        exporter = GoogleDocsExporter(
            google_credentials_path=config.google_credentials_path,
            google_credentials_cache_path=config.google_credentials_cache_path,
            template_document_id=config.google_docs_template_id,
        )
        url = exporter.export_all(session)
    return {
        "success": True,
        "url": url,
    }
