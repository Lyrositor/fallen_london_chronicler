from re import Pattern, Match
from typing import Iterable, Optional


def match_any(patterns: Iterable[Pattern], text: str) -> Optional[Match]:
    for pattern in patterns:
        if match := pattern.match(text):
            return match
    return None
