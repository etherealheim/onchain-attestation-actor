"""Tests for hashing utilities."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from attestation.hasher import sha256_hash, verify_hash, canonical_json


def test_canonical_json():
    """Test that canonical JSON ordering is consistent."""
    data1 = {"b": 2, "a": 1}
    data2 = {"a": 1, "b": 2}

    assert canonical_json(data1) == canonical_json(data2)
    assert canonical_json(data1) == '{"a":1,"b":2}'


def test_sha256_hash():
    """Test SHA-256 hashing."""
    data = {"test": "data", "number": 42}
    hash1 = sha256_hash(data)
    hash2 = sha256_hash(data)

    # Same data should produce same hash
    assert hash1 == hash2

    # Hash should start with prefix
    assert hash1.startswith("sha256:")

    # Different data should produce different hash
    different_data = {"test": "different", "number": 42}
    hash3 = sha256_hash(different_data)
    assert hash1 != hash3


def test_verify_hash():
    """Test hash verification."""
    data = {"test": "data"}
    hash_val = sha256_hash(data)

    # Should verify correctly
    assert verify_hash(data, hash_val) is True

    # Should work with or without prefix
    hash_without_prefix = hash_val[7:]  # Remove "sha256:"
    assert verify_hash(data, hash_without_prefix) is True

    # Should fail for wrong data
    wrong_data = {"test": "wrong"}
    assert verify_hash(wrong_data, hash_val) is False


if __name__ == "__main__":
    test_canonical_json()
    test_sha256_hash()
    test_verify_hash()
    print("✓ All tests passed!")
