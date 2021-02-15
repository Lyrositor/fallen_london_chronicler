import random
import string
from argparse import ArgumentParser
from typing import Optional

import uvicorn

from fallen_london_chronicler.config import config
from fallen_london_chronicler.log import LOGGING_CONFIG
from fallen_london_chronicler.model.api_key import APIKey


def create_api_key(user_name: str) -> str:
    from fallen_london_chronicler.app import setup_db
    setup_db()
    from fallen_london_chronicler.db import get_session
    with get_session() as session:
        api_key = APIKey(user_name=user_name)
        while True:
            key = "".join(
                random.choices(string.ascii_letters + string.digits, k=32)
            )
            if not session.query(APIKey).get(key):
                break
        api_key.key = key
        session.add(api_key)
    return key


def main(add_api_key: Optional[str] = None) -> None:
    if add_api_key:
        key = create_api_key(add_api_key)
        print(f"API key created for {add_api_key}: {key}")
        return

    uvicorn.run(
        "fallen_london_chronicler.app:app",
        host="0.0.0.0",
        port=config.app_port,
        debug=config.debug,
        log_config=LOGGING_CONFIG,
    )


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        "--add_api_key",
        default=None,
        help="Adds a new API key instead of starting the server."
    )
    args = parser.parse_args()
    main(args.add_api_key)
