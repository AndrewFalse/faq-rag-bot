import os
from pathlib import Path

# Set env vars before any project imports
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("GIGACHAT_API_KEY", "test")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("QDRANT_API_KEY", "test")
os.environ.setdefault("GOOGLE_SERVICE_ACCOUNT_JSON", "test.json")
os.environ.setdefault("GOOGLE_DRIVE_ROOT_FOLDER_ID", "test")
os.environ.setdefault("ADMIN_PASSWORD", "test")

from rag_bot.rag.parser import parse_document

TMP_FILE = Path("/tmp/test_rag.txt")


def setup_module() -> None:
    TMP_FILE.write_text(
        "Рабочая программа дисциплины Математика.\n"
        "Курс предназначен для студентов первого курса.\n"
        "Включает разделы: линейная алгебра, математический анализ, "
        "теория вероятностей и математическая статистика.\n"
        "Форма контроля: экзамен в конце семестра.\n",
        encoding="utf-8",
    )


def teardown_module() -> None:
    TMP_FILE.unlink(missing_ok=True)


def test_parse_returns_chunks() -> None:
    chunks = parse_document(str(TMP_FILE), "RPD", "drive_123")
    assert len(chunks) > 0, "parse_document must return at least one chunk"


def test_chunks_have_topic_metadata() -> None:
    chunks = parse_document(str(TMP_FILE), "RPD", "drive_123")
    for chunk in chunks:
        assert "topic" in chunk.metadata
        assert chunk.metadata["topic"] == "RPD"


def test_chunks_have_source_metadata() -> None:
    chunks = parse_document(str(TMP_FILE), "GEA", "drive_456")
    for chunk in chunks:
        assert chunk.metadata["source"] == "test_rag.txt"
        assert chunk.metadata["drive_file_id"] == "drive_456"


def test_chunks_have_content() -> None:
    chunks = parse_document(str(TMP_FILE), "RPD", "drive_123")
    for chunk in chunks:
        assert len(chunk.page_content) > 0
