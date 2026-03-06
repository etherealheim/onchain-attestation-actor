# Example Usage

## Basic Attestation

### Create an attestation on Solana

```json
{
  "chain": "solana",
  "data": {
    "product_name": "Wireless Earbuds",
    "price": 49.99,
    "source": "amazon.com",
    "scraped_at": "2026-03-06T14:30:00Z"
  },
  "metadata": {
    "actor_id": "apify/amazon-scraper",
    "run_id": "abc123",
    "source_url": "https://amazon.com/product/xyz",
    "description": "Product pricing data"
  }
}
```

**Output:**
```json
{
  "attestation_id": "att_7xKm4a9b2c3d",
  "chain": "solana",
  "tx_hash": "5xYzAbC...xyz789",
  "explorer_url": "https://solscan.io/tx/5xYzAbC...xyz789",
  "data_hash": "sha256:a1b2c3d4...xyz",
  "attestor_address": "7xKm...ABC",
  "timestamp": "2026-03-06T14:30:15Z",
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

---

## Verify an Attestation

```json
{
  "verify": true,
  "chain": "solana",
  "tx_hash": "5xYzAbC...xyz789",
  "data": {
    "product_name": "Wireless Earbuds",
    "price": 49.99,
    "source": "amazon.com",
    "scraped_at": "2026-03-06T14:30:00Z"
  }
}
```

**Output:**
```json
{
  "verified": true,
  "details": {
    "tx_hash": "5xYzAbC...xyz789",
    "chain": "solana",
    "data_hash": "sha256:a1b2c3d4...xyz",
    "message": "Attestation verified successfully"
  }
}
```

---

## Integration Examples

### From Another Apify Actor (Python)

```python
from apify import Actor

async def main():
    async with Actor:
        # Your scraping logic
        results = await scrape_data()
        
        # Attest the results
        attestation = await Actor.call(
            "username/onchain-attestation",
            run_input={
                "chain": "solana",
                "data": results,
                "metadata": {
                    "actor_id": Actor.get_env().get('actor_id'),
                    "run_id": Actor.get_env().get('actor_run_id'),
                    "description": "Scraped product data"
                }
            }
        )
        
        # Store attestation with your results
        results["attestation"] = {
            "tx_hash": attestation["tx_hash"],
            "explorer_url": attestation["explorer_url"],
            "data_hash": attestation["data_hash"]
        }
        
        await Actor.push_data(results)
```

### From JavaScript/TypeScript

```javascript
import { Actor } from 'apify';

await Actor.main(async () => {
    // Your scraping logic
    const results = await scrapeData();
    
    // Attest the results
    const attestation = await Actor.call('username/onchain-attestation', {
        chain: 'solana',
        data: results,
        metadata: {
            actorId: Actor.getEnv().actorId,
            runId: Actor.getEnv().actorRunId,
            description: 'Scraped product data'
        }
    });
    
    // Store attestation with your results
    results.attestation = {
        txHash: attestation.tx_hash,
        explorerUrl: attestation.explorer_url,
        dataHash: attestation.data_hash
    };
    
    await Actor.pushData(results);
});
```

---

## Use Case Examples

### 1. Legal Evidence Collection

```json
{
  "chain": "base",
  "data": {
    "url": "https://example.com/article",
    "html_content": "<html>...</html>",
    "screenshot_url": "https://...",
    "captured_at": "2026-03-06T14:30:00Z"
  },
  "metadata": {
    "purpose": "legal_evidence",
    "case_id": "2026-CV-12345",
    "captured_url": "https://example.com/article",
    "description": "Web page content for legal proceedings"
  },
  "options": {
    "verification_url": true,
    "store_full_data": true
  }
}
```

### 2. AI Training Data Provenance

```json
{
  "chain": "solana",
  "data": {
    "dataset_id": "training-set-2026-03",
    "source_urls": ["https://site1.com", "https://site2.com"],
    "item_count": 50000,
    "scrape_date": "2026-03-06",
    "license": "CC-BY-4.0"
  },
  "metadata": {
    "purpose": "ai_training_compliance",
    "model_name": "gpt-5-custom",
    "description": "Training data provenance for EU AI Act compliance"
  }
}
```

### 3. DeFi Oracle Data

```json
{
  "chain": "solana",
  "data": {
    "asset": "AAPL",
    "price": 178.42,
    "source": "yahoo_finance",
    "timestamp": "2026-03-06T14:30:00Z"
  },
  "metadata": {
    "purpose": "defi_oracle",
    "protocol": "lending-protocol-xyz",
    "description": "Real-world asset pricing for collateral valuation"
  }
}
```

### 4. Agent Audit Trail

```json
{
  "chain": "solana",
  "data": {
    "agent_id": "agent-123",
    "action": "executed_trade",
    "params": {
      "from_token": "SOL",
      "to_token": "USDC",
      "amount": 10.0,
      "executed_price": 49.50
    },
    "reasoning": "Market analysis indicated favorable swap opportunity",
    "timestamp": "2026-03-06T14:30:00Z"
  },
  "metadata": {
    "purpose": "agent_observability",
    "agent_framework": "crewai",
    "description": "Autonomous trading decision audit trail"
  }
}
```

---

## Batch Attestations (Future)

For high-volume use cases, you can attest multiple items:

```json
{
  "chain": "solana",
  "batch": true,
  "items": [
    {"data": {...}, "metadata": {...}},
    {"data": {...}, "metadata": {...}},
    {"data": {...}, "metadata": {...}}
  ]
}
```

This will create multiple attestations in a single transaction, reducing per-item cost.

---

## Environment Setup

### Local Development

```bash
# Clone and setup
cd onchain-attestation-actor
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Set environment variables
export SOLANA_PRIVATE_KEY="your_base58_key"
export BASE_PRIVATE_KEY="0xyour_hex_key"

# Run tests
python tests/test_hasher.py

# Run locally (requires Apify CLI)
apify run
```

### Deploy to Apify

```bash
# Login
apify login

# Create secrets in Apify Console
# Settings > Environment Variables > Add Secret:
# - SOLANA_PRIVATE_KEY
# - BASE_PRIVATE_KEY

# Push to Apify
apify push
```

---

## FAQ

**Q: Is my data stored on the blockchain?**  
A: No. Only a SHA-256 hash (64 characters) is stored on-chain. Your full data remains off-chain (in Apify storage if you enable `store_full_data`).

**Q: How much does it cost?**  
A: Solana: ~$0.0007 per attestation. Base: ~$0.01-0.02 per attestation. Plus Actor runtime costs on Apify.

**Q: Can I verify attestations myself?**  
A: Yes! Just hash your data with SHA-256 and compare with the on-chain hash. The transaction is publicly viewable on Solscan (Solana) or BaseScan (Base).

**Q: How long does attestation take?**  
A: Solana: <1 second. Base: 2-5 seconds.

**Q: What if I lose the original data?**  
A: If `store_full_data` is enabled, it's stored in Apify's key-value store. The on-chain record only proves that data with a specific hash existed at a specific time — it doesn't reconstruct the data.

**Q: Can I use my own wallet?**  
A: Yes, but for v1 the Actor uses its own wallet (you provide the private key as an env variable). Future versions will support user-provided wallets for delegated signing.
