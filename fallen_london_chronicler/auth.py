from typing import Optional

from fallen_london_chronicler.config import config
from fallen_london_chronicler.db import Session
from fallen_london_chronicler.model import User


def authorize(session: Session, api_key: str) -> Optional[User]:
    if config.require_api_key and not api_key:
        return None
    return User.get_by_api_key(session, api_key)
