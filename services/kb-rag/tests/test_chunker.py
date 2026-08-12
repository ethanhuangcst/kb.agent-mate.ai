"""Chunker unit tests."""

from app.chunker import chunk_text


def test_should_return_single_chunk_when_short():
    assert chunk_text("hello world") == ["hello world"]


def test_should_split_long_text_when_over_size():
    text = "para one.\n\n" + ("word " * 400)
    parts = chunk_text(text, chunk_size=200, chunk_overlap=20)
    assert len(parts) >= 2
    assert all(len(p) <= 250 for p in parts)
