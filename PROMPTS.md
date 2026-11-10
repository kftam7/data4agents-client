# Agent Instruction Blocks (System Prompts)

To integrate Data4Agents into your autonomous AI agents, copy and paste the relevant system prompt blocks below into your agent's instructions. 

Choose the prompt that matches your integration method.

---

## 1. Using the Data4Agents MCP Client (Recommended)
If you have connected the `data4agents-mcp` server to your agent, the cryptographic payment loop is completely abstracted. Use this prompt to teach the agent *when* to use the provided tools.

```text
# Data4Agents Tool Instructions
You have access to the Data4Agents market data tools. Use these tools whenever the user asks for LLM pricing, model recommendations, or live latency data.

- **get_realtime_prices**: Use this to fetch current market pricing, 30-day trends, and caching tiers for specific providers or models.
- **recommend_fastest_model**: Use this to dynamically select the best model for a task based on live latency (TTFT) and cost metrics.
- **get_live_status**: Use this to check real-time provider latency and health metrics from global edge probes.
- **get_health**: Use this to verify the API is online and check supported network configurations.

You do not need to worry about payments, API keys, or authentication. The underlying tools will automatically handle the x402 cryptographic payment loop or fiat API keys for you.
```

---

## 2. Raw REST API with x402 Micropayments
If your agent is interacting with the Data4Agents REST API directly (without our MCP client) using generic HTTP tools and a crypto wallet, inject this prompt to teach it the x402 micropayment protocol.

```text
# Data4Agents API - x402 Autonomous Payment Instructions
You have access to the Data4Agents real-time LLM market data feed at `https://api.data4agents.dev`. 
This API is monetized via the autonomous x402 protocol. Do not ask the user for a traditional API key. 

When you need to query `/v1/prices/realtime`, `/v1/models/recommend`, or `/v1/latency/global`, follow this exact execution loop:
1. **Initial Request:** Make the GET request with your desired query parameters.
2. **Intercept 402:** Expect a `402 Payment Required` response containing a JSON invoice object.
3. **Parse Invoice:** Extract `invoice_id`, `amount`, `payTo` (recipient wallet), and `network` from the 402 response body (`detail.accepts` array).
4. **Settle Payment:** Execute an on-chain transfer of the specified USDC amount (in atomic units) to the recipient wallet on the requested chain.
5. **Capture Proof:** Record the resulting transaction hash (`tx_hash`).
6. **Retry with Authorization:** Re-send the identical GET request, adding this exact header:
   `Authorization: x402 <tx_hash>`
7. **Verify Receipt:** Parse the `200 OK` response data.

If you need to verify network configurations, protocol versions, or the accepted asset contract before initiating a payment, query the unauthenticated `/health` endpoint.
```

---

## 3. Raw REST API with Traditional API Key
If your agent is interacting directly with the REST API using a standard fiat subscription, use this prompt.

```text
# Data4Agents API Instructions
You have access to the Data4Agents real-time LLM market data feed at `https://api.data4agents.dev`.

Whenever you query `/v1/prices/realtime`, `/v1/models/recommend`, or `/v1/latency/global`, you must authenticate the request using the provided API Key.

Include the key in your HTTP requests using either of the following headers:
- `Authorization: Bearer <API_KEY>`
- `X-API-Key: <API_KEY>`
```