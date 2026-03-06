"""Solana wallet management."""

import base58
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from typing import Optional


class SolanaWallet:
    """Manages a Solana wallet for signing attestation transactions."""

    def __init__(self, private_key: Optional[str] = None):
        """
        Initialize Solana wallet.

        Args:
            private_key: Base58-encoded private key. If None, generates new keypair.
        """
        if private_key:
            try:
                # Decode base58 private key
                decoded = base58.b58decode(private_key)
                self.keypair = Keypair.from_bytes(decoded)
            except Exception as e:
                raise ValueError(f"Invalid Solana private key: {e}")
        else:
            # Generate new keypair
            self.keypair = Keypair()

    @property
    def public_key(self) -> str:
        """Get the wallet's public key as a string."""
        return str(self.keypair.pubkey())

    @property
    def address(self) -> str:
        """Alias for public_key."""
        return self.public_key

    def to_bytes(self) -> bytes:
        """Get the keypair as bytes (for signing)."""
        return bytes(self.keypair)

    def __repr__(self) -> str:
        return f"SolanaWallet(address={self.address})"
