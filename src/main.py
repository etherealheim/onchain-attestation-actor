"""Main entry point for the on-chain attestation Actor."""

import os
import httpx
from apify import Actor
from src.attestation import sha256_hash
from src.chains import SolanaAdapter, BaseAdapter
from src.wallet import SolanaWallet, EVMWallet
from src.verification import verify_attestation


async def fetch_actor_run_data(run_id: str, token: str = None) -> dict:
    """Fetch the output data from an Actor run."""
    # Try to get token from environment if not provided
    if not token:
        token = os.getenv("APIFY_TOKEN")

    if not token:
        raise ValueError("APIFY_TOKEN is required to fetch run data")

    # Fetch the dataset items from the run
    url = f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params={"token": token}, timeout=30.0)
        response.raise_for_status()
        return response.json()


async def main():
    """Main Actor execution function."""
    async with Actor:
        # Get Actor input
        actor_input = await Actor.get_input() or {}
        Actor.log.info(f"Received input keys: {list(actor_input.keys())}")

        try:
            # Check if this is a webhook payload from another Actor
            # Webhook payloads have 'resource' with run details
            resource = actor_input.get("resource", {})

            # Log the resource to help debug
            if resource:
                Actor.log.info(f"Received resource keys: {list(resource.keys())}")

            # Check various possible field names for run ID
            source_run_id = (
                resource.get("actorRunId")
                or resource.get("id")
                or resource.get("runId")
            )

            if resource and source_run_id:
                Actor.log.info("Detected webhook payload from another Actor")

                source_actor_id = (
                    resource.get("actId")
                    or resource.get("actorId")
                    or resource.get("actorTaskId")
                )

                Actor.log.info(f"Source Actor: {source_actor_id}, Run: {source_run_id}")

                # Fetch the actual data from the source run
                # APIFY_TOKEN is automatically available when running on Apify platform
                data = await fetch_actor_run_data(source_run_id)

                Actor.log.info(
                    f"Fetched {len(data) if isinstance(data, list) else 1} items from source run"
                )

                # Auto-populate metadata from webhook
                if not actor_input.get("actor_id"):
                    actor_input["actor_id"] = source_actor_id
                if not actor_input.get("run_id"):
                    actor_input["run_id"] = source_run_id

            else:
                # Direct input mode - data is provided directly
                data = actor_input.get("data", {})

            # Extract required fields
            chain = actor_input.get("chain", "solana")

            if not data:
                raise ValueError(
                    "'data' field is required (or webhook payload with run data)"
                )

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

            # Get wallet credentials from input (with fallback to environment variables)
            if chain == "solana":
                private_key = actor_input.get("solana_private_key") or os.getenv(
                    "SOLANA_PRIVATE_KEY"
                )
                if not private_key:
                    raise ValueError(
                        "Solana private key is required. Please provide 'solana_private_key' in the input."
                    )

                wallet = SolanaWallet(private_key)
                rpc_url = actor_input.get("solana_rpc_url") or os.getenv(
                    "SOLANA_RPC_URL"
                )
                adapter = SolanaAdapter(rpc_url)

                Actor.log.info(f"Using Solana wallet: {wallet.address}")

            elif chain == "base":
                private_key = actor_input.get("base_private_key") or os.getenv(
                    "BASE_PRIVATE_KEY"
                )
                if not private_key:
                    raise ValueError(
                        "Base private key is required. Please provide 'base_private_key' in the input."
                    )

                wallet = EVMWallet(private_key)
                rpc_url = actor_input.get("base_rpc_url") or os.getenv("BASE_RPC_URL")
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
