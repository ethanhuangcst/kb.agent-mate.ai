"""Simple recursive character chunker for confirm→index."""

from __future__ import annotations


def chunk_text(
    text: str,
    *,
    chunk_size: int = 1200,
    chunk_overlap: int = 120,
    min_chars: int = 50,
) -> list[str]:
    """Split text into overlapping chunks. Empty/whitespace-only → []."""
    cleaned = (text or "").strip()
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    separators = ["\n\n", "\n", "。", ". ", " ", ""]
    parts = _split_recursive(cleaned, separators, chunk_size)
    merged: list[str] = []
    buf = ""
    for part in parts:
        if not buf:
            buf = part
        elif len(buf) + len(part) + 1 <= chunk_size:
            buf = f"{buf} {part}".strip() if not buf.endswith("\n") else f"{buf}{part}"
        else:
            if len(buf) >= min_chars:
                merged.append(buf)
            else:
                # keep short remainder attached next if possible
                pass
            if chunk_overlap > 0 and len(buf) > chunk_overlap:
                overlap = buf[-chunk_overlap:]
                buf = f"{overlap}{part}".strip()
            else:
                buf = part
    if buf and len(buf) >= min_chars:
        merged.append(buf)
    elif buf and merged:
        merged[-1] = f"{merged[-1]} {buf}".strip()
    elif buf:
        merged.append(buf)
    return merged


def _split_recursive(text: str, separators: list[str], chunk_size: int) -> list[str]:
    if len(text) <= chunk_size or not separators:
        return [text]
    sep = separators[0]
    rest = separators[1:]
    if sep == "":
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    pieces = text.split(sep)
    out: list[str] = []
    for i, piece in enumerate(pieces):
        piece = piece if sep == "" else (piece if i == len(pieces) - 1 else f"{piece}{sep}")
        if len(piece) <= chunk_size:
            if piece:
                out.append(piece)
        else:
            out.extend(_split_recursive(piece, rest, chunk_size))
    return out
