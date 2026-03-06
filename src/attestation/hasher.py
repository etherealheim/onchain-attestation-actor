"""Cryptographic hashing utilities for attestations."""

import hashlib
import json
from typing import Any, Dict


def canonical_json(data: Dict[str, Any]) -> str:
    """
    Convert data to canonical JSON representation.

    This ensures that the same data always produces the same hash,
    regardless of key ordering or whitespace.

    Args:
        data: Dictionary to canonicalize

    Returns:
        Canonical JSON string
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hash(data: Dict[str, Any]) -> str:
    """
    Create SHA-256 hash of data.

    Args:
        data: Dictionary to hash

    Returns:
        Hex-encoded SHA-256 hash prefixed with 'sha256:'
    """
    canonical = canonical_json(data)
    hash_bytes = hashlib.sha256(canonical.encode("utf-8")).digest()
    hash_hex = hash_bytes.hex()
    return f"sha256:{hash_hex}"


def verify_hash(data: Dict[str, Any], expected_hash: str) -> bool:
    """
    Verify that data matches the expected hash.

    Args:
        data: Dictionary to verify
        expected_hash: Expected hash (with or without 'sha256:' prefix)

    Returns:
        True if hashes match, False otherwise
    """
    actual_hash = sha256_hash(data)

    # Remove prefix if present for comparison
    if expected_hash.startswith("sha256:"):
        expected_hash = expected_hash[7:]
    if actual_hash.startswith("sha256:"):
        actual_hash = actual_hash[7:]

    return actual_hash == expected_hash


def truncate_hash(hash_str: str, length: int = 8) -> str:
    """
    Truncate hash for display purposes.

    Args:
        hash_str: Full hash string
        length: Number of characters to keep from start and end

    Returns:
        Truncated hash like 'sha256:a1b2c3...xyz789'
    """
    if hash_str.startswith("sha256:"):
        prefix = "sha256:"
        hash_part = hash_str[7:]
    else:
        prefix = ""
        hash_part = hash_str

    if len(hash_part) <= length * 2:
        return hash_str

    return f"{prefix}{hash_part[:length]}...{hash_part[-length:]}"
