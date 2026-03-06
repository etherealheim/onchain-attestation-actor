"""Base blockchain adapter using Ethereum Attestation Service (EAS)."""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from web3 import Web3
from eth_account.signers.local import LocalAccount

from .base_chain import ChainAdapter
from ..attestation.schema import AttestationOutput, CostInfo, VerificationInfo
from ..wallet.evm_wallet import EVMWallet


# EAS contract addresses on Base mainnet
EAS_CONTRACT_ADDRESS = "0x4200000000000000000000000000000000000021"
SCHEMA_REGISTRY_ADDRESS = "0x4200000000000000000000000000000000000020"

# Schema UID for data attestations (you would create this on EAS)
# For v1, we'll use a simple schema: string dataHash, string metadata
DATA_ATTESTATION_SCHEMA_UID = (
    "0x0000000000000000000000000000000000000000000000000000000000000000"
)


class BaseAdapter(ChainAdapter):
    """Base (EVM) attestation adapter using EAS."""

    def __init__(self, rpc_url: Optional[str] = None):
        """
        Initialize Base adapter.

        Args:
            rpc_url: Base RPC endpoint (defaults to public mainnet)
        """
        super().__init__(rpc_url or "https://mainnet.base.org")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        # EAS contract ABI (simplified - just the attest function)
        self.eas_abi = [
            {
                "inputs": [
                    {
                        "components": [
                            {"name": "schema", "type": "bytes32"},
                            {"name": "data", "type": "bytes"},
                        ],
                        "name": "request",
                        "type": "tuple",
                    }
                ],
                "name": "attest",
                "outputs": [{"name": "", "type": "bytes32"}],
                "stateMutability": "payable",
                "type": "function",
            }
        ]

        self.eas_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(EAS_CONTRACT_ADDRESS), abi=self.eas_abi
        )

    async def attest(
        self, data_hash: str, metadata: Dict[str, Any], wallet: EVMWallet
    ) -> AttestationOutput:
        """
        Create an attestation on Base using EAS.

        Args:
            data_hash: SHA-256 hash of the data
            metadata: Additional metadata
            wallet: EVMWallet for signing

        Returns:
            AttestationOutput with transaction details
        """
        # For v1, we'll use a simpler approach: just submit a transaction with
        # attestation data in the calldata/input field rather than full EAS integration
        # This keeps it simple while still being verifiable on-chain

        timestamp = datetime.utcnow().isoformat() + "Z"

        # Create attestation payload as JSON
        import json

        attestation_data = {
            "hash": data_hash,
            "metadata": metadata,
            "timestamp": timestamp,
            "attestor": wallet.address,
        }
        data_bytes = json.dumps(attestation_data).encode("utf-8")

        # Create transaction with data in calldata
        nonce = self.w3.eth.get_transaction_count(wallet.address)

        # Simple transaction with data
        tx = {
            "nonce": nonce,
            "to": wallet.address,  # Send to self with data
            "value": 0,
            "gas": 100000,
            "gasPrice": self.w3.eth.gas_price,
            "data": "0x" + data_bytes.hex(),
            "chainId": 8453,  # Base mainnet
        }

        # Sign and send transaction
        try:
            signed_tx = self.w3.eth.account.sign_transaction(tx, wallet.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            block_number = receipt["blockNumber"]

        except Exception as e:
            raise RuntimeError(f"Failed to send Base transaction: {e}")

        # Generate attestation ID
        attestation_id = f"att_{uuid.uuid4().hex[:12]}"

        return AttestationOutput(
            attestation_id=attestation_id,
            chain="base",
            tx_hash=tx_hash_hex,
            explorer_url=self.get_explorer_url(tx_hash_hex),
            data_hash=data_hash,
            attestor_address=wallet.address,
            timestamp=timestamp,
            block_number=block_number,
            verification=VerificationInfo(),
            cost=self.estimate_cost(),
            metadata=metadata,
        )

    async def verify(self, tx_hash: str, expected_hash: str) -> bool:
        """
        Verify a Base attestation.

        Args:
            tx_hash: Transaction hash
            expected_hash: Expected data hash

        Returns:
            True if attestation exists and hash matches
        """
        try:
            tx = self.w3.eth.get_transaction(tx_hash)

            if not tx:
                return False

            # Extract data from transaction input
            data_hex = tx["input"]
            if data_hex.startswith("0x"):
                data_hex = data_hex[2:]

            data_bytes = bytes.fromhex(data_hex)

            import json

            attestation = json.loads(data_bytes.decode("utf-8"))

            stored_hash = attestation.get("hash", "")

            # Compare hashes
            if expected_hash.startswith("sha256:"):
                expected_hash = expected_hash[7:]
            if stored_hash.startswith("sha256:"):
                stored_hash = stored_hash[7:]

            return stored_hash == expected_hash

        except Exception as e:
            raise RuntimeError(f"Failed to verify Base attestation: {e}")

    def get_explorer_url(self, tx_hash: str) -> str:
        """Get BaseScan explorer URL."""
        return f"https://basescan.org/tx/{tx_hash}"

    def estimate_cost(self) -> CostInfo:
        """
        Estimate cost of Base attestation.

        Base transactions typically cost 0.0001-0.001 ETH depending on gas price.
        At $2500 per ETH, that's roughly $0.25-2.50, but usually on the lower end.
        """
        return CostInfo(
            chain_fee_usd=0.015,
            token="ETH",
            amount=0.000006,  # ~6 gwei * 100k gas
        )
