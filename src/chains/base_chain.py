"""Base interface for blockchain adapters."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..attestation.schema import AttestationOutput, CostInfo


class ChainAdapter(ABC):
    """Abstract base class for blockchain attestation adapters."""

    def __init__(self, rpc_url: Optional[str] = None):
        """
        Initialize chain adapter.

        Args:
            rpc_url: RPC endpoint URL (uses default if None)
        """
        self.rpc_url = rpc_url

    @abstractmethod
    async def attest(
        self, data_hash: str, metadata: Dict[str, Any], wallet: Any
    ) -> AttestationOutput:
        """
        Create an on-chain attestation.

        Args:
            data_hash: SHA-256 hash of the data to attest
            metadata: Additional metadata to include
            wallet: Wallet object for signing

        Returns:
            AttestationOutput with transaction details
        """
        pass

    @abstractmethod
    async def verify(self, tx_hash: str, expected_hash: str) -> bool:
        """
        Verify an attestation by transaction hash.

        Args:
            tx_hash: Transaction hash to verify
            expected_hash: Expected data hash

        Returns:
            True if attestation is valid and matches expected hash
        """
        pass

    @abstractmethod
    def get_explorer_url(self, tx_hash: str) -> str:
        """
        Get block explorer URL for a transaction.

        Args:
            tx_hash: Transaction hash

        Returns:
            URL to view transaction on block explorer
        """
        pass

    @abstractmethod
    def estimate_cost(self) -> CostInfo:
        """
        Estimate the cost of creating an attestation.

        Returns:
            CostInfo with estimated fees
        """
        pass
