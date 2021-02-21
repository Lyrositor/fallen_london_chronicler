from typing import Optional

from pydantic import BaseSettings


class AppConfig(BaseSettings):
    app_version: str = "1.1.0"
    app_port: int = 7777
    debug: bool = False
    db_url: str = "sqlite:///./fallen_london.db"
    root_url: str = f"http://localhost:{app_port}"
    serve_cached_images: bool = True
    reset_data_enable: bool = True
    require_api_key: bool = False
    session_secret: str = "please_change_me"

    html_export_enable: bool = True
    html_export_path: str = "export/html"
    html_export_url: str = ""

    google_docs_export_enable: bool = True
    google_credentials_path: str = "credentials.json"
    google_credentials_cache_path: str = "credentials.cache"
    google_docs_template_id: Optional[str] = \
        "1HFak7enwGuiuOiHkX-3lnf-_pgUC7zj0kIZShqhvEUM"

    sentry_dsn: Optional[str] = None

    class Config:
        case_sensitive = False
        env_file = "config.env"


def load_config() -> AppConfig:
    return AppConfig()


config = load_config()
