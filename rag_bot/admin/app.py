import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from rag_bot.config import settings
from rag_bot.db.models import Document
from rag_bot.db.session import engine
from rag_bot.rag.vector_store import VectorStore
from rag_bot.sync.indexer import sync_drive

app = FastAPI()
security = HTTPBasic()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

_store = VectorStore()


def check_auth(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    if not secrets.compare_digest(credentials.password, settings.ADMIN_PASSWORD):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/admin/", response_class=HTMLResponse)
async def admin_index(
    request: Request,
    _user: str = Depends(check_auth),
) -> HTMLResponse:
    with Session(engine) as session:
        docs = session.query(Document).order_by(Document.filename).all()
        stats = {
            "total": len(docs),
            "rpd": sum(1 for d in docs if d.topic == "RPD"),
            "gea": sum(1 for d in docs if d.topic == "GEA"),
        }
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "documents": docs, "stats": stats},
        )


@app.post("/admin/sync")
async def admin_sync(_user: str = Depends(check_auth)) -> dict:
    result = await sync_drive()
    return {
        "status": "ok",
        "added": result["added"],
        "updated": result["updated"],
        "deleted": result["deleted"],
    }


@app.delete("/admin/document/{drive_file_id}")
async def admin_delete_document(
    drive_file_id: str,
    _user: str = Depends(check_auth),
) -> dict:
    _store.delete_by_file_id(drive_file_id)

    with Session(engine) as session:
        doc = (
            session.query(Document)
            .filter(Document.drive_file_id == drive_file_id)
            .first()
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        doc.is_indexed = False
        doc.indexed_at = None
        session.commit()

    return {"status": "deleted"}
