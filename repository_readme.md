# Data4Agents MCP Server

This repository contains the Model Context Protocol (MCP) server for the [Data4Agents](https://data4agents.dev) API. 

Data4Agents provides real-time LLM market pricing, model routing, and provider latency analytics designed natively for autonomous agents.

This MCP server acts as a client wrapper around the Data4Agents API, allowing developer-run agents (like Claude Desktop) to natively discover and call the API as built-in tools. It features an automated machine-to-machine payment loop that handles the API's x402 cryptographic micropayment protocol.

## Features

*   **Real-time Pricing (`get_realtime_prices`):** Fetch real-time LLM market pricing, 30-day trends, and caching tiers.
*   **Model Routing (`recommend_fastest_model`):** Get ranked model recommendations based on live latency and cost metrics across global regions.
*   **Live Latency Probes (`get_live_status`):** Check real-time provider latency metrics (TTFT, tokens/sec) from global edge probes.
*   **Autonomous x402 Payments:** Automatically intercepts `402 Payment Required` challenges, executes on-chain USDC transfers, and retries requests with cryptographic proof.
*   **Hybrid Authentication:** Supports both Web3 micropayments and traditional Web2 fiat API keys.

## Prerequisites

*   Python 3.10+
*   A funded EVM wallet (for x402 micropayments) OR a traditional Data4Agents API Key.

## Installation

1.  Clone this repository:
    ```bash
    git clone https://github.com/your-org/data4agents-client.git
    cd data4agents-client
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration (Claude Desktop)

To use this MCP server with Claude Desktop, you must configure the `claude_desktop_config.json` file. 

### Option A: Web3 Autonomous Payments (x402)
This configuration allows your agent to autonomously pay for data using USDC on an EVM network (e.g., Base).

**⚠️ SECURITY WARNING:** The `WALLET_PRIVATE_KEY` executes live EVM transactions. Strictly use a dedicated **burner wallet** funded with only a small amount of USDC and native gas tokens. **Never use your main wallet's private key.**

Add the following to your `claude_desktop_config.json` (located at `~/Library/Application Support/Claude/claude_desktop_config.json` on Mac or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "data4agents": {
      "command": "python3",
      "args": [
        "/absolute/path/to/data4agents-mcp/mcp_server.py"
      ],
      "env": {
        "WALLET_PRIVATE_KEY": "0xYourBurnerKeyWithFunds",
        "RPC_URL": "https://mainnet.base.org", 
        "USDC_CONTRACT_ADDRESS": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
      }
    }
  }
}
```
*(Note: To test on Base Sepolia, use RPC `https://sepolia.base.org` and USDC Contract `0x036CbD53842c5426634e7929541eC2318f3dCF7e`)*

### Option B: Traditional API Key (Web2)
If you prefer a traditional fiat subscription, omit the Web3 variables and provide your API key.

```json
{
  "mcpServers": {
    "data4agents": {
      "command": "python3",
      "args": [
        "/absolute/path/to/data4agents-mcp/mcp_server.py"
      ],
      "env": {
        "DATA4AGENTS_API_KEY": "sk_live_yourTraditionalApiKey"
      }
    }
  }
}
```

## Agent Instruction Block (System Prompt)

If you are instructing a custom agent to use this tool, provide it with the following system prompt block to ensure it understands the payment loop:

```text
# Data4Agents API Integration Instructions
You have access to the Data4Agents real-time LLM market data feed at `https://api.data4agents.dev`. 
This API is monetized via the autonomous x402 protocol. Do not ask the user for a traditional API key. 

When you need to query `/v1/prices/realtime`, `/v1/router/recommend`, or `/v1/status/live`, follow this exact execution loop:
1. **Initial Request:** Make the GET request with your desired query parameters.
2. **Intercept 402:** Expect a `402 Payment Required` response containing a JSON invoice object.
3. **Parse Invoice:** Extract `invoice_id`, `amount_usdc`, `recipient_wallet`, and `chain_id` from the 402 response body.
4. **Settle Payment:** Execute an on-chain transfer of the specified USDC amount to the recipient wallet on the requested chain.
5. **Capture Proof:** Record the resulting transaction hash (`tx_hash`).
6. **Retry with Authorization:** Re-send the identical GET request, adding this exact header:
   `Authorization: X402 <invoice_id>:<tx_hash>`
7. **Verify Receipt:** Parse the `200 OK` response data. Verify the server successfully settled your payment by checking the `PAYMENT-RESPONSE` header.

If you need to verify network configurations, protocol versions, or the accepted asset contract before initiating a payment, query the unauthenticated `/health` endpoint.
```