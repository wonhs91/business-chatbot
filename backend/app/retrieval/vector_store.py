from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Optional

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings
from loguru import logger

from app.config.settings import get_settings


class VectorStoreProvider:
    """Factory/utility helper around the configured vector store."""

    def __init__(self) -> None:
        self._settings = get_settings()
        persist_directory = (self._settings.chroma_persist_directory or "").strip()
        self._persist_directory: Optional[Path] = None
        if persist_directory:
            self._persist_directory = Path(persist_directory).expanduser().resolve()
            self._persist_directory.mkdir(parents=True, exist_ok=True)
            logger.debug("Chroma persist directory set to {}", self._persist_directory)
        else:
            logger.debug("Chroma configured for in-memory usage (no persistence).")

        self._collection_name = self._settings.chroma_collection_name
        self._vector_store: Optional[Chroma] = None

    def embeddings(self) -> Embeddings:
        """Return embeddings implementation for the knowledge base."""
        if not self._settings.openai_api_key:
            raise RuntimeError("OpenAI API key must be configured for embeddings.")
        return OpenAIEmbeddings(
            api_key=self._settings.openai_api_key.get_secret_value(),
            model="text-embedding-3-large",
        )

    def _persist_kwargs(self) -> dict[str, Any]:
        if self._persist_directory:
            return {"persist_directory": str(self._persist_directory)}
        return {}

    def ingest_documents(self, docs: Iterable[Document]) -> None:
        """Persist documents to the vector store."""
        documents = list(docs)
        if not documents:
            logger.info("No documents provided for ingestion; skipping vector store update.")
            return

        vector_store = self.retriever()
        vector_store.add_documents(documents)
        persist = getattr(vector_store, "persist", None)
        if callable(persist) and self._persist_directory:
            persist()
            logger.info(
                "Persisted {} documents to Chroma at {}", len(documents), self._persist_directory
            )

    def retriever(self) -> VectorStore:
        """Return vector store retriever."""
        if self._vector_store:
            return self._vector_store

        embeddings = self.embeddings()
        self._vector_store = Chroma(
            embedding_function=embeddings,
            collection_name=self._collection_name,
            **self._persist_kwargs(),
        )
        return self._vector_store

