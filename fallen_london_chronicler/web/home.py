import os.path
import urllib.parse

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response

from fallen_london_chronicler.config import config
from fallen_london_chronicler.db import engine, get_session
from fallen_london_chronicler.model import Base
from fallen_london_chronicler.web.templates import templated

router = APIRouter()

USERSCRIPT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../../resources", "userscript.js"
)


class JavaScriptResponse(Response):
    media_type = "text/javascript"


# noinspection PyUnusedLocal
@router.get("/", response_class=HTMLResponse)
@templated("home.html")
async def home(request: Request):
    return {
        "reset_data_enable": config.reset_data_enable,
        "html_export_enable": config.html_export_enable,
        "google_docs_export_enable": config.google_docs_export_enable,
    }


@router.get("/userscript.js", response_class=HTMLResponse)
async def userscript(api_key: str = ""):
    with open(USERSCRIPT_PATH) as f:
        script = f.read()
    params = urllib.parse.urlencode({"api_key": api_key})
    script = script.replace("{{api_key}}", str(api_key))
    script = script.replace(
        "{{download_url}}", f"{config.root_url}/userscript.js?{params}"
    )
    script = script.replace("{{submit_url}}", config.root_url + "/api/submit")
    return JavaScriptResponse(script)


@router.post("/reset",)
async def reset():
    if not config.reset_data_enable:
        return {
            "success": False
        }
    for tbl in reversed(Base.metadata.sorted_tables):
        engine.execute(tbl.delete())
    return {
        "success": True
    }


@router.post("/export_html")
async def export_html():
    from fallen_london_chronicler.export.html import HTMLExporter

    if not config.html_export_enable:
        return {
            "success": False
        }

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

    if not config.google_docs_export_enable:
        return {
            "success": False
        }

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
