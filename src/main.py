"""Main entry point for the on-chain attestation Actor."""

import os
from apify import Actor
from attestation import AttestationInput, sha256_hash
from chains import SolanaAdapter, BaseAdapter
from wallet import SolanaWallet, EVMWallet
from verification import verify_attestation


async def main():
    """Main Actor execution function."""
    async with Actor:
        # Get Actor input
        actor_input = await Actor.get_input() or {}
        Actor.log.info(f"Received input: {actor_input}")

        try:
            # Parse and validate input
            input_data = AttestationInput(**actor_input)

            # Check if this is a verification request
            if input_data.verify:
                Actor.log.info(f"Verifying attestation: {input_data.tx_hash}")

                if not input_data.tx_hash:
                    raise ValueError("tx_hash is required for verification")

                result = await verify_attestation(
                    tx_hash=input_data.tx_hash,
                    chain=input_data.chain,
                    original_data=input_data.data,
                    rpc_url=os.getenv(f"{input_data.chain.upper()}_RPC_URL"),
                )

                await Actor.push_data(result.dict())
                Actor.log.info(f"Verification complete: {result.verified}")
                return

            # Create attestation mode
            Actor.log.info(f"Creating attestation on {input_data.chain}")

            # Hash the data
            data_hash = sha256_hash(input_data.data)
            Actor.log.info(f"Data hash: {data_hash}")

            # Prepare metadata
            metadata = input_data.metadata.dict() if input_data.metadata else {}

            # Get wallet credentials from environment
            if input_data.chain == "solana":
                private_key = os.getenv("SOLANA_PRIVATE_KEY")
                if not private_key:
                    raise ValueError(
                        "SOLANA_PRIVATE_KEY environment variable is required"
                    )

                wallet = SolanaWallet(private_key)
                rpc_url = os.getenv("SOLANA_RPC_URL")
                adapter = SolanaAdapter(rpc_url)

                Actor.log.info(f"Using Solana wallet: {wallet.address}")

            elif input_data.chain == "base":
                private_key = os.getenv("BASE_PRIVATE_KEY")
                if not private_key:
                    raise ValueError(
                        "BASE_PRIVATE_KEY environment variable is required"
                    )

                wallet = EVMWallet(private_key)
                rpc_url = os.getenv("BASE_RPC_URL")
                adapter = BaseAdapter(rpc_url)

                Actor.log.info(f"Using Base wallet: {wallet.address}")

            else:
                raise ValueError(f"Unsupported chain: {input_data.chain}")

            # Create attestation
            Actor.log.info("Submitting attestation to blockchain...")
            attestation = await adapter.attest(data_hash, metadata, wallet)

            # Close Solana connection if applicable
            if input_data.chain == "solana":
                await adapter.close()

            Actor.log.info(f"Attestation created: {attestation.tx_hash}")
            Actor.log.info(f"Explorer URL: {attestation.explorer_url}")

            # Store full data in Apify key-value store if requested
            if input_data.options and input_data.options.store_full_data:
                await Actor.set_value(
                    f"attestation_{attestation.attestation_id}",
                    {"data": input_data.data, "attestation": attestation.dict()},
                )

                # Add URL to output
                attestation.apify_data_url = (
                    f"https://api.apify.com/v2/key-value-stores/"
                    f"{Actor.get_env().get('default_key_value_store_id')}"
                    f"/records/attestation_{attestation.attestation_id}"
                )

            # Output the attestation
            await Actor.push_data(attestation.dict())

            Actor.log.info("Attestation complete!")

        except Exception as e:
            Actor.log.error(f"Error: {str(e)}")
            await Actor.fail(status_message=str(e))
