"""
Data4Agents x402 Autonomous Payment Demo Client

This script demonstrates how to use the official x402 Python SDK to automatically 
handle 402 Payment Required challenges, execute Web3 USDC transfers, and retry 
requests with cryptographic proof.

Requirements:
pip install x402 httpx web3 python-dotenv
"""
import os
import sys
import json
import traceback
import logging
import asyncio
from dotenv import load_dotenv
from web3 import Web3

# Enable DEBUG logging to observe the internal intercept/pay/retry flow
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)

from x402 import x402Client
from x402.http.clients import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client

# Load environment variables from .env file
load_dotenv(".env")

# Configuration
NETWORK = os.getenv("NETWORK", "eip155:84532") # Base Sepolia
BASE_URL = os.getenv("TARGET_API_BASE_URL", "https://api.data4agents.dev").rstrip("/")

# Endpoints to test the payment loop against
ENDPOINTS_TO_TEST = [
    {"path": "/v1/latency/global", "params": {"region": "us-east"}},
    {"path": "/v1/prices/realtime", "params": {"provider": "Qwen"}},
    {"path": "/v1/models/recommend", "params": {"category": "general", "region": "us-east"}},
]

async def test_endpoint(x402_http, base_url, endpoint):
    url = f"{base_url}{endpoint['path']}"
    params = endpoint.get("params", {})
    
    print("\n" + "=" * 70)
    print(f"[STAGE 1] 🚀 Requesting {endpoint['path']}")
    print(f"Params: {params}")
    print("=" * 70)

    try:
        # The SDK handles the 402 intercept, payment, and retry automatically
        resp = await x402_http.get(url, params=params)
        
        print(f"\n[STAGE 2] ✅ Final Response Status: {resp.status_code}")
        
        payment_response_raw = resp.headers.get("PAYMENT-RESPONSE")
        if payment_response_raw:
            try:
                pr_data = json.loads(payment_response_raw)
                tx_hash = pr_data.get("tx_hash")
                print(f"[STAGE 3] 📜 Server acknowledged payment! TX Hash: {tx_hash}")
                
                # Dynamically provide the correct block explorer link
                explorer = "basescan.org" if "8453" in NETWORK and "84532" not in NETWORK else "sepolia.basescan.org"
                print(f"🔗 Explorer Link: https://{explorer}/tx/{tx_hash}")
            except Exception as e:
                print(f"Cannot decode PAYMENT-RESPONSE JSON: {e}")
        else:
            print("⚠️ PAYMENT-RESPONSE header NOT present. (Was a payment actually required?)")

        print("\n[STAGE 4] 📦 Response Body:")
        try:
            print(json.dumps(resp.json(), indent=2)[:500] + "\n... [truncated]")
        except Exception:
            print(resp.text[:500])

    except Exception as e:
        print(f"\n❌ CLIENT EXCEPTION: {type(e).__name__}: {e}")
        traceback.print_exc()

async def main():
    # Matches MCP server env var for consistency, fallback to buyer-specific one
    private_key = os.getenv("WALLET_PRIVATE_KEY") or os.getenv("BUYER_WALLET_PRIVATE_KEY")

    if not private_key:
        raise RuntimeError(
            "Missing WALLET_PRIVATE_KEY in .env file. "
            "Please provide a burner wallet private key funded with USDC."
        )

    # Setup Web3 and Signer
    pk_hex = private_key.removeprefix("0x")
    pk_bytes = bytes.fromhex(pk_hex)
    w3 = Web3()
    account = w3.eth.account.from_key(pk_bytes)
    evm_signer = EthAccountSigner(account=account)

    print("=" * 70)
    print(f"   X402 AUTONOMOUS PAYMENT TEST SUITE   ")
    print(f"Buyer wallet address: {account.address}")
    print(f"Target API Base: {BASE_URL}")
    print(f"Network: {NETWORK}")
    print("=" * 70, "\n")

    # Initialize x402 Client
    client = x402Client()
    register_exact_evm_client(client, signer=evm_signer, networks=[NETWORK])
    
    # Increase HTTP timeout and pass directly to the client
    import httpx
    timeout = httpx.Timeout(30.0, connect=10.0)
    
    x402_http = x402HttpxClient(
        x402_client=client, 
        timeout=timeout
    )

    # Run Tests
    for endpoint in ENDPOINTS_TO_TEST:
        await test_endpoint(x402_http, BASE_URL, endpoint)
        await asyncio.sleep(2) # Brief pause between requests

    print("\n" + "=" * 70)
    print("🏁 Test suite finished.")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())