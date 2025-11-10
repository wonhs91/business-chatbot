from typing import Iterable

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from app.retrieval.vector_store import VectorStoreProvider


class RetrievalService:
    """Service wrapper to fetch relevant document snippets for conversation context."""

    def __init__(self, provider: VectorStoreProvider | None = None) -> None:
        self._provider = provider or VectorStoreProvider()

    def get_context(self, query: str, *, top_k: int = 3) -> list[Document]:
        retriever: VectorStore = self._provider.retriever()
        return retriever.similarity_search(query, k=top_k)

    def format_context(self, documents: Iterable[Document]) -> str:
        chunks = []
        for doc in documents:
            metadata = doc.metadata or {}
            source = metadata.get("source", "unknown")
            chunks.append(f"[{source}] {doc.page_content.strip()}")
        return "\n\n".join(chunks)

