import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session

from rag_bot.db.models import Document
from rag_bot.db.session import engine, init_db
from rag_bot.rag.vector_store import COLLECTION, VectorStore
from rag_bot.sync.indexer import sync_drive


def reset_db():
    init_db()
    with Session(engine) as session:
        deleted = session.query(Document).delete()
        session.commit()
    print(f"Удалено записей из SQLite: {deleted}")


def reset_qdrant():
    store = VectorStore()
    existing = [c.name for c in store._client.get_collections().collections]
    if COLLECTION in existing:
        store._client.delete_collection(COLLECTION)
        print("Коллекция Qdrant удалена")
    store._ensure_collection()
    print("Коллекция Qdrant создана заново с индексом topic")


async def main():
    print("=== Шаг 1: сброс Qdrant коллекции ===")
    reset_qdrant()

    print()
    print("=== Шаг 2: сброс SQLite метаданных ===")
    reset_db()

    print()
    print("=== Шаг 3: переиндексация документов из Google Drive ===")
    result = await sync_drive()
    print(f"Результат: {result}")


if __name__ == "__main__":
    asyncio.run(main())
