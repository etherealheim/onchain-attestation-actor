# Wallet Setup Guide

## Quick Start: Get Your Attestation Actor Running in 5 Minutes

### Step 1: Create a Solana Wallet

**Option A: Using Phantom (Easiest)**
1. Install [Phantom Wallet](https://phantom.app/) browser extension
2. Create a new wallet (save your seed phrase!)
3. Go to Settings → Export Private Key
4. Copy the base58-encoded private key

**Option B: Using Solana CLI**
```bash
# Install Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Generate new keypair
solana-keygen new --outfile ~/attestation-wallet.json

# Get the private key in base58 format
cat ~/attestation-wallet.json
# This outputs an array like [123,45,67,...] 
# You'll need to convert this to base58 (see below)
```

**Option C: Generate Programmatically (for testing)**
```python
from solders.keypair import Keypair
import base58

# Generate new keypair
keypair = Keypair()

# Get private key in base58 format (this is what you need for Apify)
private_key_base58 = base58.b58encode(bytes(keypair)).decode('utf-8')
print(f"Private Key (base58): {private_key_base58}")
print(f"Public Key (address): {keypair.pubkey()}")
```

### Step 2: Fund Your Wallet

**For Mainnet (Real Money):**
- Send ~0.01 SOL to your wallet address (~$1-2)
- This covers ~1000+ attestations
- Buy SOL on: Coinbase, Binance, Kraken, or use Moonpay in Phantom

**For Devnet (Free Testing):**
```bash
# Switch to devnet
solana config set --url devnet

# Airdrop free SOL (2 SOL per request)
solana airdrop 2 YOUR_WALLET_ADDRESS
```

Or use the web faucet: https://faucet.solana.com/

### Step 3: Configure Apify Actor

1. Go to your Actor in **Apify Console**
2. Click on the **Source** tab
3. Scroll down to the **Environment variables** section
4. Add your private key:
   - **Variable name:** `SOLANA_PRIVATE_KEY`
   - **Value:** Your base58-encoded private key from Step 1
   - **Check the "Secret" checkbox** (this encrypts the value and hides it from logs)
5. Click **Save** and then **Build** to apply the changes

**For Devnet Testing:** Also add:
   - **Variable name:** `SOLANA_RPC_URL`
   - **Value:** `https://api.devnet.solana.com`
   - (No need to mark as Secret)

**Important:** Environment variables are set at build time. After adding/changing them, you must create a new build for the changes to take effect.

### Step 4: Test Your First Attestation

Run the Actor with this input:
```json
{
  "chain": "solana",
  "data": {
    "test": "Hello blockchain!",
    "timestamp": "2026-03-06T15:00:00Z"
  },
  "description": "My first attestation"
}
```

You should get back:
- `tx_hash`: The Solana transaction signature
- `explorer_url`: Link to view on Solscan
- `data_hash`: The SHA-256 hash of your data

### Cost Breakdown

| Network | Cost per Attestation | $1 gets you |
|---------|---------------------|-------------|
| Solana Mainnet | ~$0.001 | ~1000 attestations |
| Solana Devnet | FREE | Unlimited (testing) |
| Base | ~$0.02 | ~50 attestations |

### Mainnet vs Devnet

**Use Devnet for:**
- Testing your integration
- Development
- Demos (transactions are real but on test network)

**Use Mainnet for:**
- Production attestations
- Data that needs to be permanently verifiable
- When you need the "real" proof

To switch between them, just change `SOLANA_RPC_URL`:
- Mainnet: `https://api.mainnet-beta.solana.com` (default)
- Devnet: `https://api.devnet.solana.com`

---

## Integration with Other Actors

### Method 1: Call from Another Actor (Recommended)

```python
from apify import Actor

async def main():
    async with Actor:
        # Your scraping logic
        scraped_data = await scrape_instagram()
        
        # Attest the results
        attestation_run = await Actor.call(
            "YOUR_USERNAME/onchain-attestation",
            run_input={
                "chain": "solana",
                "data": scraped_data,
                "description": "Instagram scrape results",
                "source_url": "https://instagram.com/...",
                "actor_id": Actor.get_env().get("actorId"),
                "run_id": Actor.get_env().get("actorRunId"),
            }
        )
        
        # Get the attestation result
        attestation = attestation_run.get("defaultDatasetId")
        # ... use attestation.tx_hash, attestation.explorer_url
```

### Method 2: Webhook Integration (Automatic)

Set up a webhook to automatically attest every Actor run:

1. Go to your scraping Actor → Settings → Webhooks
2. Add webhook:
   - Event: `ACTOR.RUN.SUCCEEDED`
   - URL: `https://api.apify.com/v2/acts/YOUR_USERNAME~onchain-attestation/runs`
   - Payload template:
   ```json
   {
     "chain": "solana",
     "data": {{resource}},
     "actor_id": "{{actorId}}",
     "run_id": "{{actorRunId}}"
   }
   ```

### Method 3: Manual via API

```bash
curl -X POST "https://api.apify.com/v2/acts/YOUR_USERNAME~onchain-attestation/runs?token=YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chain": "solana",
    "data": {"your": "data"},
    "description": "Manual attestation"
  }'
```

---

## Verifying Attestations

Anyone can verify an attestation:

1. **Using the Actor:**
```json
{
  "chain": "solana",
  "verify_mode": true,
  "tx_hash": "5xYzAbC...",
  "data": {"original": "data"}
}
```

2. **Manually on Solscan:**
   - Go to the explorer URL from the attestation output
   - View the transaction memo
   - Compare the hash with SHA-256 of your data

3. **Programmatically:**
```python
import hashlib
import json

# Your original data
data = {"your": "data"}

# Create canonical JSON and hash
canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
hash_hex = hashlib.sha256(canonical.encode()).hexdigest()

print(f"Expected hash: sha256:{hash_hex}")
# Compare with on-chain hash
```

---

## Troubleshooting

**"SOLANA_PRIVATE_KEY environment variable is required"**
→ Add the secret in Actor Settings → Environment Variables

**"insufficient funds"**
→ Your wallet needs SOL. Send at least 0.01 SOL to the wallet address.

**"Failed to send Solana transaction"**
→ Check RPC URL, wallet balance, or try again (network congestion)

**Verification returns false**
→ Make sure you're using the EXACT same data (including whitespace, key order)
