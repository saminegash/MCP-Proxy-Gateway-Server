# MCP Proxy Gateway Server

This project provides a simple MCP proxy, a dev assistant agent with RAG, and a basic web UI for issuing queries through the agent.

## Architecture
```
           ┌────────────┐
           │ IDE / UI   │
           └─────┬──────┘
                 │ HTTP + MCP
                 ▼
           ┌────────────┐
           │ Proxy Gate │
           └─┬──────────┘
       routes /mcp/:target
     ┌──────┴──────┬────────┐
     │             │        │
Filesystem     GitHub  Atlassian
MCP Server  MCP Server MCP Server
```

## Setup
1. Install Node.js and [pnpm](https://pnpm.io/).
2. Install dependencies:
   ```bash
   pnpm install
   ```
3. (Optional) Customize environment variables in a `.env` file.

## Development
- `pnpm dev:proxy` – start the proxy server
- `pnpm dev:agent` – run the command line agent
- `pnpm dev:ui` – start the express UI

The UI serves `public/index.html` on `http://localhost:3000/` and exposes an API at `/api/query`.

## Testing
Run all tests with:
```bash
pnpm test
```

## Documentation
- [MCP Documentation](docs/MCP_DOCUMENTATION.md)
- [Protocols Understanding – MCP & A2A](docs/protocols_understanding.md)
- [Real-Time RAG Notes](docs/realtime_rag_notes.md)
- [Advanced MCP Concepts](docs/advanced_mcp_concepts.md)
- [IDE MCP Integration](docs/ide_mcp_integration.md)
