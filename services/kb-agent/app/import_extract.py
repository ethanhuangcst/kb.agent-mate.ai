"""Extract text from import files (.md / .txt / text-layer PDF)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ALLOWED_EXTENSIONS = {".md", ".txt", ".pdf"}


@dataclass
class ExtractResult:
    text: str | None
    error_code: str | None
    message: str | None


def extension_of(filename: str) -> str:
    return Path(filename or "").suffix.lower()


def is_allowed_filename(filename: str) -> bool:
    return extension_of(filename) in ALLOWED_EXTENSIONS


def extract_text(filename: str, data: bytes) -> ExtractResult:
    ext = extension_of(filename)
    if ext not in ALLOWED_EXTENSIONS:
        return ExtractResult(
            None,
            "IMPORT_FILE_REJECTED",
            f"unsupported extension {ext or '(none)'}; allowed: .md .txt .pdf",
        )
    if ext in {".md", ".txt"}:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = data.decode("utf-8-sig")
            except UnicodeDecodeError:
                return ExtractResult(None, "IMPORT_FILE_REJECTED", "text file is not valid UTF-8")
        if not text.strip():
            return ExtractResult(None, "IMPORT_FILE_REJECTED", "empty text file")
        return ExtractResult(text, None, None)

    # PDF — text layer only
    try:
        from pypdf import PdfReader
        import io

        reader = PdfReader(io.BytesIO(data))
        parts: list[str] = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        text = "\n".join(parts).strip()
    except Exception as exc:  # noqa: BLE001 — surface as reject
        return ExtractResult(None, "IMPORT_FILE_REJECTED", f"pdf extract failed: {exc}")
    if not text:
        return ExtractResult(
            None,
            "IMPORT_FILE_REJECTED",
            "pdf has no extractable text layer",
        )
    return ExtractResult(text, None, None)


def import_limits_from_env() -> tuple[int, int, int]:
    max_files = int(os.environ.get("KB_IMPORT_MAX_FILES_PER_BATCH", "20"))
    max_file = int(os.environ.get("KB_IMPORT_MAX_BYTES_PER_FILE", str(5 * 1024 * 1024)))
    max_batch = int(os.environ.get("KB_IMPORT_MAX_BYTES_PER_BATCH", str(20 * 1024 * 1024)))
    return max_files, max_file, max_batch
