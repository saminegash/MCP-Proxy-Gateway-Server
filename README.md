# MCP Agent Proxy System

A comprehensive Model Context Protocol (MCP) implementation featuring a proxy server, intelligent agent with RAG capabilities, mock servers, and a web interface. This system demonstrates how to build a scalable MCP infrastructure for AI development and integration.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Layer  │    │   Proxy Layer   │    │  Server Layer   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │   Web UI    │ │◄──►│ │ MCP Proxy   │ │◄──►│ │ Filesystem  │ │
│ └─────────────┘ │    │ │   Server    │ │    │ │   Server    │ │
│                 │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │       │         │    │ ┌─────────────┐ │
│ │MCP Client   │ │◄───┼───────┼─────────┼────┤ │   GitHub    │ │
│ │   Tester    │ │    │       │         │    │ │   Server    │ │
│ └─────────────┘ │    │ ┌─────▼─────┐   │    │ └─────────────┘ │
│                 │    │ │    RAG    │   │    │ ┌─────────────┐ │
│ ┌─────────────┐ │    │ │  Agent    │   │    │ │ Atlassian   │ │
│ │ Dev Agent   │ │◄──►│ │           │   │    │ │   Server    │ │
│ │   (CLI)     │ │    │ └───────────┘   │    │ └─────────────┘ │
│ └─────────────┘ │    │                 │    │ ┌─────────────┐ │
└─────────────────┘    └─────────────────┘    │ │   GDrive    │ │
                                              │ │   Server    │ │
                                              │ └─────────────┘ │
                                              └─────────────────┘
```

## ✨ Features

- **🔄 MCP Proxy Server**: Centralized gateway routing requests to multiple MCP servers
- **🤖 AI Agent with RAG**: Intelligent assistant with Retrieval-Augmented Generation
- **🧪 Mock MCP Servers**: Ready-to-use implementations for Filesystem, GitHub, Atlassian, and Google Drive
- **🌐 Web Interface**: User-friendly UI for interacting with the agent
- **🔧 Client Tester**: Command-line tool for testing MCP communications
- **📚 Knowledge Base**: Mock documentation, code, and tickets for RAG testing
- **✅ Comprehensive Testing**: Full test suite with mocking and integration tests

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ 
- pnpm package manager
- (Optional) Google API key for real embeddings

### Installation

1. **Clone and install dependencies:**
   ```bash
   git clone <repository-url>
   cd agent-proxy
   pnpm install
   ```

2. **Set up environment variables (optional):**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services:**
   ```bash
   # Terminal 1: Start MCP Proxy
   pnpm dev:proxy

   # Terminal 2: Start Mock Servers (in separate terminals)
   pnpm dev:filesystem    # Port 7001
   pnpm dev:github        # Port 7002  
   pnpm dev:atlassian     # Port 7003
   pnpm dev:gdrive        # Port 7004

   # Terminal 3: Start Web UI
   pnpm dev:ui            # Port 3000
   ```

4. **Test the system:**
   ```bash
   # Terminal 4: Test client
   pnpm dev:client

   # Terminal 5: Test agent
   pnpm dev:agent "filesystem list files"
   ```

## 🛠️ Components

### 1. MCP Proxy Server (`src/proxy/server.ts`)
Central routing hub that forwards JSON-RPC requests to appropriate downstream MCP servers.

- **Port**: 8002 (configurable via `PORT`)
- **Routes**: `/mcp/:target` where target is `filesystem|github|atlassian|gdrive`
- **Features**: Request validation, error handling, method aggregation

### 2. Dev Assistant Agent (`src/agent/`)
AI-powered assistant combining MCP tool calling with RAG-enhanced responses.

- **Core**: `agent.ts` - Query parsing and handling
- **Runner**: `run.ts` - CLI interface
- **Features**: Tool selection, MCP integration, knowledge retrieval

### 3. RAG System (`src/rag/setup.ts`)
Vector-based retrieval system over the mock knowledge base.

- **Embeddings**: Google Generative AI or Fake (fallback)
- **Chunking**: RecursiveCharacterTextSplitter (1000 chars, 200 overlap)
- **Storage**: In-memory vector store
- **Knowledge Base**: `mock_knowledge_base/` (docs, code, tickets)

### 4. Mock MCP Servers (`src/servers/`)
Production-ready mock implementations demonstrating MCP patterns.

#### Filesystem Server (`:7001`)
- `list_files` - Directory listing
- `read_file` - File content retrieval

#### GitHub Server (`:7002`)  
- `list_repos` - Repository listing
- `get_repo` - Repository details

#### Atlassian Server (`:7003`)
- `list_projects` - Project listing  
- `get_project` - Project details

#### Google Drive Server (`:7004`)
- `list_files` - Drive file listing
- `get_file` - File content retrieval

### 5. Web UI (`src/ui/server.ts`, `public/index.html`)
Simple web interface for agent interaction.

- **Port**: 3000 (configurable via `UI_PORT`)
- **API**: `POST /api/query` - Send queries to agent
- **Frontend**: Vanilla JavaScript form interface

### 6. MCP Client Tester (`src/client/mcpClientTester.ts`)
Command-line tool for testing MCP server communication.

```bash
# Usage examples
pnpm dev:client filesystem get_methods
pnpm dev:client github list_repos
pnpm dev:client filesystem list_files '{"path":"."}'
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Proxy server port | `8002` |
| `UI_PORT` | Web UI port | `3000` |
| `GOOGLE_API_KEY` | Google API key for embeddings | _None (uses fake embeddings)_ |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | GitHub API token | _None_ |
| `MCP_FILESYSTEM_URL` | Filesystem server URL | `http://localhost:7001` |
| `MCP_GITHUB_URL` | GitHub server URL | `http://localhost:7002` |
| `MCP_ATLASSIAN_URL` | Atlassian server URL | `http://localhost:7003` |
| `MCP_GDRIVE_URL` | Google Drive server URL | `http://localhost:7004` |

