"""Tests for utility functions."""

import pytest
from pathlib import Path
import tempfile

from aibooks.utils.hash_utils import calculate_content_hash, calculate_file_hash


def test_calculate_content_hash_string():
    """Test hashing string content."""
    content = "This is test content"
    hash1 = calculate_content_hash(content)
    hash2 = calculate_content_hash(content)

    assert hash1 == hash2  # Same content = same hash
    assert len(hash1) == 64  # SHA-256 produces 64 hex chars


def test_calculate_content_hash_bytes():
    """Test hashing bytes content."""
    content = b"Binary content"
    hash1 = calculate_content_hash(content)

    assert len(hash1) == 64


def test_calculate_content_hash_different():
    """Test different content produces different hashes."""
    hash1 = calculate_content_hash("Content 1")
    hash2 = calculate_content_hash("Content 2")

    assert hash1 != hash2


def test_calculate_file_hash():
    """Test hashing file content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Test file content")
        file_path = Path(f.name)

    try:
        hash1 = calculate_file_hash(file_path)
        hash2 = calculate_file_hash(file_path)

        assert hash1 == hash2
        assert len(hash1) == 64
    finally:
        file_path.unlink()
