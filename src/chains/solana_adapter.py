"""Solana blockchain adapter using memo-based attestations."""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.transaction import Transaction
from solders.message import Message
from solders.instruction import Instruction, AccountMeta
from solders.system_program import TransferParams, transfer
from solders.pubkey import Pubkey

from .base_chain import ChainAdapter
from ..attestation.schema import AttestationOutput, CostInfo, VerificationInfo
from ..wallet.solana_wallet import SolanaWallet


# Memo program ID
MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")


class SolanaAdapter(ChainAdapter):
    """Solana attestation adapter using transaction memos."""

    def __init__(self, rpc_url: Optional[str] = None):
        """
        Initialize Solana adapter.

        Args:
            rpc_url: Solana RPC endpoint (defaults to public mainnet)
        """
        super().__init__(rpc_url or "https://api.mainnet-beta.solana.com")
        self.client = AsyncClient(self.rpc_url)

    async def attest(
        self, data_hash: str, metadata: Dict[str, Any], wallet: SolanaWallet
    ) -> AttestationOutput:
        """
        Create an attestation on Solana using a memo instruction.

        The attestation data is stored in the transaction memo field.
        Structure: {"hash": "sha256:...", "metadata": {...}, "timestamp": "..."}

        Args:
            data_hash: SHA-256 hash of the data
            metadata: Additional metadata
            wallet: SolanaWallet for signing

        Returns:
            AttestationOutput with transaction details
        """
        # Create attestation payload
        attestation_data = {
            "hash": data_hash,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "attestor": wallet.address,
        }

        # Convert to JSON (limited to 566 bytes for memo)
        memo_text = json.dumps(attestation_data, separators=(",", ":"))

        if len(memo_text.encode("utf-8")) > 566:
            # Truncate metadata if too large
            simplified = {
                "hash": data_hash,
                "timestamp": attestation_data["timestamp"],
                "attestor": wallet.address,
            }
            memo_text = json.dumps(simplified, separators=(",", ":"))

        # Create memo instruction
        memo_instruction = Instruction(
            program_id=MEMO_PROGRAM_ID, accounts=[], data=memo_text.encode("utf-8")
        )

        # Get recent blockhash
        blockhash_resp = await self.client.get_latest_blockhash(Confirmed)
        recent_blockhash = blockhash_resp.value.blockhash

        # Create and sign transaction
        message = Message.new_with_blockhash(
            [memo_instruction], wallet.keypair.pubkey(), recent_blockhash
        )
        transaction = Transaction([wallet.keypair], message, recent_blockhash)

        # Send transaction
        try:
            result = await self.client.send_transaction(transaction)
            tx_signature = str(result.value)

            # Wait for confirmation
            await self.client.confirm_transaction(tx_signature, Confirmed)

            # Get transaction details for block number
            tx_info = await self.client.get_transaction(tx_signature, Confirmed)
            block_number = tx_info.value.slot if tx_info.value else None

        except Exception as e:
            raise RuntimeError(f"Failed to send Solana transaction: {e}")

        # Generate attestation ID
        attestation_id = f"att_{uuid.uuid4().hex[:12]}"

        # Create output
        return AttestationOutput(
            attestation_id=attestation_id,
            chain="solana",
            tx_hash=tx_signature,
            explorer_url=self.get_explorer_url(tx_signature),
            data_hash=data_hash,
            attestor_address=wallet.address,
            timestamp=attestation_data["timestamp"],
            block_number=block_number,
            verification=VerificationInfo(),
            cost=self.estimate_cost(),
            metadata=metadata,
        )

    async def verify(self, tx_hash: str, expected_hash: str) -> bool:
        """
        Verify a Solana attestation.

        Args:
            tx_hash: Transaction signature
            expected_hash: Expected data hash

        Returns:
            True if attestation exists and hash matches
        """
        try:
            tx_info = await self.client.get_transaction(tx_hash, Confirmed)

            if not tx_info.value:
                return False

            # Extract memo from transaction
            transaction = tx_info.value.transaction

            # Look for memo in instructions
            for instruction in transaction.message.instructions:
                if str(instruction.program_id) == str(MEMO_PROGRAM_ID):
                    memo_data = bytes(instruction.data).decode("utf-8")
                    attestation = json.loads(memo_data)

                    stored_hash = attestation.get("hash", "")

                    # Compare hashes (remove prefix if present)
                    if expected_hash.startswith("sha256:"):
                        expected_hash = expected_hash[7:]
                    if stored_hash.startswith("sha256:"):
                        stored_hash = stored_hash[7:]

                    return stored_hash == expected_hash

            return False

        except Exception as e:
            raise RuntimeError(f"Failed to verify Solana attestation: {e}")

    def get_explorer_url(self, tx_hash: str) -> str:
        """Get Solscan explorer URL."""
        return f"https://solscan.io/tx/{tx_hash}"

    def estimate_cost(self) -> CostInfo:
        """
        Estimate cost of Solana attestation.

        Solana transactions cost ~5000 lamports (0.000005 SOL).
        At $50 per SOL, that's ~$0.00025, but we round up for safety.
        """
        return CostInfo(chain_fee_usd=0.0007, token="SOL", amount=0.000005)

    async def close(self):
        """Close the RPC client connection."""
        await self.client.close()
