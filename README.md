# MCP Proxy Gateway Server

This project provides a simple MCP proxy, a dev assistant agent with RAG, and a basic web UI for issuing queries through the agent.

## Development

- `pnpm dev:proxy` – start the proxy server
- `pnpm dev:agent` – run the command line agent
- `pnpm dev:ui` – start the express UI
- `pnpm dev:filesystem` – mock filesystem server on `http://localhost:7001`
- `pnpm dev:github` – mock GitHub server on `http://localhost:7002`
- `pnpm dev:atlassian` – mock Atlassian server on `http://localhost:7003`
- `pnpm dev:gdrive` – mock Google Drive server on `http://localhost:7004`

The UI serves `public/index.html` on `http://localhost:3000/` and exposes an API at `/api/query`.

## Environment Variables

- `GOOGLE_API_KEY` – used for building real embeddings. If unset, tests fall back to deterministic `FakeEmbeddings`.
- `GITHUB_PERSONAL_ACCESS_TOKEN` – required for the GitHub MCP server.
- `PORT` – port for the proxy server (defaults to `8002`).
- `UI_PORT` – port for the web UI (defaults to `3000`).

## Testing

Run all tests with:

```
pnpm test
```
