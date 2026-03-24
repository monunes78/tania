"""
Divide texto em chunks com overlap para indexação no Qdrant.
"""
from typing import List


def chunk_text(
    text: str,
    chunk_size: int = 400,
    overlap: int = 50,
) -> List[str]:
    """
    Divide o texto em chunks por palavras, com overlap.
    chunk_size e overlap são contados em palavras.
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        if end >= len(words):
            break
        start = end - overlap

    return chunks
