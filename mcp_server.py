import os
import httpx
from typing import Optional, Literal
from mcp.server.fastmcp import FastMCP
from web3 import Web3

# Import x402 SDK components
from x402 import x402Client
from x402.http.clients import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client

mcp = FastMCP("Data4Agents")

# Configuration
API_BASE_URL = os.environ.get("TARGET_API_BASE_URL", "")
API_KEY = os.environ.get("DATA4AGENTS_API_KEY", "")
PRIVATE_KEY = os.environ.get("WALLET_PRIVATE_KEY", "")
NETWORK = os.environ.get("NETWORK", "")

# Reusable Literal Types for Dropdowns
RegionType = Literal["us-east", "us-west", "ap-southeast", "ap-northeast", "eu-central", "eu-west"]
ProviderType = Literal["Qwen", "Volcano Ark", "Zhipu", "DeepSeek", "MiniMax", "Moonshot"]
CategoryType = Literal["general", "image", "video"]

# Initialize x402 client if a private key is provided
x402_http = None
if PRIVATE_KEY:
    pk_bytes = bytes.fromhex(PRIVATE_KEY.removeprefix("0x"))
    w3 = Web3()
    account = w3.eth.account.from_key(pk_bytes)
    evm_signer = EthAccountSigner(account=account)
    
    client = x402Client()
    register_exact_evm_client(client, signer=evm_signer, networks=[NETWORK])
    x402_http = x402HttpxClient(x402_client=client)

async def make_authed_request(endpoint: str, params: dict) -> str:
    """Routes requests through standard HTTP (if API Key) or the x402 SDK (if Web3)."""
    url = f"{API_BASE_URL}/v1{endpoint}"
    
    # 1. Strict Priority: API Key Mode
    if API_KEY and API_KEY.strip() != "":
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "X-API-Key": API_KEY
        }
        async with httpx.AsyncClient() as std_client:
            try:
                response = await std_client.get(url, params=params, headers=headers)
                
                if response.status_code == 402:
                    return f"HTTP 402 Error: API Key was provided but rejected (invalid or zero credits). Web3 fallback disabled to prevent accidental spend. Raw Response: {response.text}"
                
                if response.status_code != 200:
                    return f"HTTP {response.status_code} Error: {response.text}"
                    
                return response.text
            except Exception as e:
                return f"Request Failed: {str(e)}"
                
    # 2. Autonomous Micropayment Mode (x402 SDK)
    if not x402_http:
        return "Configuration Error: No DATA4AGENTS_API_KEY or WALLET_PRIVATE_KEY provided."
        
    try:
        # The x402HttpxClient automatically handles 402 intercepts, payments, and retries
        response = await x402_http.get(url, params=params)
        
        if response.status_code != 200:
            return f"HTTP {response.status_code} Error: {response.text}"
            
        return response.text
    except Exception as e:
        return f"x402 Autonomous Payment Failed: {str(e)}"

@mcp.tool()
async def get_health() -> str:
    """Verify API health, network configurations, protocol versions, and accepted asset contracts."""
    try:
        url = f"{API_BASE_URL}/health"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                return f"HTTP {response.status_code} Error: {response.text}"
                
            return response.text
    except Exception as e:
        return f"Health Check Request Failed: {str(e)}"

@mcp.tool()
async def get_realtime_prices(
    provider: Optional[ProviderType] = None, 
    model_type: Optional[CategoryType] = None, 
    model: Optional[str] = None
) -> str:
    """Fetch real-time LLM market pricing, 30-day trends, and caching tiers."""
    params = {k: v for k, v in {"provider": provider, "model_type": model_type, "model": model}.items() if v}
    return await make_authed_request("/prices/realtime", params)

@mcp.tool()
async def recommend_fastest_model(category: CategoryType, region: RegionType = "us-east") -> str:
    """Get ranked model recommendations based on live latency and cost metrics."""
    params = {"category": category, "region": region}
    return await make_authed_request("/router/recommend", params)

@mcp.tool()
async def get_live_status(region: RegionType = "us-east", provider: Optional[ProviderType] = None) -> str:
    """Check real-time provider latency metrics (TTFT, tokens/sec)."""
    params = {k: v for k, v in {"region": region, "provider": provider}.items() if v}
    return await make_authed_request("/status/live", params)

if __name__ == "__main__":
    mcp.run()