
---

```markdown
# Protocols Understanding – MCP & A2A

## 1. Model Context Protocol (MCP)

### 1.1 Purpose
The **Model Context Protocol** standardizes how AI agents access external tools and data sources (APIs, databases, filesystems, etc.) using a single consistent interface.

Without MCP, each integration would require custom logic. MCP acts like a **universal adapter** between the agent and any tool.

---

### 1.2 Architecture
```

\[ Agent ] → \[ MCP Client ] → \[ MCP Server ] → \[ Tool/API ]

````
- **Agent** – The “brain” (e.g., Dev Assistant).
- **MCP Client** – Inside the agent, sends standard requests.
- **MCP Server** – Wraps a tool or API, exposes functionality in MCP format.
- **Tool/API** – The actual service (GitHub, filesystem, JIRA, etc.).
- **Transport** – Usually HTTP(S) or WebSocket.
- **Format** – JSON-RPC 2.0.

---

### 1.3 Core Methods
| Method         | Purpose |
|----------------|---------|
| `get_methods`  | Lists available tool functions, their parameters, and descriptions. |
| `invoke_method`| Calls a specific function on the tool with given parameters. |

---

### 1.4 JSON-RPC Request/Response Shapes

**`get_methods` request**
```json
{
  "jsonrpc": "2.0",
  "method": "get_methods",
  "id": "1"
}
````

**`get_methods` response**

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": [
    {
      "name": "list_files",
      "params": { "path": "string" },
      "description": "Lists files at a given path"
    }
  ]
}
```

**`invoke_method` request**

```json
{
  "jsonrpc": "2.0",
  "method": "invoke_method",
  "params": {
    "name": "list_files",
    "arguments": { "path": "./mock_knowledge_base" }
  },
  "id": "2"
}
```

**`invoke_method` response**

```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "result": ["file1.txt", "file2.md"]
}
```

**Error response**

```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "error": {
    "code": -32602,
    "message": "Invalid params: path does not exist"
  }
}
```

---

### 1.5 MCP in this Challenge

You will:

1. Run multiple MCP Servers (Filesystem, GitHub, Atlassian…).
2. Build an MCP Proxy that forwards requests to the correct server.
3. Have your Dev Assistant Agent call the proxy to access tools.
4. Test through an IDE like Cursor using the MCP client integration.

---

## 2. Agent-to-Agent Protocol (A2A)

### 2.1 Purpose

The **Agent-to-Agent** protocol standardizes communication between AI agents built by different teams or systems.

It allows agents to:

* Discover each other’s capabilities.
* Call each other’s functions securely.
* Send real-time updates.

---

### 2.2 Architecture

```
[ Agent A ] <—A2A—> [ Agent B ]
```

* **Transport** – HTTP/WebSocket.
* **Format** – JSON-RPC 2.0 for requests/responses.
* **Events** – Often uses SSE (Server-Sent Events) for push updates.
* **Security** – OAuth 2.1 / OpenID Connect recommended.

---

### 2.3 Key Features

* **Agent Cards** – Metadata describing agent capabilities.
* **Capability Discovery** – `get_capabilities` method.
* **Secure Auth** – OAuth/OIDC.
* **Asynchronous Events** – Push updates without polling.

---

### 2.4 Example

**Capability discovery request**

```json
{
  "jsonrpc": "2.0",
  "method": "get_capabilities",
  "id": "1"
}
```

**Capability discovery response**

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "agent_name": "Order Tracker",
    "capabilities": ["get_order_status", "cancel_order"]
  }
}
```

---

## 3. MCP vs A2A

| Feature   | MCP                   | A2A                           |
| --------- | --------------------- | ----------------------------- |
| Connects… | Agents to tools/APIs  | Agents to other agents        |
| Discovery | `get_methods`         | `get_capabilities`            |
| Auth      | Depends on server     | Strongly recommended          |
| Real-time | Not built-in          | Built-in via SSE/WebSockets   |
| Purpose   | Universal tool access | Universal agent collaboration |

---

## 4. How This Fits Your Challenge

1. **Start MCP Servers** – each connected to one tool.
2. **Build MCP Proxy** – one URL for all tool calls.
3. **Build Agent with RAG** – queries local KB + calls tools via proxy.
4. **Test in Cursor IDE** – send MCP commands from chat to proxy.

---

## 5. Visual: Challenge Architecture

```
          ┌────────────────┐
          │ Cursor IDE Chat │
          └───────┬────────┘
                  │ JSON-RPC
                  ▼
          ┌────────────────┐
          │   MCP Proxy    │
          └───────┬────────┘
   routes by /mcp/:target
      ┌────────────┼────────────┐
      ▼            ▼            ▼
[Filesystem]   [GitHub]   [Atlassian]
 MCP Server    MCP Server MCP Server
```

---

## 6. JSON-RPC Recap

**Request**

```json
{
  "jsonrpc": "2.0",
  "method": "<method_name>",
  "params": { ... },
  "id": "unique-id"
}
```

**Response**

```json
{
  "jsonrpc": "2.0",
  "id": "same-as-request",
  "result": { ... } // or
  "error": { "code": ..., "message": "..." }
}
```

---

## 7. Key Takeaways

* MCP = standard way for agents to talk to tools.
* A2A = standard way for agents to talk to other agents.
* Both use JSON-RPC 2.0, so the request/response pattern is consistent.
* In this challenge, you will **only implement MCP flows**, but understanding A2A helps for future scaling.

```

