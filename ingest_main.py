"""
Ingestion pipeline entry point.

Orchestrates the full scan → split → upsert flow to populate the
local ChromaDB vector store from upstream Markdown documents.

Usage::

    python ingest_main.py           # incremental upsert
    python ingest_main.py --force   # drop + recreate collection
"""

from __future__ import annotations

import argparse
import sys
import time

from src.config import settings
from src.ingest.file_scanner import scan_markdown_files
from src.ingest.text_splitter import DocumentChunk, split_document
from src.ingest.vector_store import get_or_create_collection, upsert_documents
from src.logger import get_logger

logger = get_logger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest HarmonyOS Markdown docs into ChromaDB."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Drop and recreate the ChromaDB collection before ingesting.",
    )
    return parser.parse_args()


def run_ingestion(force: bool = False) -> None:
    """Execute the full ingestion pipeline.

    Steps:
        1. Scan the document directory for Markdown files.
        2. Split each file into chunks using header-based splitting.
        3. Upsert all chunks into ChromaDB.

    Args:
        force: If ``True``, recreate the collection from scratch.
    """
    start = time.monotonic()
    logger.info("=" * 60)
    logger.info("Starting ingestion pipeline")
    logger.info("  Source: %s", settings.docs_source_path)
    logger.info("  Storage: %s", settings.chroma_storage_path)
    logger.info("  Model: %s", settings.embedding_model_name)
    logger.info("  Force recreate: %s", force)
    logger.info("=" * 60)

    # --- Step 1: Scan ---
    scanned_files = scan_markdown_files(settings.docs_source_path)
    if not scanned_files:
        logger.warning("No Markdown files found. Exiting.")
        return

    # --- Step 2: Split ---
    all_chunks: list[DocumentChunk] = []
    for sf in scanned_files:
        metadata = {
            "category": sf.category,
            "source_path": str(sf.path),
        }
        chunks = split_document(sf.content, metadata)
        all_chunks.extend(chunks)

    logger.info(
        "Total chunks after splitting: %d (from %d files)",
        len(all_chunks),
        len(scanned_files),
    )

    if not all_chunks:
        logger.warning("All documents produced zero chunks. Exiting.")
        return

    # --- Step 3: Upsert ---
    _client, collection = get_or_create_collection(force_recreate=force)
    upserted = upsert_documents(collection, all_chunks)

    elapsed = time.monotonic() - start
    logger.info("=" * 60)
    logger.info("Ingestion complete.")
    logger.info("  Files scanned : %d", len(scanned_files))
    logger.info("  Chunks upserted: %d", upserted)
    logger.info("  Collection size: %d", collection.count())
    logger.info("  Time elapsed   : %.1fs", elapsed)
    logger.info("=" * 60)


def main() -> None:
    """CLI entry point."""
    args = _parse_args()
    try:
        run_ingestion(force=args.force)
    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user.")
        sys.exit(130)
    except Exception:
        logger.exception("Ingestion failed with an unexpected error.")
        sys.exit(1)


if __name__ == "__main__":
    main()
