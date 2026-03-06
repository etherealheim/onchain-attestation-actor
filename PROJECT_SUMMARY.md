# On-Chain Attestation Actor - Project Summary

## What We Built

A **modular blockchain attestation service** for the Apify Actor ecosystem that creates cryptographic proofs of data on Solana and Base blockchains.

### Core Value Proposition

**"Prove your data is real."**

Any Apify Actor can now create verifiable, immutable proof that specific data existed at a specific time — enabling compliance, trust, and accountability in the Actor economy.

---

## Architecture

### Modular Design

```
┌─────────────────────────────────────────────────┐
│  On-Chain Attestation Actor                    │
│                                                 │
│  ┌─────────────┐  ┌──────────────────────┐     │
│  │ Core        │  │ Chain Adapters       │     │
│  │ - Hasher    │  │ - Solana (memo)      │     │
│  │ - Schema    │  │ - Base (calldata)    │     │
│  │ - Verifier  │  │ - Future: ETH, etc   │     │
│  └─────────────┘  └──────────────────────┘     │
│                                                 │
│  Input: data + metadata                         │
│  Output: tx_hash + proof                        │
└─────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Off-chain data, on-chain hash** - Only SHA-256 hashes go on-chain (cheap, scalable)
2. **Chain-agnostic interface** - Same API for Solana/Base/future chains
3. **No custom smart contracts** - Uses native blockchain primitives (memos, calldata)
4. **Modular architecture** - Foundation for future `blockchain-*` Actor suite

---

## Technical Stack

| Component | Technology |
|---|---|
| Runtime | Python 3.11 + Apify SDK |
| Solana | solana-py, solders |
| EVM/Base | web3.py, eth-account |
| Hashing | SHA-256 (stdlib) |
| Validation | Pydantic v2 |
| Container | Docker (Apify base image) |

---

## Implementation Details

### Solana Attestation (Memo-based)
- **Method:** Transaction memo field (up to 566 bytes)
- **Cost:** ~$0.0007 per attestation
- **Finality:** Sub-second
- **Structure:** `{"hash": "sha256:...", "metadata": {...}, "timestamp": "..."}`

### Base Attestation (Calldata)
- **Method:** Self-transfer transaction with data in calldata
- **Cost:** ~$0.015 per attestation
- **Finality:** 2-5 seconds
- **Future:** Upgrade to EAS (Ethereum Attestation Service) for structured schemas

### Verification
- Hash the original data (SHA-256)
- Fetch on-chain transaction
- Extract hash from memo/calldata
- Compare hashes → verified or not

---

## Use Cases (Prioritized)

### v1 Target Users

1. **Apify Actor Developers**
   - Add blockchain verification to their Actors
   - Differentiate with "verified results" badge
   - Willing to pay $0.01-0.03 per attestation

2. **Enterprise Data Buyers**
   - Compliance and audit requirements
   - Prove data provenance for legal/regulatory purposes
   - High value in: finance, legal, insurance, AI/ML

3. **AI Agents**
   - Agent observability and audit trails
   - Prove autonomous decision-making processes
   - Growing market (2024-2026 inflection)

### Future Users (v2+)

4. **DeFi Protocols** - Cheap oracle alternative
5. **Journalists/Legal** - Cryptographic notarization
6. **Marketplace Quality** - On-chain Actor reputation

---

## Files Created

```
onchain-attestation-actor/
├── README.md                          # Full documentation + use cases
├── QUICKSTART.md                      # Getting started guide
├── EXAMPLE_USAGE.md                   # Integration examples
├── PROJECT_SUMMARY.md                 # This file
├── Dockerfile                         # Container config
├── requirements.txt                   # Dependencies
├── .gitignore                         # Git ignore rules
│
├── .actor/
│   ├── actor.json                     # Actor metadata
│   └── input_schema.json              # Input validation
│
├── src/
│   ├── main.py                        # Entry point (96 lines)
│   │
│   ├── attestation/
│   │   ├── __init__.py
│   │   ├── schema.py                  # Pydantic models
│   │   └── hasher.py                  # SHA-256 utilities
│   │
│   ├── chains/
│   │   ├── __init__.py
│   │   ├── base_chain.py              # Abstract adapter
│   │   ├── solana_adapter.py          # Solana implementation
│   │   └── base_adapter.py            # Base implementation
│   │
│   ├── wallet/
│   │   ├── __init__.py
│   │   ├── solana_wallet.py           # Solana keypair
│   │   └── evm_wallet.py              # EVM wallet
│   │
│   └── verification/
│       ├── __init__.py
│       └── verifier.py                # Attestation verification
│
└── tests/
    └── test_hasher.py                 # Unit tests
```

**Total:** ~800 lines of code across 20 files

---

## How It Works (Step by Step)

### Creating an Attestation

```
1. Actor receives input
   ↓
2. Parse and validate with Pydantic
   ↓
