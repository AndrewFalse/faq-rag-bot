import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from rag_bot.db.models import Document
from rag_bot.db.session import engine
from rag_bot.rag.embedder import embedder
from rag_bot.rag.parser import parse_document
from rag_bot.rag.vector_store import VectorStore
from rag_bot.sync.google_drive import GoogleDriveClient

logger = logging.getLogger(__name__)


def _index_file(
    drive: GoogleDriveClient,
    store: VectorStore,
    file_id: str,
    filename: str,
    mime_type: str,
    topic: str,
) -> None:
    path = drive.download_file(file_id, filename, mime_type)
    try:
        chunks = parse_document(path, topic, file_id)
        vectors = embedder.embed_documents(
            [c.page_content for c in chunks]
        )
        store.add_documents(chunks, vectors)
    finally:
        drive.delete_local_file(path)


async def sync_drive() -> dict:
    drive = GoogleDriveClient()
    store = VectorStore()

    result: dict = {"added": 0, "updated": 0, "deleted": 0, "errors": []}

    topic_folders = drive.get_topic_folders()

    # Собираем все файлы из Drive по темам
    drive_files: dict[str, dict] = {}
    for topic, folder_id in topic_folders.items():
        for f in drive.list_files_in_folder(folder_id):
            drive_files[f["id"]] = {**f, "topic": topic}

    with Session(engine) as session:
        db_docs = {
            doc.drive_file_id: doc
            for doc in session.query(Document).all()
        }

        drive_ids = set(drive_files.keys())
        db_ids = set(db_docs.keys())

        # --- Новые файлы ---
        for file_id in drive_ids - db_ids:
            info = drive_files[file_id]
            try:
                _index_file(drive, store, file_id, info["name"], info["mimeType"], info["topic"])
                session.add(Document(
                    drive_file_id=file_id,
                    filename=info["name"],
                    topic=info["topic"],
                    modified_time=info["modifiedTime"],
                    is_indexed=True,
                    indexed_at=datetime.now(timezone.utc),
                ))
                session.commit()
                result["added"] += 1
                logger.info("Added: %s", info["name"])
            except Exception as exc:
                session.rollback()
                result["errors"].append(f"add {info['name']}: {exc}")
                logger.exception("Error adding %s", info["name"])

        # --- Изменённые файлы ---
        for file_id in drive_ids & db_ids:
            info = drive_files[file_id]
            doc = db_docs[file_id]
            if info["modifiedTime"] == doc.modified_time:
                continue
            try:
                store.delete_by_file_id(file_id)
                _index_file(drive, store, file_id, info["name"], info["mimeType"], info["topic"])
                doc.filename = info["name"]
                doc.topic = info["topic"]
                doc.modified_time = info["modifiedTime"]
                doc.is_indexed = True
                doc.indexed_at = datetime.now(timezone.utc)
                session.commit()
                result["updated"] += 1
                logger.info("Updated: %s", info["name"])
            except Exception as exc:
                session.rollback()
                result["errors"].append(f"update {info['name']}: {exc}")
                logger.exception("Error updating %s", info["name"])

        # --- Удалённые файлы ---
        for file_id in db_ids - drive_ids:
            doc = db_docs[file_id]
            try:
                store.delete_by_file_id(file_id)
                session.delete(doc)
                session.commit()
                result["deleted"] += 1
                logger.info("Deleted: %s", doc.filename)
            except Exception as exc:
                session.rollback()
                result["errors"].append(f"delete {doc.filename}: {exc}")
                logger.exception("Error deleting %s", doc.filename)

    return result


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        sync_drive,
        trigger=CronTrigger(day_of_week="sun", hour=2),
        id="weekly_sync",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started: sync_drive every Sunday at 02:00")
    return scheduler


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(sync_drive())
    print(f"Синхронизация завершена: {result}")
