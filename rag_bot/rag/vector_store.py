import uuid

from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from rag_bot.config import settings

COLLECTION = "rag_documents"
VECTOR_SIZE = 4096


class VectorStore:
    def __init__(self) -> None:
        self._client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        collections = [
            c.name for c in self._client.get_collections().collections
        ]
        if COLLECTION not in collections:
            self._client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE, distance=Distance.COSINE
                ),
            )
        self._client.create_payload_index(
            collection_name=COLLECTION,
            field_name="topic",
            field_schema="keyword",
        )

    def add_documents(self, chunks: list[Document], vectors: list[list[float]]) -> None:
        self._ensure_collection()

        points = [
            PointStruct(
                id=uuid.uuid4().hex,
                vector=vec,
                payload={
                    "text": chunk.page_content,
                    "topic": chunk.metadata.get("topic", ""),
                    "source": chunk.metadata.get("source", ""),
                    "drive_file_id": chunk.metadata.get("drive_file_id", ""),
                },
            )
            for chunk, vec in zip(chunks, vectors)
        ]

        batch_size = 100
        for i in range(0, len(points), batch_size):
            self._client.upsert(
                collection_name=COLLECTION,
                points=points[i : i + batch_size],
            )

    def search(
        self,
        query_vector: list[float],
        topic: str,
        top_k: int = 5,
    ) -> list[Document]:
        info = self._client.get_collection(COLLECTION)
        if info.points_count == 0:
            return []

        query_filter = None
        if topic != "ALL":
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="topic", match=MatchValue(value=topic)
                    )
                ]
            )

        hits = self._client.query_points(
            collection_name=COLLECTION,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
        ).points

        results = []
        for hit in hits:
            results.append(Document(
                page_content=hit.payload.get("text", ""),
                metadata=hit.payload,
            ))
        return results

    def delete_by_file_id(self, drive_file_id: str) -> None:
        self._client.delete(
            collection_name=COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="drive_file_id",
                        match=MatchValue(value=drive_file_id),
                    )
                ]
            ),
        )
