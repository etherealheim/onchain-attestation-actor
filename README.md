# On-Chain Attestation Actor

A modular Apify Actor that provides blockchain-based attestation services for any data, Actor run, or workflow. Creates cryptographic proofs on Solana and Base that data existed at a specific time with specific content — immutable, verifiable, and trustless.

## What It Does

Takes any JSON data and writes a cryptographic proof (hash + metadata) to either Solana or Base blockchain. This creates an immutable, timestamped record that proves:
- The data existed at a specific time
- The data hasn't been tampered with
- A specific Actor/agent produced this data

**Key Features:**
- ✅ Multi-chain support (Solana via Memo, Base via EAS)
- ✅ Cryptographic verification (SHA-256 hashing)
- ✅ Ultra-low cost (~$0.001 per attestation)
- ✅ Easy integration (one Actor.call())
- ✅ Verification API included
- ✅ No custom smart contracts needed for v1

## Use Cases by Persona

### 1. Apify Actor Developer (Data Provider)

**Who:** Someone who builds and publishes scraping Actors on the Apify Store.

**Problem:** Their scraped data has no proof of authenticity. A buyer can't verify that the data actually came from the claimed source at the claimed time. Competing Actors might fabricate results.

**How they use it:**
- Add `blockchain-attestation` as a post-run step in their Actor
- Every scraping run produces a tx hash that proves: "This exact data was produced by this Actor at this time"
- They advertise "blockchain-verified results" on their Store listing — a differentiator

**Value prop:** Trust/differentiation. "My data is verifiable. My competitor's isn't."

**Example:**
```python
# Inside your scraping Actor
from apify import Actor

async def main():
    results = await scrape_amazon_products()
    
    # Attest the results on-chain
    attestation = await Actor.call(
        "username/onchain-attestation",
        run_input={
            "chain": "solana",
            "data": results,
            "metadata": {
                "source": "amazon.com",
                "scrape_type": "product_pricing",
                "item_count": len(results),
            },
        },
    )
    # Returns: tx_hash, explorer_url, data_hash, attestation_id
```

---

### 2. Data Buyer / Enterprise Consumer

**Who:** Companies that buy scraped data for business intelligence, market research, competitive analysis, compliance monitoring.

**Problem:** They can't prove to auditors, lawyers, or regulators where their data came from. "We scraped this from Amazon on March 6, 2026" — says who?

**How they use it:**
- They require their data providers (Actor developers) to use attestation
- They store the tx hashes alongside the data in their systems
- When audited, they can prove the provenance chain: data → hash → on-chain proof → timestamp

**Value prop:** Compliance and audit trail. Especially relevant for:
- **Financial services** (market data provenance for trading decisions)
- **Legal/e-discovery** (proving web content existed at a specific time)
- **Insurance** (proving claim-related web content)
- **AI/ML companies** (proving training data sources for regulatory compliance)

**Example verification:**
```bash
curl -X POST https://api.apify.com/v2/acts/username/onchain-attestation/runs \
  -d '{
    "verify": true,
    "tx_hash": "5xYzAbC...",
    "chain": "solana",
    "original_data": {...}
  }'
# Returns: { "verified": true, "attestation": {...} }
```

---

### 3. AI Agent / Autonomous System

**Who:** An AI agent (built on LangGraph, CrewAI, AutoGPT, etc.) that calls Apify Actors as tools.

**Problem:** The agent chains multiple tools together. If something goes wrong downstream, there's no way to audit which tool produced which output and when. The agent's decision trail is opaque.

**How they use it:**
- The agent calls `blockchain-attestation` after each significant step
- Creates a verifiable, immutable audit trail of the agent's entire workflow
- If the agent makes a bad decision, you can trace back: "At step 3, Actor X produced this data (verified on-chain), and the LLM interpreted it as Y"

**Value prop:** Agent observability and accountability. As agents become more autonomous, proving what they did and why becomes critical.

**Example agent workflow:**
```
Agent Task: "Research competitor pricing and adjust our prices"

Step 1: Scrape competitor prices (Actor A) → attest results
Step 2: Analyze pricing trends (LLM) → attest analysis
Step 3: Generate new prices (LLM) → attest recommendations  
Step 4: Update pricing system (API call) → attest action taken

Full audit trail: 4 on-chain attestations, each verifiable
```

