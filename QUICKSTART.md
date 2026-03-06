# Quick Start Guide

## What You Built

An Apify Actor that creates cryptographic proofs of data on Solana and Base blockchains. This enables:
- **Verifiable data provenance** - Prove data existed at a specific time
- **Trustless reputation** - Build immutable track records
- **Agent observability** - Create audit trails for autonomous agents
- **Compliance** - Meet regulatory requirements for data sourcing

## Project Structure

```
onchain-attestation-actor/
├── README.md              # Full documentation with use cases
├── EXAMPLE_USAGE.md       # Code examples and integration guides
├── QUICKSTART.md         # This file
├── Dockerfile            # Container configuration
├── requirements.txt      # Python dependencies
├── .actor/
│   ├── actor.json        # Actor metadata
│   └── input_schema.json # Input validation schema
├── src/
│   ├── main.py           # Entry point
│   ├── attestation/      # Core hashing and data models
│   ├── chains/           # Solana & Base adapters
│   ├── wallet/           # Wallet management
│   └── verification/     # Attestation verification
└── tests/
    └── test_hasher.py    # Unit tests
```

## Architecture Overview

### How It Works

```
INPUT (data + metadata)
    ↓
SHA-256 hash
    ↓
Sign transaction with wallet
    ↓
Write to Solana/Base
    ↓
OUTPUT (tx_hash + attestation details)
```

### Chain Implementations

**Solana:**
- Uses transaction memo field (566 bytes max)
- Cost: ~$0.0007 per attestation
- Finality: <1 second
- Perfect for: High-frequency attestations

**Base:**
- Uses transaction calldata
- Cost: ~$0.015 per attestation  
- Finality: 2-5 seconds
- Perfect for: Legal/compliance use cases

## Next Steps

### 1. Test Locally (Optional)

```bash
cd git-local/onchain-attestation-actor

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python tests/test_hasher.py
```

### 2. Set Up Wallets

You'll need:
- A Solana wallet (generate at https://solana.com or use existing)
- A Base/EVM wallet (MetaMask or similar)

**Important:** These wallets only need enough funds to pay transaction fees:
- Solana: ~0.01 SOL (~$0.50)
- Base: ~0.001 ETH (~$2.50)

### 3. Deploy to Apify

```bash
# Install Apify CLI
npm install -g apify-cli

# Login
apify login

# Push to Apify
cd git-local/onchain-attestation-actor
apify push
```

### 4. Configure Secrets

**IMPORTANT:** You must configure wallet private keys in Apify Console.

In Apify Console:
1. Go to your Actor → Settings
2. Click on "Environment Variables" tab
3. Click "Add Secret" button
4. Add these two secrets:
   - Name: `SOLANA_PRIVATE_KEY`, Value: your base58-encoded Solana private key
   - Name: `BASE_PRIVATE_KEY`, Value: your 0x-prefixed hex EVM private key

**Security Note:** 
- These are stored as encrypted secrets in Apify
- They are NOT committed to the repository
- The Actor reads them from environment variables at runtime

### 5. Test Run

In Apify Console, run with this input:

```json
{
  "chain": "solana",
  "data": {
    "test": "Hello, blockchain!",
    "timestamp": "2026-03-06T14:30:00Z"
  },
  "metadata": {
    "description": "Test attestation"
  }
}
```

You should get back a transaction hash and explorer URL. Visit the explorer URL to see your attestation on-chain!

## Use Cases by Priority

### V1 (Now)
1. **Actor developers** - Add "blockchain-verified" badge to their Actors
2. **Enterprise data buyers** - Compliance and audit trails
3. **AI agents** - Observability and accountability

### V2 (Next)
4. **DeFi protocols** - Cheap oracle alternative
5. **Journalists/Legal** - Cryptographic notarization

## Integration Examples

### From Another Actor

```python
from apify import Actor

async def main():
    async with Actor:
        data = {"your": "scraped_data"}
        
        attestation = await Actor.call(
            "your-username/onchain-attestation",
            run_input={
                "chain": "solana",
                "data": data,
                "metadata": {"description": "My data"}
            }
        )
        
        print(f"Attested! TX: {attestation['tx_hash']}")
```

### Via Webhook

Configure a webhook in Apify to auto-attest every Actor run:
1. Actor settings → Webhooks
2. Event: `ACTOR.RUN.SUCCEEDED`
3. Payload template: Point to your attestation Actor

## Monetization Strategy

Publish to Apify Store with **Pay-per-Event** pricing:
- Solana attestation: $0.01 (margin: $0.0093)
- Base attestation: $0.03 (margin: $0.015)

At 1,000 attestations/month: $10-30/month revenue  
At 10,000 attestations/month: $100-300/month revenue  
At 100,000 attestations/month: $1,000-3,000/month revenue

## Roadmap

### Phase 1: Foundation (Complete ✓)
- Solana memo attestation
- Base calldata attestation
- Verification API
- Actor integration

### Phase 2: Scale
- Batch attestations (lower per-item cost)
- Webhook auto-attestation
- Custom Solana program (queryable attestations)
- Web verification UI

### Phase 3: Ecosystem
- `blockchain-payment` Actor (accept/send crypto)
- `blockchain-watcher` Actor (monitor on-chain events)
- `blockchain-executor` Actor (execute on-chain actions)
- Token-gated attestations
- On-chain reputation system

## Support

- **Documentation:** See README.md for full details
- **Examples:** See EXAMPLE_USAGE.md for code samples
- **Issues:** File issues in your repo
- **Community:** Share on Apify Discord

## Key Insights from Our Planning

1. **Modular > Monolithic** - We built a foundational primitive, not a complete product. Other modules will compose with this.

2. **Chain-agnostic interface** - Same API for Solana and Base. Adding Ethereum/Polygon/etc is just another adapter.

3. **Off-chain data, on-chain proof** - Only hashes go on-chain (cheap), full data stays off-chain (flexible).

4. **Infrastructure play** - We're not building for one use case — we're enabling use cases we haven't imagined yet.

5. **Early but growing** - The market is early (2026), but the direction is clear. Agents need payment rails and audit trails. We're building the rails.

---

**You built v1 of blockchain infrastructure for the Actor economy. Now ship it and see what people build with it.**
