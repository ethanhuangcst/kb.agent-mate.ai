"""Local filesystem BlobStore."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


class BlobStore:
    """LocalFs BlobStore: put / get / delete by content-addressed or explicit key."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        # Avoid path traversal; nest by first two hex chars when key looks like a hash.
        safe = key.replace("..", "").lstrip("/\\")
        if len(safe) >= 4 and all(c in "0123456789abcdef" for c in safe[:4].lower()):
            return self.root / safe[:2] / safe[2:4] / safe
        return self.root / safe

    def put(self, data: bytes, *, key: str | None = None) -> str:
        """Store bytes; return the blob key (uri-relative id)."""
        if key is None:
            key = hashlib.sha256(data).hexdigest()
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def get(self, key: str) -> bytes:
        path = self._path_for(key)
        if not path.is_file():
            raise FileNotFoundError(f"blob not found: {key}")
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._path_for(key)
        if path.is_file():
            path.unlink()
            # Best-effort cleanup of empty parents (ignore errors).
            for parent in (path.parent, path.parent.parent):
                try:
                    if parent != self.root and parent.is_dir() and not any(parent.iterdir()):
                        parent.rmdir()
                except OSError:
                    pass

    def exists(self, key: str) -> bool:
        return self._path_for(key).is_file()


def default_blob_store() -> BlobStore:
    root = os.environ.get("BLOB_ROOT", "/tmp/kb-blob")
    return BlobStore(root)
