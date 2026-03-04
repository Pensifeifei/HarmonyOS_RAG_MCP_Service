"""
Query engine — read-side abstraction over ChromaDB.

Provides methods to list knowledge categories and perform vector
similarity search with optional metadata filtering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from src.config import settings
from src.ingest.vector_store import LocalEmbeddingFunction
from src.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class SearchResult:
    """A single search result returned by the query engine.

    Attributes:
        content: The text content of the matched chunk.
        category: The knowledge category this chunk belongs to.
        source_path: Original file path the chunk was extracted from.
        distance: Cosine distance score (lower is more similar).
        metadata: Full metadata dict from ChromaDB.
    """

    content: str
    category: str
    source_path: str
    distance: float
    metadata: dict[str, Any] = field(default_factory=dict)


class QueryEngine:
    """Read-only query interface to the ChromaDB vector store.

    Connects to the persisted ChromaDB collection and provides
    high-level search and category-listing methods.
    """

    def __init__(self) -> None:
        storage_path = str(settings.chroma_storage_path)
        logger.info("Connecting to ChromaDB at: %s", storage_path)

        self._client = chromadb.PersistentClient(path=storage_path)
        ef = LocalEmbeddingFunction(settings.embedding_model_name)

        self._collection: Collection = self._client.get_or_create_collection(
            name=settings.chroma_collection_name,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "QueryEngine ready — collection '%s' (count: %d)",
            settings.chroma_collection_name,
            self._collection.count(),
        )

    def list_categories(self) -> list[str]:
        """Return a sorted, deduplicated list of knowledge categories.

        Categories are derived from the ``category`` metadata field
        written during ingestion.

        Returns:
            Sorted list of unique category strings.  Returns an empty
            list if the collection is empty.
        """
        try:
            # Fetch all metadata (only the "category" field) efficiently.
            result = self._collection.get(include=["metadatas"])
            if not result["metadatas"]:
                return []

            categories: set[str] = set()
            for meta in result["metadatas"]:
                cat = meta.get("category")
                if cat:
                    categories.add(cat)

            return sorted(categories)
        except Exception:
            logger.exception("Failed to list categories.")
            return []

    def search(
        self,
        query: str,
        n_results: int = 5,
        category: str | None = None,
    ) -> list[SearchResult]:
        """Perform vector similarity search with optional category filter.

        Args:
            query: The natural-language search query.
            n_results: Maximum number of results to return (1–20).
            category: If provided, restrict results to this category.

        Returns:
            A list of ``SearchResult`` objects ordered by similarity
            (most similar first).
        """
        # Clamp n_results to a reasonable range.
        n_results = max(1, min(n_results, 20))

        where_filter: dict[str, str] | None = None
        if category:
            where_filter = {"category": category}

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            logger.exception("ChromaDB query failed.")
            return []

        # Unpack the nested result structure.
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        output: list[SearchResult] = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            output.append(
                SearchResult(
                    content=doc or "",
                    category=meta.get("category", ""),
                    source_path=meta.get("source_path", ""),
                    distance=dist,
                    metadata=meta,
                )
            )

        logger.info(
            "Search '%s' (category=%s) returned %d results.",
            query[:60],
            category or "ALL",
            len(output),
        )
        return output
