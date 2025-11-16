"""Hashing utilities for content deduplication."""

import hashlib
from pathlib import Path
from typing import Union


def calculate_content_hash(content: Union[str, bytes], algorithm: str = "sha256") -> str:
    """Calculate hash of content for deduplication.

    Args:
        content: Content to hash (string or bytes)
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal hash string
    """
    if isinstance(content, str):
        content = content.encode("utf-8")

    hasher = hashlib.new(algorithm)
    hasher.update(content)

    return hasher.hexdigest()


def calculate_file_hash(file_path: Union[str, Path], algorithm: str = "sha256", chunk_size: int = 8192) -> str:
    """Calculate hash of a file.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm to use (default: sha256)
        chunk_size: Size of chunks to read (default: 8192 bytes)

    Returns:
        Hexadecimal hash string
    """
    file_path = Path(file_path)
    hasher = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()
