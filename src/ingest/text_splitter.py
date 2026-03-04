"""
Markdown text splitter for the ingestion pipeline.

Splits Markdown content by header hierarchy using LangChain's
``MarkdownHeaderTextSplitter``, preserving structural context in
each chunk's metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langchain_text_splitters import MarkdownHeaderTextSplitter

from src.logger import get_logger

logger = get_logger(__name__)

# Headers to split on — H1 through H3.
_HEADERS_TO_SPLIT_ON: list[tuple[str, str]] = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]


@dataclass(frozen=True)
class DocumentChunk:
    """A chunk of text produced by splitting a Markdown document.

    Attributes:
        content: The text content of this chunk.
        metadata: Combined metadata — original file-level metadata plus
            header hierarchy extracted by the splitter.
    """

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


def split_document(
    content: str,
    metadata: dict[str, Any],
) -> list[DocumentChunk]:
    """Split a Markdown document into chunks by header hierarchy.

    Each returned chunk inherits the supplied *metadata* (e.g.
    ``category``, ``source_path``) and is augmented with header-level
    keys (``h1``, ``h2``, ``h3``) extracted from the document structure.

    Empty chunks are silently discarded.

    Args:
        content: Raw Markdown text to split.
        metadata: Base metadata dict to attach to every chunk.

    Returns:
        A list of ``DocumentChunk`` objects.
    """
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=_HEADERS_TO_SPLIT_ON,
        strip_headers=False,
    )

    try:
        splits = splitter.split_text(content)
    except Exception:
        logger.exception("MarkdownHeaderTextSplitter failed for %s", metadata.get("source_path", "<unknown>"))
        return []

    chunks: list[DocumentChunk] = []

    for doc in splits:
        text = doc.page_content.strip()
        if not text:
            continue

        # Merge base metadata with header-level metadata from the splitter.
        merged = {**metadata, **doc.metadata}
        chunks.append(DocumentChunk(content=text, metadata=merged))

    logger.debug(
        "Split document %s into %d chunks",
        metadata.get("source_path", "<unknown>"),
        len(chunks),
    )
    return chunks
