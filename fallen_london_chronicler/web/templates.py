import os.path
from contextvars import Context
from functools import wraps
from typing import Any, Callable

from jinja2 import contextfilter
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from fallen_london_chronicler.config import config

TEMPLATES_DIR = os.path.join("resources", "templates")


def templated(template_file: str):
    def templated_with_template(func: Callable):
        @wraps(func)
        async def new_func(
                request: Request, *args: Any, **kwargs: Any
        ) -> templates.TemplateResponse:
            context = await func(request, *args, **kwargs)
            return templates.TemplateResponse(
                template_file,
                {
                    "request": request,
                    **context
                }
            )
        return new_func
    return templated_with_template


@contextfilter
def format_url_filter(ctx: Context, value: str) -> str:
    return (
        ctx.get("root_url", "")
        + value
        + ("/index.html" if ctx.get("is_export") else "")
    )


@contextfilter
def format_image_url_filter(ctx: Context, value: str) -> str:
    return ctx.get("root_url", "") + "/images" + value


def make_templates() -> Jinja2Templates:
    jinja_templates = Jinja2Templates(directory=TEMPLATES_DIR)
    jinja_templates.env.filters["unknown"] = (
        lambda value: value if value is not None else "<em>(Unknown)</em>"
    )
    jinja_templates.env.filters["format_url"] = format_url_filter
    jinja_templates.env.filters["format_image_url"] = format_image_url_filter
    jinja_templates.env.globals["root_url"] = config.root_url
    return jinja_templates


templates = make_templates()
