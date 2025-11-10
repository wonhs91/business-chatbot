from pathlib import Path
from typing import Iterable

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document


def load_documents(data_dir: Path) -> Iterable[Document]:
    """Load documents from a directory using basic text loader fallback."""

    if not data_dir.exists():
        raise FileNotFoundError(f"Document directory not found: {data_dir}")

    loader = DirectoryLoader(
        str(data_dir),
        glob="**/*",
        show_progress=True,
        loader_cls=TextLoader,
    )
    return loader.load()

