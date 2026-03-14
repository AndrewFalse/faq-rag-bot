from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_core.documents import Document

_LOADERS = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
}

_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


def parse_document(
    file_path: str,
    topic: str,
    drive_file_id: str,
) -> list[Document]:
    ext = Path(file_path).suffix.lower()
    loader_cls = _LOADERS.get(ext)
    if loader_cls is None:
        raise ValueError(f"Unsupported file extension: {ext}")

    pages = loader_cls(file_path).load()
    chunks = _splitter.split_documents(pages)

    filename = Path(file_path).name
    for chunk in chunks:
        chunk.metadata.update(
            {
                "topic": topic,
                "source": filename,
                "drive_file_id": drive_file_id,
            }
        )

    return chunks
