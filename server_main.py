"""
HarmonyOS RAG MCP Server.

A FastMCP server that exposes two tools for local LLM agents:

- ``list_knowledge_categories``: enumerate available doc categories.
- ``search_harmony_docs``: vector similarity search with optional
  category filtering.

Communicates via stdio (standard MCP transport for local agents).

Usage::

    python server_main.py
"""

from __future__ import annotations

import sys

from mcp.server.fastmcp import FastMCP

from src.logger import get_logger
from src.server.query_engine import QueryEngine

logger = get_logger(__name__)

# --- Initialize MCP Server & Query Engine ---

mcp = FastMCP("HarmonyOS-Docs-RAG")

# Lazy-init query engine on first tool call to avoid blocking server
# startup with heavy model loading.
_engine: QueryEngine | None = None


def _get_engine() -> QueryEngine:
    """Lazy singleton accessor for the query engine."""
    global _engine
    if _engine is None:
        _engine = QueryEngine()
    return _engine


# --- MCP Tools ---


@mcp.tool()
def list_knowledge_categories() -> str:
    """List all available knowledge categories in the HarmonyOS documentation.

    Returns a newline-separated list of category names that can be used
    to filter searches via ``search_harmony_docs``.
    """
    try:
        engine = _get_engine()
        categories = engine.list_categories()
        if not categories:
            return "No categories found. The knowledge base may be empty — please run ingest_main.py first."
        return "\n".join(categories)
    except Exception as exc:
        logger.exception("list_knowledge_categories failed.")
        return f"Error listing categories: {exc}"


@mcp.tool()
def search_harmony_docs(
    query: str,
    category: str = "",
    n_results: int = 5,
) -> str:
    """Search the HarmonyOS documentation knowledge base.

    Performs vector similarity search against the local ChromaDB store.
    Optionally filter by a specific documentation category.

    Args:
        query: Natural language search query describing what you're
            looking for, e.g. "How to use AbilityStage lifecycle".
        category: Optional category name to restrict search scope.
            Use ``list_knowledge_categories`` to see available values.
            Leave empty to search all categories.
        n_results: Number of results to return (1-20, default 5).

    Returns:
        Formatted search results with source information, or an error
        message if something goes wrong.
    """
    if not query or not query.strip():
        return "Error: 'query' parameter is required and must not be empty."

    try:
        engine = _get_engine()
        results = engine.search(
            query=query.strip(),
            n_results=n_results,
            category=category.strip() if category else None,
        )

        if not results:
            hint = f" in category '{category}'" if category else ""
            return f"No results found for '{query}'{hint}. Try broadening your search or removing the category filter."

        # Format results for LLM consumption.
        parts: list[str] = []
        for i, r in enumerate(results, 1):
            parts.append(
                f"--- Result {i} (distance: {r.distance:.4f}) ---\n"
                f"Category: {r.category}\n"
                f"Source: {r.source_path}\n"
                f"\n{r.content}\n"
            )

        return "\n".join(parts)

    except Exception as exc:
        logger.exception("search_harmony_docs failed.")
        return f"Error during search: {exc}"


# --- Entry Point ---


def main() -> None:
    """Start the MCP server in stdio mode."""
    logger.info("Starting HarmonyOS-Docs-RAG MCP Server (stdio mode)...")
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server shut down by user.")
        sys.exit(0)
    except Exception:
        logger.exception("Server crashed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