---

### 4. DeFi Protocol / Crypto Project

**Who:** DeFi protocols, DAOs, or crypto projects that need off-chain data on-chain.

**Problem:** They need "oracle-like" data — real-world information verified and available on-chain — but building a custom oracle is expensive and complex.

**How they use it:**
- Use Apify Actors to scrape real-world data (prices, events, stats)
- Attest the scraped data on-chain
- Smart contracts or other agents can reference the attestation as a lightweight proof

**Example use cases:**
- **Prediction markets:** Scrape sports results → attest on-chain → resolve bets
- **Insurance protocols:** Scrape weather data → attest → trigger parametric insurance payouts
- **Lending protocols:** Scrape real-world asset data → attest → use as collateral valuation input
- **DAO governance:** Scrape KPI metrics → attest → trigger automatic treasury actions

**Value prop:** Cheap, flexible oracle alternative. Not as decentralized as Chainlink, but 100x cheaper and can scrape any website, not just pre-configured data feeds.

---

### 5. Journalist / Researcher / Legal Professional

**Who:** Anyone who needs to prove "this web content existed at this time."

**Problem:** Web content changes. Screenshots can be faked. The Wayback Machine isn't real-time and isn't cryptographically verified.

**How they use it:**
- Scrape a web page using an Apify Actor
- Attest the content on-chain — timestamped, hashed, immutable
- Later, produce the attestation as evidence: "This page contained X on date Y — here's the Solana transaction proving it"

**Value prop:** Cryptographic notarization of web content. Like a digital notary public, but automated and on-chain.

**Example:**
```python
# Capture evidence of a web page
attestation = await Actor.call(
    "apify/web-scraper",
    run_input={"startUrls": [{"url": "https://example.com/article"}]}
)

# Attest the captured content
proof = await Actor.call(
    "username/onchain-attestation",
    run_input={
        "chain": "base",  # Use Base for legal documentation
        "data": attestation["dataset"],
        "metadata": {
            "purpose": "legal_evidence",
            "case_id": "2026-CV-12345",
            "captured_url": "https://example.com/article"
        }
    }
)
# Store proof["tx_hash"] as evidence
```

---

## How It Works

### On-Chain vs Off-Chain

```
ON-CHAIN (Solana/Base):          OFF-CHAIN (Apify storage):
┌──────────────────────┐         ┌──────────────────────────┐
│ data_hash (SHA-256)  │         │ Full original data       │
│ actor_id             │─────────│ Input parameters         │
│ run_id               │         │ Output dataset           │
│ timestamp            │         │ Attestation metadata     │
│ attestor_address     │         │ On-chain tx hash (link)  │
└──────────────────────┘         └──────────────────────────┘
```

Anyone can verify: hash the off-chain data → compare with on-chain hash → if they match, the data is authentic and untampered.

### Chain Implementations

**Solana (Memo-based):**
- Cost: ~$0.0007 per attestation
- Method: Transaction memo field (up to 566 bytes)
- Finality: Sub-second
- Perfect for: High-frequency attestations, micropayments

**Base (EAS - Ethereum Attestation Service):**
- Cost: ~$0.01-0.02 per attestation
- Method: Purpose-built attestation protocol
- Benefits: Structured schemas, indexing, ecosystem tooling
- Perfect for: Legal/compliance use cases, structured data

## Input Schema

```json
{
  "chain": "solana",                    // "solana" | "base"
  "data": { ... },                      // any JSON — will be hashed
  "metadata": {                         // optional context
    "actor_id": "apify/google-search-scraper",
    "run_id": "abc123",
    "source_url": "https://google.com",
    "description": "Search results for 'AI agents'",
    "custom": { ... }
  },
  "options": {
    "verification_url": true            // generate verification URL
  }
}
```

## Output Schema

