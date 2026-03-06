"""Main entry point for the on-chain attestation Actor."""

import os
import httpx
from apify import Actor
from src.attestation import sha256_hash
from src.chains import SolanaAdapter
from src.wallet import SolanaWallet
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
        return {}

    url = f"https://api.apify.com/v2/acts/{actor_id}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params={"token": token}, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            return {
                "name": data.get("name"),
                "username": data.get("username"),
                "title": data.get("title"),
                "description": data.get("description"),
                "full_name": f"{data.get('username', 'unknown')}/{data.get('name', 'unknown')}",
            }
    except Exception:
        return {}


async def fetch_run_input(run_id: str, token: str = None) -> dict:
    """Fetch the input that was used for an Actor run."""
    if not token:
        token = os.getenv("APIFY_TOKEN")

    if not token:
        return {}

    url = f"https://api.apify.com/v2/actor-runs/{run_id}/input"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params={"token": token}, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except Exception:
        return {}


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

                # Fetch the input that was used for the source run
                # This shows HOW the data was collected (e.g., which Instagram profile)
                run_input = await fetch_run_input(source_run_id)
                Actor.log.info(
                    f"Source run input keys: {list(run_input.keys()) if run_input else 'none'}"
                )

                # Fetch the actual output data from the source run
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
                if run_input:
                    actor_input["source_input"] = run_input

            else:
                # Direct input mode - data is provided directly
                data = actor_input.get("data", {})

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
                    original_data=data,
                    rpc_url=os.getenv("SOLANA_RPC_URL"),
                )

                await Actor.push_data(result.dict())
                Actor.log.info(f"Verification complete: {result.verified}")
                return

            # Create attestation mode
            Actor.log.info("Creating attestation on Solana")

            # Hash the data
            data_hash = sha256_hash(data)
            Actor.log.info(f"Data hash: {data_hash}")

            # Check privacy mode - default is private (only hash on-chain)
            private_mode = actor_input.get("private_mode", True)
            Actor.log.info(
                f"Privacy mode: {'PRIVATE (hash only)' if private_mode else 'PUBLIC (full metadata)'}"
            )

            # Build PRIVATE metadata (stored in Apify, not on-chain)
            private_metadata = {}

            # Origin/provenance
            if actor_input.get("origin"):
                private_metadata["origin"] = actor_input["origin"]

            # Source input details
            source_input = actor_input.get("source_input")
            if source_input:
                input_hash = sha256_hash(source_input)
                private_metadata["inputHash"] = input_hash
                private_metadata["input"] = source_input  # Full input stored privately

                # Extract target field
                target_fields = [
                    "username",
                    "usernames",
                    "url",
                    "urls",
                    "startUrls",
                    "searchQuery",
                    "search",
                    "query",
                    "hashtag",
                    "hashtags",
                    "profileUrl",
                    "profileUrls",
                ]

                for field in target_fields:
                    if field in source_input and source_input[field]:
                        value = source_input[field]
                        if isinstance(value, list):
                            value = value[:3]
                            if len(value) == 1:
                                value = value[0]
                        if isinstance(value, str) and len(value) > 100:
                            value = value[:97] + "..."
                        private_metadata["target"] = value
                        break

            # Data URL
            if actor_input.get("data_url"):
                private_metadata["dataUrl"] = actor_input["data_url"]

            # Item count
            if actor_input.get("item_count"):
                private_metadata["items"] = actor_input["item_count"]

            # Run ID
            if actor_input.get("run_id"):
                private_metadata["runId"] = actor_input["run_id"]

            # Build ON-CHAIN metadata (what goes to blockchain)
            if private_mode:
                # PRIVATE: Only hash goes on-chain, nothing else
                onchain_metadata = {}
            else:
                # PUBLIC: Include origin, target, data URL on-chain
                onchain_metadata = {}
                if private_metadata.get("origin"):
                    onchain_metadata["origin"] = private_metadata["origin"]
                if private_metadata.get("target"):
                    onchain_metadata["target"] = private_metadata["target"]
                if private_metadata.get("dataUrl"):
                    onchain_metadata["data"] = private_metadata["dataUrl"]
                if private_metadata.get("items"):
                    onchain_metadata["items"] = private_metadata["items"]
                if private_metadata.get("runId"):
                    onchain_metadata["run"] = private_metadata["runId"]

            # Get wallet credentials from input (with fallback to environment variables)
            private_key = actor_input.get("solana_private_key") or os.getenv(
                "SOLANA_PRIVATE_KEY"
            )
            if not private_key:
                raise ValueError(
                    "Solana private key is required. Please provide 'solana_private_key' in the input."
                )

            wallet = SolanaWallet(private_key)
            rpc_url = actor_input.get("solana_rpc_url") or os.getenv("SOLANA_RPC_URL")
            adapter = SolanaAdapter(rpc_url)

            Actor.log.info(f"Using Solana wallet: {wallet.address}")

            # Create attestation
            Actor.log.info("Submitting attestation to blockchain...")
            attestation = await adapter.attest(data_hash, onchain_metadata, wallet)

            # Close connection if adapter has close method (Solana)
            if hasattr(adapter, "close"):
                await adapter.close()

            Actor.log.info(f"✅ Attestation created: {attestation.tx_hash}")
            Actor.log.info(f"🔗 Explorer URL: {attestation.explorer_url}")

            # Store data in Apify key-value store
            store_full_data = actor_input.get("store_full_data", True)
            if store_full_data:
                # Build the stored record with PRIVATE metadata
                # This is what you share with buyers/auditors for verification
                stored_record = {
                    "attestation_id": attestation.attestation_id,
                    "tx_hash": attestation.tx_hash,
                    "chain": "solana",
                    "explorer_url": attestation.explorer_url,
                    "data_hash": data_hash,
                    "timestamp": attestation.timestamp,
                    "attestor": attestation.attestor_address,
                    # Private metadata (not on blockchain)
                    "private_metadata": private_metadata,
                    # The actual data
                    "data": data,
                    # What mode was used
                    "private_mode": private_mode,
                }

                await Actor.set_value(
                    f"attestation_{attestation.attestation_id}",
                    stored_record,
                )

                # Add URL to output
                kv_store_id = Actor.get_env().get("default_key_value_store_id")
                attestation.apify_data_url = (
                    f"https://api.apify.com/v2/key-value-stores/"
                    f"{kv_store_id}"
                    f"/records/attestation_{attestation.attestation_id}"
                )

                Actor.log.info(
                    f"📦 Stored private record: attestation_{attestation.attestation_id}"
                )

            # Build output - include private metadata summary for the user
            output = attestation.dict()
            output["private_mode"] = private_mode
            output["private_metadata"] = private_metadata

            # Output the attestation
            await Actor.push_data(output)

            if private_mode:
                Actor.log.info(
                    "🔒 PRIVATE attestation complete - only hash is on-chain"
                )
                Actor.log.info(
                    f"📋 Share attestation ID with buyers: {attestation.attestation_id}"
                )
            else:
                Actor.log.info("🌐 PUBLIC attestation complete - metadata is on-chain")

        except Exception as e:
            Actor.log.error(f"❌ Error: {str(e)}")
            await Actor.fail(status_message=str(e))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
