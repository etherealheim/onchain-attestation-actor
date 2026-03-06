"""Main entry point for the on-chain attestation Actor."""

import os
from apify import Actor
from attestation import sha256_hash
from chains import SolanaAdapter, BaseAdapter
from wallet import SolanaWallet, EVMWallet
from verification import verify_attestation


async def main():
    """Main Actor execution function."""
    async with Actor:
        # Get Actor input
        actor_input = await Actor.get_input() or {}
        Actor.log.info(f"Received input keys: {list(actor_input.keys())}")

        try:
            # Extract required fields
            chain = actor_input.get("chain", "solana")
            data = actor_input.get("data", {})

            if not data:
                raise ValueError("'data' field is required")

            # Check if this is a verification request
            verify_mode = actor_input.get("verify_mode", False)

            if verify_mode:
                tx_hash = actor_input.get("tx_hash")
                Actor.log.info(f"Verifying attestation: {tx_hash}")

                if not tx_hash:
                    raise ValueError("tx_hash is required for verification mode")

                result = await verify_attestation(
                    tx_hash=tx_hash,
                    chain=chain,
                    original_data=data,
                    rpc_url=os.getenv(f"{chain.upper()}_RPC_URL"),
                )

                await Actor.push_data(result.dict())
                Actor.log.info(f"Verification complete: {result.verified}")
                return

            # Create attestation mode
            Actor.log.info(f"Creating attestation on {chain}")

            # Hash the data
            data_hash = sha256_hash(data)
            Actor.log.info(f"Data hash: {data_hash}")

            # Build metadata from flat input structure
            metadata = {}
            if actor_input.get("actor_id"):
                metadata["actor_id"] = actor_input["actor_id"]
            if actor_input.get("run_id"):
                metadata["run_id"] = actor_input["run_id"]
            if actor_input.get("source_url"):
                metadata["source_url"] = actor_input["source_url"]
            if actor_input.get("description"):
                metadata["description"] = actor_input["description"]
            if actor_input.get("custom_metadata"):
                metadata["custom"] = actor_input["custom_metadata"]

            # Get wallet credentials from environment
            if chain == "solana":
                private_key = os.getenv("SOLANA_PRIVATE_KEY")
                if not private_key:
                    raise ValueError(
                        "SOLANA_PRIVATE_KEY environment variable is required. Please set it in Actor Settings → Environment Variables."
                    )

                wallet = SolanaWallet(private_key)
                rpc_url = os.getenv("SOLANA_RPC_URL")
                adapter = SolanaAdapter(rpc_url)

                Actor.log.info(f"Using Solana wallet: {wallet.address}")

            elif chain == "base":
                private_key = os.getenv("BASE_PRIVATE_KEY")
                if not private_key:
                    raise ValueError(
                        "BASE_PRIVATE_KEY environment variable is required. Please set it in Actor Settings → Environment Variables."
                    )

                wallet = EVMWallet(private_key)
                rpc_url = os.getenv("BASE_RPC_URL")
                adapter = BaseAdapter(rpc_url)

                Actor.log.info(f"Using Base wallet: {wallet.address}")

            else:
                raise ValueError(
                    f"Unsupported chain: {chain}. Must be 'solana' or 'base'."
                )

            # Create attestation
            Actor.log.info("Submitting attestation to blockchain...")
            attestation = await adapter.attest(data_hash, metadata, wallet)

            # Close connection if adapter has close method (Solana)
            if hasattr(adapter, "close"):
                await adapter.close()

            Actor.log.info(f"✅ Attestation created: {attestation.tx_hash}")
            Actor.log.info(f"🔗 Explorer URL: {attestation.explorer_url}")

            # Store full data in Apify key-value store if requested
            store_full_data = actor_input.get("store_full_data", True)
            if store_full_data:
                await Actor.set_value(
                    f"attestation_{attestation.attestation_id}",
                    {"data": data, "attestation": attestation.dict()},
                )

                # Add URL to output
                attestation.apify_data_url = (
                    f"https://api.apify.com/v2/key-value-stores/"
                    f"{Actor.get_env().get('default_key_value_store_id')}"
                    f"/records/attestation_{attestation.attestation_id}"
                )

            # Output the attestation
            await Actor.push_data(attestation.dict())

            Actor.log.info("🎉 Attestation complete!")

        except Exception as e:
            Actor.log.error(f"❌ Error: {str(e)}")
            await Actor.fail(status_message=str(e))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
