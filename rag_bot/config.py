from dataclasses import dataclass
from os import environ
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _require(name: str) -> str:
    value = environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    TELEGRAM_BOT_TOKEN: str = ""
    GIGACHAT_API_KEY: str = ""
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    GOOGLE_SERVICE_ACCOUNT_JSON: str = ""
    GOOGLE_DRIVE_ROOT_FOLDER_ID: str = ""
    ADMIN_PASSWORD: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            TELEGRAM_BOT_TOKEN=_require("TELEGRAM_BOT_TOKEN"),
            GIGACHAT_API_KEY=_require("GIGACHAT_API_KEY"),
            QDRANT_URL=_require("QDRANT_URL"),
            QDRANT_API_KEY=_require("QDRANT_API_KEY"),
            GOOGLE_SERVICE_ACCOUNT_JSON=_require("GOOGLE_SERVICE_ACCOUNT_JSON"),
            GOOGLE_DRIVE_ROOT_FOLDER_ID=_require("GOOGLE_DRIVE_ROOT_FOLDER_ID"),
            ADMIN_PASSWORD=_require("ADMIN_PASSWORD"),
        )


settings = Settings.from_env()
