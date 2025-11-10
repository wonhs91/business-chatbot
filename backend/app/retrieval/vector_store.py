from typing import Any, Iterable, Optional

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.config.settings import get_settings


class VectorStoreProvider:
    """Factory/utility helper around the configured vector store."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: Optional[QdrantClient] = None
        self._vector_store: Optional[VectorStore] = None

    def client(self) -> QdrantClient:
        """Return cached Qdrant client."""
        if self._client is None:
            if not self._settings.vector_store_url:
                raise RuntimeError("Vector store URL not configured.")
            self._client = QdrantClient(
                url=str(self._settings.vector_store_url),
                api_key=self._settings.vector_store_api_key.get_secret_value()
                if self._settings.vector_store_api_key
                else None,
            )
        return self._client

    def embeddings(self) -> Embeddings:
        """Return embeddings implementation for the knowledge base."""
        if not self._settings.openai_api_key:
            raise RuntimeError("OpenAI API key must be configured for embeddings.")
        return OpenAIEmbeddings(
            api_key=self._settings.openai_api_key.get_secret_value(),
            model="text-embedding-3-large",
        )

    def ensure_collection(self, vector_size: int) -> None:
        """Create the collection if it does not exist."""
        client = self.client()
        collection = self._settings.vector_store_collection
        if collection not in [col.name for col in client.get_collections().collections]:
            logger.info("Creating vector collection {}", collection)
            client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def ingest_documents(self, docs: Iterable[Document]) -> None:
        """Persist documents to the vector store."""
        from langchain_community.vectorstores import Qdrant

        embeddings = self.embeddings()
        test_vector = embeddings.embed_query("test")
        self.ensure_collection(vector_size=len(test_vector))
        vector_store = Qdrant.from_documents(
            list(docs),
            embeddings,
            url=str(self._settings.vector_store_url),
            api_key=self._settings.vector_store_api_key.get_secret_value()
            if self._settings.vector_store_api_key
            else None,
            collection_name=self._settings.vector_store_collection,
        )
        self._vector_store = vector_store

    def retriever(self) -> VectorStore:
        """Return vector store retriever."""
        if self._vector_store:
            return self._vector_store

        from langchain_community.vectorstores import Qdrant

        embeddings = self.embeddings()
        self._vector_store = Qdrant(
            client=self.client(),
            collection_name=self._settings.vector_store_collection,
            embeddings=embeddings,
        )
        return self._vector_store
