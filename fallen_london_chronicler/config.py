from typing import Optional

from pydantic import BaseSettings


class AppConfig(BaseSettings):
    app_version: str = "1.0.0"
    app_port: int = 7777
    debug: bool = False
    db_url: str = "sqlite:///./fallen_london.db"
    root_url: str = f"http://localhost:{app_port}"

    html_export_path: str = "export/html"
    html_export_url: str = ""

    google_credentials_path: str = "credentials.json"
    google_credentials_cache_path: str = "credentials.cache"
    google_docs_template_id: Optional[str] = \
        "1HFak7enwGuiuOiHkX-3lnf-_pgUC7zj0kIZShqhvEUM"

    class Config:
        case_sensitive = False
        env_file = "config.env"


def load_config() -> AppConfig:
    return AppConfig()


config = load_config()
