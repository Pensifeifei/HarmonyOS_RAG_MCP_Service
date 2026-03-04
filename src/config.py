"""
Centralized configuration module.

Loads settings from a `.env` file via python-dotenv and exposes them
as a typed, validated dataclass singleton.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
import os

# Load .env from the project root (two levels up from this file).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Immutable application settings populated from environment variables.

    Attributes:
        docs_source_path: Absolute path to the upstream cleaned Markdown docs.
        chroma_storage_path: Directory for ChromaDB persistent storage.
        embedding_model_name: HuggingFace model ID for the local embedding model.
        chroma_collection_name: Name of the ChromaDB collection.
        log_level: Python logging level string.
    """

    docs_source_path: Path
    chroma_storage_path: Path = field(
        default_factory=lambda: _PROJECT_ROOT / "chroma_data"
    )
    embedding_model_name: str = "BAAI/bge-large-zh-v1.5"
    chroma_collection_name: str = "harmonyos_docs"
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        """Validate critical paths after initialization."""
        if not self.docs_source_path.is_dir():
            print(
                f"[CONFIG ERROR] DOCS_SOURCE_PATH does not exist or is not a "
                f"directory: {self.docs_source_path}",
                file=sys.stderr,
            )


def _load_settings() -> Settings:
    """Build a ``Settings`` instance from environment variables.

    Returns:
        A fully populated ``Settings`` object.

    Raises:
        SystemExit: If the required ``DOCS_SOURCE_PATH`` is not set.
    """
    docs_source = os.getenv("DOCS_SOURCE_PATH")
    if not docs_source:
        print(
            "[CONFIG ERROR] DOCS_SOURCE_PATH is not set. "
            "Please configure it in your .env file.",
            file=sys.stderr,
        )
        sys.exit(1)

    chroma_storage = os.getenv("CHROMA_STORAGE_PATH")

    return Settings(
        docs_source_path=Path(docs_source).resolve(),
        chroma_storage_path=(
            Path(chroma_storage).resolve()
            if chroma_storage
            else _PROJECT_ROOT / "chroma_data"
        ),
        embedding_model_name=os.getenv(
            "EMBEDDING_MODEL_NAME", "BAAI/bge-large-zh-v1.5"
        ),
        chroma_collection_name=os.getenv(
            "CHROMA_COLLECTION_NAME", "harmonyos_docs"
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


# Global singleton — import ``settings`` directly from this module.
settings: Settings = _load_settings()
