"""EVM wallet management for Base/Ethereum chains."""

from eth_account import Account
from typing import Optional


class EVMWallet:
    """Manages an EVM wallet for signing attestation transactions."""

    def __init__(self, private_key: Optional[str] = None):
        """
        Initialize EVM wallet.

        Args:
            private_key: 0x-prefixed hex private key. If None, generates new account.
        """
        if private_key:
            try:
                # Remove 0x prefix if present
                if private_key.startswith("0x"):
                    private_key = private_key[2:]

                # Convert to bytes
                key_bytes = bytes.fromhex(private_key)
                self.account = Account.from_key(key_bytes)
            except Exception as e:
                raise ValueError(f"Invalid EVM private key: {e}")
        else:
            # Generate new account
            self.account = Account.create()

    @property
    def address(self) -> str:
        """Get the wallet's address."""
        return self.account.address

    @property
    def private_key(self) -> str:
        """Get the private key as 0x-prefixed hex string."""
        return self.account.key.hex()

    def sign_message(self, message: str) -> str:
        """
        Sign a message with this wallet.

        Args:
            message: Message to sign

        Returns:
            Hex-encoded signature
        """
        signed_message = self.account.sign_message(message.encode("utf-8"))
        return signed_message.signature.hex()

    def __repr__(self) -> str:
        return f"EVMWallet(address={self.address})"
