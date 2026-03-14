from langchain_gigachat import GigaChat
from langchain_core.messages import HumanMessage, SystemMessage

from rag_bot.config import settings
from rag_bot.rag.embedder import embedder
from rag_bot.rag.vector_store import VectorStore

SYSTEM_PROMPT = (
    "Ты — помощник IT-отдела вуза. Отвечай ТОЛЬКО на основе предоставленных "
    "фрагментов документов. Не добавляй информацию из своих знаний. "
    "Если ответа нет в документах — скажи: В документах информации нет."
)

_llm = GigaChat(
    model="GigaChat-Pro",
    credentials=settings.GIGACHAT_API_KEY,
    verify_ssl_certs=False,
)

_store = VectorStore()


def get_answer(question: str, topic: str) -> dict:
    query_vector = embedder.embed_text(question)
    chunks = _store.search(query_vector, topic, top_k=5)

    if not chunks:
        return {"answer": "По данной теме документов нет.", "sources": []}

    context = "\n\n---\n\n".join(chunk.page_content for chunk in chunks)
    sources = list(dict.fromkeys(
        chunk.metadata["source"] for chunk in chunks
    ))

    user_text = (
        f"Контекст из документов:\n{context}\n\n"
        f"Вопрос: {question}"
    )

    response = _llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_text),
    ])

    return {"answer": response.content, "sources": sources}
