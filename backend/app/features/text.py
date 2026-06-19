"""Text features for the Triage engine.

Provides text cleaning, script-based language detection (Indic vs. Latin), and a
CPU-cached LaBSE sentence-embedder singleton. LaBSE is multilingual, so the same
embedding space covers English/transliterated and native Kannada/Devanagari text.
"""
from __future__ import annotations

import re

import numpy as np

from app.core.logging import get_logger

logger = get_logger("pravah.features.text")

# Default multilingual embedding model (CPU). Override with MURIL via the
# trainer's --muril flag if a GPU is available.
LABSE_MODEL = "sentence-transformers/LaBSE"

# Script ranges for Indic detection.
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")  # Hindi / Marathi etc.
_KANNADA = re.compile(r"[ಀ-೿]")
_WHITESPACE = re.compile(r"\s+")


def clean_text(text: str | None) -> str:
    """Trim, collapse internal whitespace, and drop control chars.

    Case and script are preserved — LaBSE is case- and script-aware, so lowering
    or transliterating would only lose signal.
    """
    # Type-guard handles None, pandas NA, and NaN floats in one shot.
    if not isinstance(text, str) or not text:
        return ""
    cleaned = "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32)
    return _WHITESPACE.sub(" ", cleaned).strip()


def detect_lang(text: str | None) -> str:
    """Return ``"indic"`` if Devanagari/Kannada characters are present, else ``"latin"``."""
    if not text:
        return "latin"
    if _KANNADA.search(text) or _DEVANAGARI.search(text):
        return "indic"
    return "latin"


class TextEmbedder:
    """Lazy, process-wide LaBSE embedder (loaded once, reused everywhere)."""

    def __init__(self, model_name: str = LABSE_MODEL) -> None:
        self.model_name = model_name
        self._model = None  # type: ignore[var-annotated]

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        if self._model is not None:
            return
        # Imported lazily so the heavy dependency only loads when embeddings are needed.
        from sentence_transformers import SentenceTransformer

        logger.info("Loading sentence embedder: %s (CPU)", self.model_name)
        self._model = SentenceTransformer(self.model_name, device="cpu")
        logger.info("Embedder loaded (dim=%d)", self.dim)

    @property
    def dim(self) -> int:
        if self._model is None:
            raise RuntimeError("Embedder not loaded — call load() first.")
        # Method was renamed across sentence-transformers versions.
        getter = getattr(self._model, "get_embedding_dimension", None) or (
            self._model.get_sentence_embedding_dimension
        )
        return int(getter())

    def encode(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        """Embed texts to an (n, dim) float32 array (L2-normalized)."""
        if self._model is None:
            self.load()
        assert self._model is not None
        return self._model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype(np.float32)


_embedder = TextEmbedder()


def get_embedder() -> TextEmbedder:
    """Return the process-wide LaBSE embedder singleton."""
    return _embedder
