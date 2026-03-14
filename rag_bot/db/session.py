from pathlib import Path

from sqlalchemy import create_engine

from rag_bot.db.models import Base

DB_PATH = Path(__file__).resolve().parent.parent.parent / "rag_bot.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


def init_db() -> None:
    Base.metadata.create_all(engine)
