from langchain_gigachat import GigaChatEmbeddings

from rag_bot.config import settings


class Embedder:
    def __init__(self) -> None:
        self._model = GigaChatEmbeddings(
            credentials=settings.GIGACHAT_API_KEY,
            verify_ssl_certs=False,
        )

    def embed_text(self, text: str) -> list[float]:
        return self._model.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.embed_documents(texts)


embedder = Embedder()
