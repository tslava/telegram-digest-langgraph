from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    tg_api_id: Optional[int] = Field(default=None, validation_alias="TG_API_ID")
    tg_api_hash: Optional[str] = Field(default=None, validation_alias="TG_API_HASH")
    tg_bot_token: Optional[str] = Field(default=None, validation_alias="TG_BOT_TOKEN")
    tg_target_channel_id: Optional[int] = Field(
        default=None, validation_alias="TG_TARGET_CHANNEL_ID"
    )

    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")

    db_path: Path = Field(default=Path("./.local/app.db"), validation_alias="DB_PATH")
    telethon_session: Path = Field(
        default=Path("./.local/telethon.session"), validation_alias="TELETHON_SESSION"
    )

    dry_run: bool = Field(default=False, validation_alias="DRY_RUN")
    post_to_telegram: bool = Field(default=True, validation_alias="POST_TO_TELEGRAM")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    llm_mode: str = Field(default="openai", validation_alias="LLM_MODE")

    def ensure_local_paths(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.telethon_session.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_local_paths()
    return settings