### MCP Configuration (`src/config/targets.ts`)
The system can load MCP server configurations from `~/.cursor/mcp.json` for integration with Cursor IDE, falling back to environment-based URLs.

## 🧪 Testing

```bash
# Run all tests
pnpm test

# Run specific test suites
pnpm test agent.test.ts
pnpm test proxy.test.ts
pnpm test ui.test.ts
pnpm test e2e.test.ts

# Run with coverage
pnpm test --coverage
```

### Test Structure
- **Unit Tests**: Individual component testing with mocking
- **Integration Tests**: Cross-component communication testing  
- **E2E Tests**: Full system workflow testing
- **Mock Servers**: Dedicated test servers with nock interception

## 📁 Project Structure

```
agent-proxy/
├── src/
│   ├── agent/           # AI agent with RAG
│   ├── client/          # MCP client tester
│   ├── config/          # Configuration management
│   ├── proxy/           # MCP proxy server
│   ├── rag/             # RAG implementation
│   ├── servers/         # Mock MCP servers
│   └── ui/              # Web interface
├── tests/               # Test suites
├── mock_knowledge_base/ # Sample data for RAG
│   ├── docs/           # Documentation files
│   ├── code/           # Code examples
│   ├── tickets/        # JIRA tickets
│   └── jira_tickets.json
├── public/             # Web UI assets
└── docs/               # Project documentation
```

## 🔗 API Reference

### Agent Query Format
The agent accepts natural language queries that get parsed into MCP calls:

```bash
# Format: [tool] [action] [key=value ...]
"filesystem list_files path=./src"
"github get_repo name=example"
"atlassian get_project key=TEST"
```

### MCP JSON-RPC Format
All MCP communication follows JSON-RPC 2.0:

```json
{
  "jsonrpc": "2.0",
  "method": "invoke_method",
  "params": {
    "method": "list_files",
    "path": "./src"
  },
  "id": "request-1"
}
```

## 📚 Knowledge Base

The `mock_knowledge_base/` directory contains sample data demonstrating real-world RAG scenarios:

- **Documentation**: Technical specs, design docs, API documentation
- **Code Examples**: Sample commits with explanations
- **JIRA Tickets**: Structured ticket data with references
- **Cross-References**: Links between tickets, commits, and documentation

## 🚀 Deployment

### Production Checklist

1. **Environment Setup**:
   - Set production environment variables
   - Configure real Google API key for embeddings
   - Set up proper logging and monitoring

2. **Security**:
   - Enable HTTPS/TLS
   - Configure authentication/authorization  
   - Validate all input parameters
   - Set up rate limiting

3. **Scaling**:
   - Use process managers (PM2, Docker)
   - Configure load balancing for proxy
   - Set up health checks
   - Monitor performance metrics

### Docker Support
```dockerfile
# Example Dockerfile structure
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build
EXPOSE 8002 3000
CMD ["pnpm", "start"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Ensure all tests pass (`pnpm test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📖 Documentation

- [🔧 MCP Protocol Documentation](docs/MCP_DOCUMENTATION.md)
- [🌐 Protocols Understanding](docs/protocols_understanding.md)
- [⚡ Real-Time RAG Notes](docs/realtime_rag_notes.md)
- [🚀 Advanced MCP Concepts](docs/advanced_mcp_concepts.md)
- [💻 IDE Integration Guide](docs/ide_mcp_integration.md)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- Model Context Protocol specification and community
- LangChain for RAG implementation
- FastMCP for TypeScript MCP utilities
- Google Generative AI for embeddings
