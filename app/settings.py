from functools import lru_cache

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    app_id_prod: str | None = None

    url_prod: str | None = None

    telegram_bot_token: str | None = None
    telegram_chat_ids: list[int] | None = None

    keywords_filters: list[str] | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()
