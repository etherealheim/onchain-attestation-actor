"""Attestation verification utilities."""

from typing import Dict, Any, Optional
from ..attestation.schema import VerificationResult, AttestationOutput
from ..attestation.hasher import verify_hash
from ..chains import SolanaAdapter, BaseAdapter


async def verify_attestation(
    tx_hash: str,
    chain: str,
    original_data: Dict[str, Any],
    rpc_url: Optional[str] = None,
) -> VerificationResult:
    """
    Verify an attestation by comparing on-chain data with provided data.

    Args:
        tx_hash: Transaction hash to verify
        chain: Blockchain ("solana" or "base")
        original_data: The original data that was attested
        rpc_url: Optional RPC URL for the chain

    Returns:
        VerificationResult with verification status
    """
    try:
        # Select appropriate adapter
        if chain == "solana":
            adapter = SolanaAdapter(rpc_url)
        elif chain == "base":
            adapter = BaseAdapter(rpc_url)
        else:
            return VerificationResult(
                verified=False, error=f"Unsupported chain: {chain}"
            )

        # Hash the provided data
        from ..attestation.hasher import sha256_hash

        expected_hash = sha256_hash(original_data)

        # Verify on-chain
        is_valid = await adapter.verify(tx_hash, expected_hash)

        # Close connection if adapter has close method (Solana)
        if hasattr(adapter, "close"):
            await adapter.close()

        if is_valid:
            return VerificationResult(
                verified=True,
                details={
                    "tx_hash": tx_hash,
                    "chain": chain,
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
            details={"tx_hash": tx_hash, "chain": chain},
        )
