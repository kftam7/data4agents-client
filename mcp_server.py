import os
import requests
from mcp.server.fastmcp import FastMCP
from web3 import Web3

mcp = FastMCP("Data4Agents")

API_BASE_URL = "https://api.data4agents.dev/v1"
API_KEY = os.environ.get("DATA4AGENTS_API_KEY", "")
PRIVATE_KEY = os.environ.get("WALLET_PRIVATE_KEY", "")
RPC_URL = os.environ.get("RPC_URL", "https://mainnet.base.org") # Example default to Base network
USDC_ADDRESS = os.environ.get("USDC_CONTRACT_ADDRESS", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

# Minimal ERC-20 ABI for USDC transfers
USDC_ABI = [
    {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"}
]

def pay_x402_invoice(recipient: str, amount_usdc: str) -> str:
    """Executes a Web3 USDC transfer and returns the transaction hash."""
    if not PRIVATE_KEY:
        raise ValueError("WALLET_PRIVATE_KEY is required to process x402 payments.")

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = w3.eth.account.from_key(PRIVATE_KEY)
    contract = w3.eth.contract(address=USDC_ADDRESS, abi=USDC_ABI)
    
    # USDC uses 6 decimals
    amount_atomic = int(float(amount_usdc) * 10**6)
    
    tx = contract.functions.transfer(Web3.to_checksum_address(recipient), amount_atomic).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 100000,
        'gasPrice': w3.eth.gas_price
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    # Wait for settlement confirmation
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex()

def make_authed_request(endpoint: str, params: dict) -> str:
    """Wraps requests to automatically handle 402 Payment Required challenges."""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    
    response = requests.get(url, params=params, headers=headers)
    
    # Handle the x402 Micropayment Loop
    if response.status_code == 402:
        invoice = response.json()
        invoice_id = invoice["invoice_id"]
        
        # Execute payment
        tx_hash = pay_x402_invoice(invoice["recipient_wallet"], invoice["amount_usdc"])
        
        # Retry with X402 proof
        headers["Authorization"] = f"X402 {invoice_id}:{tx_hash}"
        response = requests.get(url, params=params, headers=headers)
        
    return response.text

@mcp.tool()
def get_realtime_prices(provider: str = None, model_type: str = None, model: str = None) -> str:
    """Fetch real-time LLM market pricing, 30-day trends, and caching tiers."""
    params = {k: v for k, v in {"provider": provider, "model_type": model_type, "model": model}.items() if v}
    return make_authed_request("/prices/realtime", params)

@mcp.tool()
def recommend_fastest_model(category: str, region: str = "us-east") -> str:
    """Get ranked model recommendations based on live latency and cost metrics."""
    params = {"category": category, "region": region}
    return make_authed_request("/router/recommend", params)

@mcp.tool()
def get_live_status(region: str = "us-east", provider: str = None) -> str:
    """Check real-time provider latency metrics (TTFT, tokens/sec)."""
    params = {k: v for k, v in {"region": region, "provider": provider}.items() if v}
    return make_authed_request("/status/live", params)

if __name__ == "__main__":
    mcp.run()