3. Hash the data (SHA-256)
   ↓
4. Load wallet from env variables
   ↓
5. Select chain adapter (Solana or Base)
   ↓
6. Create and sign transaction
   ↓
7. Submit to blockchain
   ↓
8. Wait for confirmation
   ↓
9. Return attestation output
   ↓
10. Optional: Store full data in Apify KV store
```

### Verifying an Attestation

```
1. Actor receives tx_hash + original data
   ↓
2. Hash the provided data
   ↓
3. Fetch on-chain transaction
   ↓
4. Extract hash from transaction
   ↓
5. Compare hashes
   ↓
6. Return verification result
```

---

## Cost Analysis

### Per-Attestation Costs

| Chain | TX Fee | Recommended Price | Margin |
|---|---|---|---|
| Solana | $0.0007 | $0.01 | $0.0093 (93%) |
| Base | $0.015 | $0.03 | $0.015 (50%) |

### Revenue Projections (Apify Store)

**Conservative (1,000/month):**
- Revenue: $10-30/month
- Margin: $9-23/month

**Moderate (10,000/month):**
- Revenue: $100-300/month
- Margin: $93-215/month

**Optimistic (100,000/month):**
- Revenue: $1,000-3,000/month
- Margin: $930-2,150/month

**Break-even:** ~100 attestations (covers Apify platform costs)

---

## Next Steps

### Immediate (Deploy v1)

1. ✅ Code complete
2. ⏳ Set up wallets (Solana + Base)
3. ⏳ Deploy to Apify
4. ⏳ Configure secrets
5. ⏳ Test with real attestations
6. ⏳ Publish to Apify Store

### Short-term (v1.1-1.2)

- Batch attestations (lower cost per item)
- Webhook integration (auto-attest on Actor completion)
- Better error handling and retry logic
- Performance optimization (connection pooling)

### Medium-term (v2)

- Custom Solana program (queryable attestations)
- Upgrade Base to EAS (structured schemas)
- Web verification UI
- Additional chains (Ethereum, Polygon, Arbitrum)
- Actor analytics dashboard

### Long-term (v3+)

Build the full blockchain-Actor infrastructure suite:

- **blockchain-payment** - Accept/send crypto payments (x402, Skyfire)
- **blockchain-watcher** - Monitor on-chain events, trigger Actors
- **blockchain-executor** - Execute on-chain transactions (swaps, votes, transfers)
- **blockchain-reputation** - On-chain quality scoring for Actors

Each module is independent but composable — enabling emergent use cases.

---

## Why This Matters

### The Vision

**Apify has 22,000 Actors. None of them provide cryptographic proof of their output.**

This Actor changes that. It's infrastructure that enables:

1. **Trust** - Data buyers can verify Actor outputs
2. **Compliance** - Meet regulatory requirements (EU AI Act, etc.)
3. **Observability** - AI agents get audit trails
4. **Innovation** - Enables use cases we haven't imagined yet

### The Opportunity

- **Market timing:** Early (2026) but growing fast
- **Competition:** Low — almost nobody has built this
- **Defensibility:** Network effects (more attestations = more trust)
- **Expansion:** Foundation for entire blockchain-Actor ecosystem

### The Risk

**Demand is still early.** The number of AI agents with crypto wallets looking for verified scraping data is small today. But:

- Coinbase, Google, OpenAI are all pushing agentic payments
- x402 grew from 0 to 500K weekly transactions in 6 months
- Agent economy is the next frontier (2024-2027)

**We're building rails before the train arrives.** That's the right move if you believe agents will need blockchain infrastructure — which all the major players clearly do.

---

## Success Metrics

### v1 (3 months)
- 10+ Actor developers integrate attestation
- 1,000+ attestations created
- Published on Apify Store

### v2 (6 months)
- 100+ active Actor integrations
- 10,000+ attestations/month
- First enterprise customer (finance/legal)

### v3 (12 months)
- blockchain-payment and blockchain-watcher launched
- 100,000+ attestations/month
- $1,000+/month revenue
- First AI agent using the full suite

---

## Lessons from Planning

1. **Start with infrastructure, not applications** - Primitives enable innovation
2. **Modular beats monolithic** - Build composable pieces
3. **Chain-agnostic from day one** - Don't lock into one blockchain
4. **Off-chain data, on-chain proof** - Scalability through separation
5. **Market timing is early but direction is clear** - Agents need payment rails and audit trails

---

## Built With

- Strategic brainstorming: Analyzed market, use cases, personas
- Architecture decisions: Solana (memo) + Base (calldata), no smart contracts v1
- Clean code: Modular, extensible, well-documented
- Real research: x402 protocol, Solana agent ecosystem, EAS on Base
- User focus: Started with use cases, built backwards

**From idea to implementation in one session.**

---

**This is v1 of blockchain infrastructure for the Apify Actor economy. Ship it and see what people build.**
