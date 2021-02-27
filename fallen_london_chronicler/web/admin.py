from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import HTMLResponse

from fallen_london_chronicler.auth import authorize
from fallen_london_chronicler.db import get_session
from fallen_london_chronicler.model import User
from fallen_london_chronicler.web.templates import templated

router = APIRouter()


# noinspection PyUnusedLocal
@router.get("/", response_class=HTMLResponse)
@templated("admin.html")
async def area_view(request: Request, api_key: str = ""):
    with get_session() as session:
        require_admin(session, api_key)
        return render_admin(session)


@router.post("/", response_class=HTMLResponse)
@templated("admin.html")
async def area_view(request: Request, api_key: str):
    with get_session() as session:
        require_admin(session, api_key)

        form = await request.form()
        if "save_user" in form:
            save_user = form["save_user"]
            is_admin = bool(form.get("is_admin"))
            if save_user:
                user: User = session.query(User).get(int(save_user))
                user.is_admin = is_admin
            else:
                user = User.create(
                    session, name=form["name"].strip(), is_admin=is_admin
                )
            user.is_active = bool(form.get("is_active"))

        return render_admin(session)


def render_admin(session: Session) -> Dict[str, Any]:
    return {
        "users": session.query(User).all()
    }


def require_admin(session: Session, api_key: str) -> None:
    user = authorize(session, api_key)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
