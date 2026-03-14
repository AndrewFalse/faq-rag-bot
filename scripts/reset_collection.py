import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_bot.rag.vector_store import COLLECTION, VectorStore


def reset():
    store = VectorStore()
    existing = [c.name for c in store._client.get_collections().collections]

    if COLLECTION in existing:
        store._client.delete_collection(COLLECTION)
        print(f"Коллекция '{COLLECTION}' удалена")
    else:
        print(f"Коллекция '{COLLECTION}' не существует, пропускаем удаление")

    store._ensure_collection()
    print(f"Коллекция '{COLLECTION}' создана заново с индексом на поле 'topic'")


if __name__ == "__main__":
    reset()
