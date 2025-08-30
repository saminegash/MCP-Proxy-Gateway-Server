# MCP Proxy Gateway Server

This project provides a simple MCP proxy, a dev assistant agent with RAG, and a basic web UI for issuing queries through the agent.

## Development

- `pnpm dev:proxy` – start the proxy server
- `pnpm dev:agent` – run the command line agent
- `pnpm dev:ui` – start the express UI

The UI serves `public/index.html` on `http://localhost:3000/` and exposes an API at `/api/query`.

## Testing

Run all tests with:

```
pnpm test
```
