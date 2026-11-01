# Data4Agents MCP Server

This repository contains the Model Context Protocol (MCP) server for the [Data4Agents](https://data4agents.dev) API. 

Data4Agents provides real-time LLM market pricing, model routing, and provider latency analytics designed natively for autonomous agents.

This MCP server acts as a client wrapper around the Data4Agents API, allowing developer-run agents (like Claude Desktop) to natively discover and call the API as built-in tools. It features an automated machine-to-machine payment loop that handles the API's x402 cryptographic micropayment protocol.

## Features

*   **Real-time Pricing (`get_realtime_prices`):** Fetch real-time LLM market pricing, 30-day trends, and caching tiers.
*   **Model Routing (`recommend_fastest_model`):** Get ranked model recommendations based on live latency and cost metrics across global regions.
*   **Live Latency Probes (`get_live_status`):** Check real-time provider latency metrics (TTFT, tokens/sec) from global edge probes.
*   **API Health (`get_health`):** Verify API health, network configurations, protocol versions, and accepted asset contracts.
*   **Autonomous x402 Payments:** Automatically intercepts `402 Payment Required` challenges, executes on-chain USDC transfers, and retries requests with cryptographic proof via the official x402 SDK.
*   **Hybrid Authentication:** Supports both Web3 micropayments and traditional Web2 fiat API keys.

## Prerequisites

*   Python 3.10+
*   A funded EVM wallet (for x402 micropayments) OR a traditional Data4Agents API Key.

## Installation

1.  Clone this repository:
    ```bash
    git clone [https://github.com/your-org/data4agents-client.git](https://github.com/your-org/data4agents-client.git)
    cd data4agents-client
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration (Claude Desktop)

To use this MCP server with Claude Desktop, configure the `claude_desktop_config.json` file. 

### Option A: Web3 Autonomous Payments (x402)
This configuration allows your agent to autonomously pay for data using USDC on an EVM network.

**⚠️ SECURITY WARNING:** The `WALLET_PRIVATE_KEY` executes live EVM transactions. Strictly use a dedicated **burner wallet** funded with only a small amount of USDC and native gas tokens. **Never use your main wallet's private key.**

Add the following to your `claude_desktop_config.json` (located at `~/Library/Application Support/Claude/claude_desktop_config.json` on Mac or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "data4agents": {
      "command": "python3",
      "args": [
        "/absolute/path/to/data4agents-client/mcp_server.py"
      ],
      "env": {
        "TARGET_API_BASE_URL": "[https://api.data4agents.dev](https://api.data4agents.dev)",
        "NETWORK": "eip155:8453",
        "WALLET_PRIVATE_KEY": "0xYourBurnerKeyWithFunds"
      }
    }
  }
}
```
*(Note: To test on Base Sepolia, change NETWORK to `eip155:84532`)*

### Option B: Traditional API Key (Web2)
If you prefer a traditional fiat subscription, omit the Web3 variables and provide your API key.

```json
{
  "mcpServers": {
    "data4agents": {
      "command": "python3",
      "args": [
        "/absolute/path/to/data4agents-client/mcp_server.py"
      ],
      "env": {
        "TARGET_API_BASE_URL": "[https://api.data4agents.dev](https://api.data4agents.dev)",
        "DATA4AGENTS_API_KEY": "sk_live_yourTraditionalApiKey"
      }
    }
  }
}
```