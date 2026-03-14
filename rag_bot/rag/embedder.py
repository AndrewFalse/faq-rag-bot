from openai import OpenAI

from rag_bot.config import settings


class Embedder:
    def __init__(self) -> None:
        self._client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )
        self._model = "qwen/qwen3-embedding-8b"

    def embed_text(self, text: str) -> list[float]:
        response = self._client.embeddings.create(
            input=[text],
            model=self._model,
        )
        return response.data[0].embedding

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(
            input=texts,
            model=self._model,
        )
        return [item.embedding for item in response.data]


embedder = Embedder()
