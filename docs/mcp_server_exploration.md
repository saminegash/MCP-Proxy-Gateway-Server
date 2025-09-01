# MCP Server Exploration

This document demonstrates using `mcpClientTester.ts` to interact with the mock MCP servers through the proxy.

## Filesystem Mock Server

### `get_methods`

```bash
npx ts-node src/client/mcpClientTester.ts filesystem get_methods
```

Sample response:

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": [
    { "name": "list_files", "params": { "path": "string" }, "description": "List files in a directory" },
    { "name": "read_file",  "params": { "path": "string" }, "description": "Read a file" }
  ]
}
```

### `invoke_method` – `list_files`

```bash
npx ts-node src/client/mcpClientTester.ts filesystem invoke_method '{"name":"list_files","arguments":{"path":"mock_knowledge_base"}}'
```

Sample response:

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": [
    "code",
    "docs",
    "jira_tickets.json",
    "tickets"
  ]
}
```

### `invoke_method` – `read_file`

```bash
npx ts-node src/client/mcpClientTester.ts filesystem invoke_method '{"name":"read_file","arguments":{"path":"mock_knowledge_base/jira_tickets.json"}}'
```

Sample response (truncated):

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": "[\n    {\n      \"ticket_id\": \"NEX-123\", ..."
}
```

These examples show how different MCP calls can be issued through the proxy using the target key, method name, and JSON parameters.

