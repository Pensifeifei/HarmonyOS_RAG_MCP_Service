"""
Vector store integration for the ingestion pipeline.

Provides a custom ChromaDB-compatible embedding function backed by a
local SentenceTransformers model, plus helpers to upsert document
chunks into ChromaDB with deterministic IDs.
"""

from __future__ import annotations

import hashlib
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.api.types import EmbeddingFunction, Embeddings, Documents
from sentence_transformers import SentenceTransformer

from src.config import settings
from src.ingest.text_splitter import DocumentChunk
from src.logger import get_logger

logger = get_logger(__name__)

# Maximum batch size for ChromaDB upsert operations.
_UPSERT_BATCH_SIZE = 200


class LocalEmbeddingFunction(EmbeddingFunction[Documents]):
    """ChromaDB embedding function using a local SentenceTransformers model.

    The model is loaded lazily on the first call to avoid blocking import
    time when the vector store module is imported but not immediately used.
    """

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    def _ensure_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading embedding model: %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)
            logger.info("Embedding model loaded successfully.")
        return self._model

    def __call__(self, input: Documents) -> Embeddings:
        """Encode a batch of documents into embeddings.

        Args:
            input: List of text strings to encode.

        Returns:
            List of embedding vectors (each a list of floats).
        """
        model = self._ensure_model()
        embeddings = model.encode(input, show_progress_bar=False, normalize_embeddings=True)
        return embeddings.tolist()


def _make_chroma_client() -> chromadb.ClientAPI:
    """Create a ChromaDB PersistentClient at the configured storage path."""
    storage_path = str(settings.chroma_storage_path)
    logger.info("Initializing ChromaDB PersistentClient at: %s", storage_path)
    return chromadb.PersistentClient(path=storage_path)


def get_or_create_collection(
    client: chromadb.ClientAPI | None = None,
    force_recreate: bool = False,
) -> tuple[chromadb.ClientAPI, Collection]:
    """Get or create the ChromaDB collection with the configured embedding function.

    Args:
        client: Optional existing ChromaDB client. If ``None``, a new
            ``PersistentClient`` is created.
        force_recreate: If ``True``, delete the existing collection
            before creating a fresh one.

    Returns:
        A tuple of ``(client, collection)``.
    """
    if client is None:
        client = _make_chroma_client()

    ef = LocalEmbeddingFunction(settings.embedding_model_name)
    collection_name = settings.chroma_collection_name

    if force_recreate:
        try:
            client.delete_collection(collection_name)
            logger.info("Deleted existing collection: %s", collection_name)
        except Exception:
            # Collection may not exist yet — that's fine.
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info(
        "Collection '%s' ready (current count: %d)",
        collection_name,
        collection.count(),
    )
    return client, collection


def _chunk_id(chunk: DocumentChunk) -> str:
    """Deterministic ID from chunk content + source metadata.

    Using a content hash makes upserts idempotent — re-ingesting the
    same document won't create duplicates.
    """
    source = chunk.metadata.get("source_path", "")
    raw = f"{source}::{chunk.content}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def upsert_documents(
    collection: Collection,
    chunks: list[DocumentChunk],
) -> int:
    """Upsert document chunks into the ChromaDB collection.

    Processes chunks in batches of ``_UPSERT_BATCH_SIZE`` to stay within
    ChromaDB's per-request limits.

    Args:
        collection: Target ChromaDB collection.
        chunks: List of ``DocumentChunk`` objects to upsert.

    Returns:
        Number of chunks successfully upserted.
    """
    if not chunks:
        return 0

    total = 0

    for i in range(0, len(chunks), _UPSERT_BATCH_SIZE):
        batch = chunks[i : i + _UPSERT_BATCH_SIZE]

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for chunk in batch:
            ids.append(_chunk_id(chunk))
            documents.append(chunk.content)
            # ChromaDB metadata values must be str | int | float | bool.
            clean_meta = {
                k: str(v) for k, v in chunk.metadata.items() if v is not None
            }
            metadatas.append(clean_meta)

        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            total += len(batch)
        except Exception:
            logger.exception(
                "Failed to upsert batch %d–%d",
                i,
                i + len(batch),
            )

    logger.info("Upserted %d / %d chunks into collection.", total, len(chunks))
    return total
