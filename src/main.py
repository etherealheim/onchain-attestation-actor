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
    if not token:
        token = os.getenv("APIFY_TOKEN")

    if not token:
        raise ValueError("APIFY_TOKEN is required to fetch run data")

    url = f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params={"token": token}, timeout=30.0)
        response.raise_for_status()
        return response.json()


async def fetch_actor_info(actor_id: str, token: str = None) -> dict:
    """Fetch Actor details (name, description) from Apify API."""
    if not token:
        token = os.getenv("APIFY_TOKEN")

    if not token:
        return {}  # Return empty if no token - origin will be unknown

    url = f"https://api.apify.com/v2/acts/{actor_id}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params={"token": token}, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            return {
                "name": data.get("name"),  # e.g., "instagram-scraper"
                "username": data.get("username"),  # e.g., "apify"
                "title": data.get("title"),  # e.g., "Instagram Scraper"
                "description": data.get("description"),
                "full_name": f"{data.get('username', 'unknown')}/{data.get('name', 'unknown')}",
            }
    except Exception:
        return {}  # Fail silently - origin will just be unknown


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

                # Extract useful context from resource
                default_dataset_id = resource.get("defaultDatasetId")
                build_number = resource.get("buildNumber")
                started_at = resource.get("startedAt")
                finished_at = resource.get("finishedAt")
                status = resource.get("status")

                # Get stats if available
                stats = resource.get("stats", {})
                item_count = stats.get("outputItems") or stats.get("datasetItems", 0)

                Actor.log.info(f"Source Actor: {source_actor_id}, Run: {source_run_id}")

                # Fetch Actor info to get human-readable name (origin/provenance)
                actor_info = await fetch_actor_info(source_actor_id)
                origin = actor_info.get("full_name", "unknown")
                actor_title = actor_info.get("title")

                Actor.log.info(f"Data origin: {origin} ({actor_title or 'no title'})")

                # Fetch the actual data from the source run
                data = await fetch_actor_run_data(source_run_id)

                # Count items if not from stats
                if not item_count and isinstance(data, list):
                    item_count = len(data)

                Actor.log.info(f"Fetched {item_count} items from source run")

                # Build comprehensive metadata for on-chain record
                data_url = (
                    f"https://api.apify.com/v2/datasets/{default_dataset_id}/items"
                    if default_dataset_id
                    else None
                )

                # Auto-populate metadata with useful context
                actor_input["run_id"] = source_run_id
                actor_input["origin"] = origin  # e.g., "apify/instagram-scraper"
                actor_input["actor_id"] = source_actor_id
                if data_url:
                    actor_input["data_url"] = data_url
                if item_count:
                    actor_input["item_count"] = item_count

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

            # Build metadata - prioritize useful, verifiable info
            metadata = {}

            # Origin/provenance - where did this data come from?
            # e.g., "apify/instagram-scraper" - human-readable Actor name
            if actor_input.get("origin"):
                metadata["origin"] = actor_input["origin"]

            # Data URL - allows anyone to verify the attestation
            if actor_input.get("data_url"):
                metadata["data"] = actor_input["data_url"]

            # Item count provides context
            if actor_input.get("item_count"):
                metadata["items"] = actor_input["item_count"]

            # Source URL if provided (for direct input mode)
            if actor_input.get("source_url"):
                metadata["src"] = actor_input["source_url"]

            # Run reference for traceability
            if actor_input.get("run_id"):
                metadata["run"] = actor_input["run_id"]

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
