"""
File scanner for the ingestion pipeline.

Recursively walks the upstream document directory, collects Markdown
files, and extracts category metadata from the directory structure.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.logger import get_logger

logger = get_logger(__name__)

# Directories to skip during scanning.
_EXCLUDED_DIRS: frozenset[str] = frozenset({"Archived", ".git", "__pycache__", "node_modules"})


@dataclass(frozen=True)
class ScannedFile:
    """Represents a single Markdown file discovered during scanning.

    Attributes:
        path: Absolute path to the Markdown file.
        category: Top-level directory name relative to the docs root,
            used as the primary metadata tag for retrieval filtering.
        content: Raw text content of the file.
    """

    path: Path
    category: str
    content: str


def scan_markdown_files(root: Path) -> list[ScannedFile]:
    """Recursively scan *root* for Markdown files and extract metadata.

    The **category** is derived from the first-level subdirectory name
    relative to *root*.  For example, given::

        root/
          Application-Configuration-Stage/
            overview.md   -> category = "Application-Configuration-Stage"
            guide/
              usage.md    -> category = "Application-Configuration-Stage"

    Files directly under *root* get category ``"_root"``.

    Args:
        root: Absolute path to the upstream document directory.

    Returns:
        A list of ``ScannedFile`` objects, sorted by path for
        deterministic processing order.
    """
    if not root.is_dir():
        logger.error("Document root does not exist: %s", root)
        return []

    results: list[ScannedFile] = []
    skipped = 0

    for md_path in sorted(root.rglob("*.md")):
        # Skip files inside excluded directories.
        if any(part in _EXCLUDED_DIRS for part in md_path.parts):
            skipped += 1
            continue

        # Derive category from the first-level subdirectory.
        relative = md_path.relative_to(root)
        category = relative.parts[0] if len(relative.parts) > 1 else "_root"

        try:
            content = md_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            logger.warning("Failed to read %s: %s", md_path, exc)
            skipped += 1
            continue

        if not content.strip():
            logger.debug("Skipping empty file: %s", md_path)
            skipped += 1
            continue

        results.append(ScannedFile(path=md_path, category=category, content=content))

    logger.info(
        "Scanned %d Markdown files (%d skipped) under %s",
        len(results),
        skipped,
        root,
    )
    return results
