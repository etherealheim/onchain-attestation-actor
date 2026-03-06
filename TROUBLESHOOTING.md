# Troubleshooting Guide

## Common Build and Runtime Errors

### Build Error: "environmentVariables must be string"

**Error Message:**
```
ERROR: .actor/actor.json has invalid format
"message": "must be string"
```

**Solution:**
This error has been fixed in the latest version. Pull the latest code:
```bash
git pull origin main
```

The `actor.json` now only contains default RPC URLs. Secret keys must be set in Apify Console (not in the JSON file).

---

### Build Error: Missing Dependencies

**Error Message:**
```
ModuleNotFoundError: No module named 'solana'
```

**Solution:**
Make sure `requirements.txt` is present and all dependencies are listed. The Actor should automatically install dependencies during build.

If building locally:
```bash
pip install -r requirements.txt
```

---

### Runtime Error: "SOLANA_PRIVATE_KEY environment variable is required"

**Error Message:**
```
ValueError: SOLANA_PRIVATE_KEY environment variable is required
```

**Solution:**
You need to set the wallet private keys as secrets in Apify Console:

1. Go to your Actor in Apify Console
2. Settings → Environment Variables
3. Click "Add Secret"
4. Add `SOLANA_PRIVATE_KEY` with your base58-encoded Solana private key
5. Add `BASE_PRIVATE_KEY` with your 0x-prefixed EVM private key

**How to get your private key:**

**Solana:**
- From Phantom wallet: Settings → Export Private Key (base58 format)
- From Solana CLI: `solana-keygen recover` (use the array format, then encode to base58)
- Generate new: Use `solana-keygen new`

**Base/EVM:**
- From MetaMask: Account Details → Export Private Key (0x-prefixed hex)
- Generate new: Any EVM wallet or use web3.py

---

### Runtime Error: "Failed to send Solana transaction"

**Error Message:**
```
RuntimeError: Failed to send Solana transaction: insufficient funds
```

**Solution:**
Your Solana wallet needs a small amount of SOL for transaction fees.

1. Get your wallet address from the Actor logs (it prints on startup)
2. Send ~0.01 SOL to that address (~$0.50)
3. Retry the attestation

**Where to get SOL:**
- Buy on exchanges (Coinbase, Binance, etc.)
- Swap from other tokens using Jupiter
- For devnet testing: Use Solana faucet

---

### Runtime Error: "Failed to send Base transaction"

**Error Message:**
```
RuntimeError: Failed to send Base transaction: insufficient funds
```

**Solution:**
Your Base wallet needs ETH for gas fees.

1. Get your wallet address from the Actor logs
2. Send ~0.001 ETH to that address (~$2.50)
3. Retry the attestation

**Where to get ETH on Base:**
- Bridge from Ethereum using the official Base bridge
- Buy ETH on an exchange that supports Base withdrawals
- Swap from other tokens on Base DEXes

---

### Runtime Error: RPC Connection Issues

**Error Message:**
```
Failed to connect to RPC endpoint
```

**Solution:**
The default public RPC endpoints can be slow or rate-limited.

**Option 1: Use a dedicated RPC provider**

Set custom RPC URLs in Environment Variables (not secrets):
- `SOLANA_RPC_URL` - e.g., `https://mainnet.helius-rpc.com/?api-key=YOUR_KEY`
- `BASE_RPC_URL` - e.g., `https://base-mainnet.g.alchemy.com/v2/YOUR_KEY`

**Free RPC providers:**
- Solana: Helius, QuickNode (free tier)
- Base: Alchemy, Infura (free tier)

**Option 2: Retry**
Public RPCs can be intermittent. Just retry the attestation.

---

### Verification Error: "Hash mismatch"

**Error Message:**
```
verified: false
error: "Hash mismatch or transaction not found"
```

**Possible causes:**

1. **Wrong data provided** - Make sure you're verifying with the EXACT same data that was attested (same JSON structure, same values)

2. **JSON key ordering** - The hasher uses canonical JSON (sorted keys). If you're manually hashing, make sure to sort keys.

3. **Transaction not confirmed yet** - Wait a few seconds for the transaction to finalize, then retry.

4. **Wrong tx hash** - Double-check you're using the correct transaction hash.

**How to manually verify:**
```python
import json
import hashlib

# Your original data
data = {"test": "data"}

# Canonical JSON (sorted keys, no spaces)
canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))

# SHA-256 hash
hash_bytes = hashlib.sha256(canonical.encode('utf-8')).digest()
hash_hex = hash_bytes.hex()

print(f"Expected hash: sha256:{hash_hex}")
```

Compare this with the hash stored on-chain.

---

### Performance: Slow Attestations

**Symptom:** Attestations taking >10 seconds

**Solutions:**

1. **Use custom RPC endpoints** - Public RPCs can be slow
2. **Choose Solana for speed** - Solana is sub-second, Base takes 2-5 seconds
3. **Batch attestations** (coming in v2) - Attest multiple items in one transaction

---

### Development: Import Errors

**Error Message:**
```
ImportError: cannot import name 'SolanaWallet'
```

**Solution:**
Make sure you're running from the correct directory and the module structure is intact:

```bash
cd git-local/onchain-attestation-actor
python -c "from src.wallet import SolanaWallet; print('OK')"
```

If imports fail, check that all `__init__.py` files are present:
- `src/attestation/__init__.py`
- `src/chains/__init__.py`
- `src/wallet/__init__.py`
- `src/verification/__init__.py`

---

## Getting Help

1. **Check the logs** - Apify Console shows detailed error messages
2. **Review documentation** - README.md has full usage examples
3. **Test locally first** - Run `python tests/test_hasher.py` to verify setup
4. **Check wallet balances** - Most errors are due to insufficient funds
5. **File an issue** - GitHub issues for bugs: https://github.com/etherealheim/onchain-attestation-actor/issues

---

## Debug Checklist

Before filing an issue, verify:

- [ ] Latest code pulled from GitHub
- [ ] `SOLANA_PRIVATE_KEY` set as secret in Apify Console
- [ ] `BASE_PRIVATE_KEY` set as secret in Apify Console
- [ ] Wallet has sufficient balance (0.01 SOL or 0.001 ETH)
- [ ] Input JSON is valid (use JSON validator)
- [ ] Chain is spelled correctly: "solana" or "base" (lowercase)
- [ ] RPC endpoints are accessible (try in browser)

---

## Test Attestation

Use this minimal input to test if the Actor is working:

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

Expected output: Transaction hash, explorer URL, and attestation details.

If this works, the Actor is configured correctly!
