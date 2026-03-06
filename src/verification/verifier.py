"""Attestation verification utilities."""

from typing import Dict, Any, Optional
from ..attestation.schema import VerificationResult
from ..attestation.hasher import verify_hash, sha256_hash
from ..chains import SolanaAdapter


async def verify_attestation(
    tx_hash: str,
    original_data: Dict[str, Any],
    rpc_url: Optional[str] = None,
) -> VerificationResult:
    """
    Verify an attestation by comparing on-chain data with provided data.

    Args:
        tx_hash: Solana transaction signature to verify
        original_data: The original data that was attested
        rpc_url: Optional RPC URL for Solana

    Returns:
        VerificationResult with verification status
    """
    try:
        adapter = SolanaAdapter(rpc_url)

        # Hash the provided data
        expected_hash = sha256_hash(original_data)

        # Verify on-chain
        is_valid = await adapter.verify(tx_hash, expected_hash)

        # Close connection
        if hasattr(adapter, "close"):
            await adapter.close()

        if is_valid:
            return VerificationResult(
                verified=True,
                details={
                    "tx_hash": tx_hash,
                    "chain": "solana",
                    "data_hash": expected_hash,
                    "message": "Attestation verified successfully",
                },
            )
        else:
            return VerificationResult(
                verified=False,
                error="Hash mismatch or transaction not found",
                details={"tx_hash": tx_hash, "expected_hash": expected_hash},
            )

    except Exception as e:
        return VerificationResult(
            verified=False,
            error=f"Verification failed: {str(e)}",
            details={"tx_hash": tx_hash},
        )