```json
{
  "attestation_id": "att_7xKm...",
  "chain": "solana",
  "tx_hash": "5xYz...",
  "explorer_url": "https://solscan.io/tx/5xYz...",
  "data_hash": "sha256:a1b2c3d4...",
  "attestor_address": "7xKm...",
  "timestamp": "2026-03-06T14:30:00Z",
  "block_number": 284729384,
  "verification": {
    "method": "SHA-256 hash of JSON-canonicalized input data",
    "instructions": "Hash your data with SHA-256 and compare with data_hash"
  },
  "cost": {
    "chain_fee_usd": 0.0007,
    "token": "SOL",
    "amount": 0.000005
  }
}
```

## Verification

To verify an attestation:

1. Get the original data
2. Get the attestation tx_hash
3. Use the verification Actor or do it manually:
   - Hash the data with SHA-256 (using canonical JSON serialization)
   - Look up the tx on Solana/Base explorer
   - Extract the hash from the memo/attestation
   - Compare: if hashes match → data is authentic

## Environment Variables

The Actor requires wallet credentials. **Important:** You must set these as secrets in the Apify Console.

### Required Secrets (set in Apify Console → Actor Settings → Environment Variables)

```bash
SOLANA_PRIVATE_KEY=base58_encoded_private_key
BASE_PRIVATE_KEY=0x_prefixed_hex_private_key
```

**How to set secrets in Apify:**
1. Go to your Actor in Apify Console
2. Navigate to Settings → Environment Variables
3. Click "Add Secret"
4. Add `SOLANA_PRIVATE_KEY` with your base58-encoded Solana private key
5. Add `BASE_PRIVATE_KEY` with your 0x-prefixed hex EVM private key

### Optional RPC URLs (already configured with defaults)

```bash
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com  # default
BASE_RPC_URL=https://mainnet.base.org               # default
```

These are already set in the Actor configuration and don't need to be changed unless you want to use a custom RPC endpoint.

## Cost Structure

| Chain | Transaction Fee | Recommended Pricing | Your Margin |
|---|---|---|---|
| Solana | ~$0.0007 | $0.01/attestation | $0.0093 |
| Base | ~$0.01-0.02 | $0.03/attestation | $0.01-0.02 |

Recommended Apify Store pricing: **Pay-per-Event** at $0.01 (Solana) or $0.03 (Base).

## Development

### Local Setup

```bash
cd onchain-attestation-actor
pip install -r requirements.txt

# Set environment variables
export SOLANA_PRIVATE_KEY="your_key"
export BASE_PRIVATE_KEY="your_key"

# Run locally
python src/main.py
```

### Deploy to Apify

```bash
apify login
apify push
```

## Architecture

```
src/
├── main.py                    # Entry point
├── attestation/
│   ├── hasher.py             # SHA-256 hashing
│   ├── schema.py             # Data models (Pydantic)
│   └── registry.py           # Attestation tracking
├── chains/
│   ├── base_chain.py         # Abstract chain adapter
│   ├── solana_adapter.py     # Solana memo implementation
│   └── base_adapter.py       # Base EAS implementation
├── wallet/
│   ├── solana_wallet.py      # Solana keypair management
│   └── evm_wallet.py         # EVM private key management
└── verification/
    └── verifier.py           # Verify attestations
```

## Roadmap

### v1 (Current)
- ✅ Solana memo-based attestation
- ✅ Base EAS attestation
- ✅ Basic verification API
- ✅ Actor integration via Actor.call()

### v2 (Future)
- [ ] Batch attestations (lower cost per item)
- [ ] Custom Solana program for queryable attestations
- [ ] Webhook integration (auto-attest on Actor completion)
- [ ] Verification web UI
- [ ] Additional chains (Ethereum, Polygon, Arbitrum)

### v3 (Future)
- [ ] On-chain reputation scoring for Actors
- [ ] Token-gated attestations
- [ ] Integration with blockchain-watcher Actor
- [ ] Quality assurance attestations

## Contributing

This is a foundational piece of blockchain-Actor infrastructure. Future modules will build on this:
- `blockchain-payment` - Accept/send crypto payments
- `blockchain-watcher` - Monitor on-chain events, trigger Actors
- `blockchain-executor` - Execute on-chain transactions

Each module is independent but composable — enabling use cases we haven't imagined yet.

## License

MIT
