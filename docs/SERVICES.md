# Service Documentation

This document provides detailed information about each service in the MCP Agent Proxy System.

## 📋 Service Overview

| Service | Port | Purpose | Dependencies |
|---------|------|---------|--------------|
| MCP Proxy Server | 8002 | Route requests to downstream MCP servers | None |
| Web UI | 3000 | Web interface for agent interaction | MCP Proxy, Agent |
| Filesystem Server | 7001 | Mock filesystem MCP operations | None |
| GitHub Server | 7002 | Mock GitHub MCP operations | None |
| Atlassian Server | 7003 | Mock Atlassian MCP operations | None |
| Google Drive Server | 7004 | Mock Google Drive MCP operations | None |

## 🔄 MCP Proxy Server

**File**: `src/proxy/server.ts`  
**Port**: 8002 (configurable via `PORT`)  
**Purpose**: Central gateway that routes JSON-RPC requests to appropriate downstream MCP servers

### Features

- **Request Routing**: Routes `/mcp/:target` to configured downstream servers
- **JSON-RPC Validation**: Validates incoming requests against JSON-RPC 2.0 schema
- **Error Handling**: Comprehensive error handling with proper HTTP status codes
- **Method Aggregation**: `GET /mcp/get_methods` endpoint to discover all available methods

### Configuration

The proxy reads server URLs from environment variables:

```bash
MCP_FILESYSTEM_URL=http://localhost:7001
MCP_GITHUB_URL=http://localhost:7002
MCP_ATLASSIAN_URL=http://localhost:7003
MCP_GDRIVE_URL=http://localhost:7004
```

### API Endpoints

#### POST `/mcp/:target`
Routes JSON-RPC requests to the specified target server.

**Example**:
```bash
curl -X POST http://localhost:8002/mcp/filesystem \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "invoke_method",
    "params": {"method": "list_files", "path": "."},
    "id": "1"
  }'
```

#### GET `/mcp/get_methods`
Aggregates available methods from all downstream servers.

### Error Handling

- **404**: Unknown target server
- **400**: Invalid JSON-RPC request
- **500**: Downstream server errors or proxy errors
- **Timeout**: 15-second timeout for downstream requests

### Usage

```bash
# Start proxy server
pnpm dev:proxy

# Or in production
pnpm build && pnpm start
```

## 🌐 Web UI Server

**File**: `src/ui/server.ts`, `public/index.html`  
**Port**: 3000 (configurable via `UI_PORT`)  
**Purpose**: Web interface for interacting with the Dev Assistant Agent

### Features

- **Simple Interface**: Clean HTML form for query input
- **Agent Integration**: Directly calls the agent's `handleQuery` function
- **Real-time Results**: Displays JSON responses with syntax highlighting

### API Endpoints

#### GET `/`
Serves the main HTML interface from `public/index.html`.

#### POST `/api/query`
Processes agent queries and returns results.

**Request**:
```json
{
  "query": "filesystem list_files path=./src"
}
```

**Response**:
```json
{
  "parsed": {
    "tool": "filesystem",
    "action": "list_files", 
    "args": {"path": "./src"}
  },
  "mcpSnippet": ["agent.ts", "run.ts"],
  "ragContextPreview": [...]
}
```

### Frontend

Simple vanilla JavaScript interface:
- Input field for natural language queries
- Submit button to send requests
- Pre-formatted output area for results
- Error handling and display

### Usage

```bash
# Start UI server
pnpm dev:ui

# Open browser
open http://localhost:3000
```

## 🤖 Dev Assistant Agent

**Files**: `src/agent/agent.ts`, `src/agent/run.ts`  
**Purpose**: AI-powered assistant combining MCP tool calling with RAG-enhanced responses

### Core Components

#### Query Parser (`parseQuery`)
Parses natural language into structured MCP calls:

```typescript
parseQuery("filesystem list_files path=./src")
// Returns: { tool: "filesystem", action: "list_files", args: { path: "./src" } }
```

**Supported Tools**: `filesystem`, `github`, `atlassian`, `gdrive`

#### Query Handler (`handleQuery`)
Orchestrates the full query processing pipeline:

1. **Parse Query**: Extract tool, action, and arguments
2. **MCP Call**: Send JSON-RPC request via proxy
3. **RAG Retrieval**: Get relevant documents from knowledge base
4. **Response Synthesis**: Combine MCP results with RAG context

### RAG Integration

The agent uses a retrieval system built on:
- **Vector Store**: In-memory storage with similarity search
- **Embeddings**: Google Generative AI or fake embeddings (fallback)
- **Knowledge Base**: Documents, code, and tickets from `mock_knowledge_base/`

### CLI Interface

```bash
# Run single query
pnpm dev:agent "filesystem list_files"

# Interactive mode
node dist/agent/run.js
```

### Response Format

```json
{
  "parsed": {
    "tool": "filesystem",
    "action": "list_files",
    "args": {}
  },
  "mcpSnippet": ["file1.txt", "file2.txt"],
  "ragContextPreview": [
    {
      "file": "docs/api.md",
      "text": "API documentation content..."
    }
  ]
}
```

## 📁 Filesystem Server

**File**: `src/servers/filesystem-mock.ts`  
**Port**: 7001  
**Purpose**: Mock filesystem operations via MCP protocol

### Available Methods

#### `list_files`
List files and directories in the specified path.

**Parameters**:
- `path` (string): Directory path to list (default: ".")

**Example**:
```json
{
  "jsonrpc": "2.0",
  "method": "invoke_method",
  "params": {
    "method": "list_files",
    "arguments": {"path": "./src"}
  },
  "id": "1"
}
```

#### `read_file`
Read the contents of a file.

**Parameters**:
- `path` (string): File path to read

**Example**:
```json
{
  "jsonrpc": "2.0", 
  "method": "invoke_method",
  "params": {
    "method": "read_file",
    "arguments": {"path": "./package.json"}
  },
  "id": "1"
}
```

### Error Handling

- **File not found**: Returns error for invalid paths
- **Permission denied**: Returns error for inaccessible files
- **Invalid method**: Returns JSON-RPC error for unknown methods

### Usage

```bash
# Start server
pnpm dev:filesystem

# Test with client
pnpm dev:client filesystem list_files '{"path":"."}'
```

## 🐙 GitHub Server

**File**: `src/servers/github-mock.ts`  
**Port**: 7002  
**Purpose**: Mock GitHub operations via MCP protocol

### Available Methods

#### `list_repos`
List repositories for the authenticated user.

**Parameters**: None

**Response**: Array of repository names

#### `get_repo`
Get details for a specific repository.

**Parameters**:
- `name` (string): Repository name (default: "example-repo")

**Response**: Repository object with name and stars

### Usage

```bash
# Start server
pnpm dev:github

# Test with client  
pnpm dev:client github list_repos
pnpm dev:client github get_repo '{"name":"my-repo"}'
```

## 🔷 Atlassian Server

**File**: `src/servers/atlassian-mock.ts`  
**Port**: 7003  
**Purpose**: Mock Atlassian/JIRA operations via MCP protocol

### Available Methods

#### `list_projects`
List available Atlassian projects.

**Parameters**: None

**Response**: Array of project objects with key and name

#### `get_project`
Get details for a specific project.

**Parameters**:
- `key` (string): Project key (default: "TEST")

**Response**: Project object with key and name

### Usage

```bash
# Start server
pnpm dev:atlassian

# Test with client
pnpm dev:client atlassian list_projects
pnpm dev:client atlassian get_project '{"key":"PROJ"}'
```

## 📊 Google Drive Server

**File**: `src/servers/gdrive-mock.ts`  
**Port**: 7004  
**Purpose**: Mock Google Drive operations via MCP protocol

### Available Methods

#### `list_files`
List files in Google Drive.

**Parameters**: None

**Response**: Array of file objects with id and name

#### `get_file`
Get contents of a specific file.

**Parameters**:
- `id` (string): File ID (default: "1")

**Response**: File object with id, name, and content

### Usage

```bash
# Start server  
pnpm dev:gdrive

# Test with client
pnpm dev:client gdrive list_files
pnpm dev:client gdrive get_file '{"id":"123"}'
```

## 🔧 MCP Client Tester

**File**: `src/client/mcpClientTester.ts`  
**Purpose**: Command-line tool for testing MCP server communication

### Usage Patterns

```bash
# Basic method call
pnpm dev:client [target] [method] [params] [proxyBase]

# Examples
pnpm dev:client filesystem get_methods
pnpm dev:client github list_repos  
pnpm dev:client filesystem list_files '{"path":"./src"}'
pnpm dev:client atlassian get_project '{"key":"TEST"}' http://localhost:8002
```

### Parameters

- `target`: Server target (filesystem, github, atlassian, gdrive)
- `method`: MCP method to call (default: "get_methods")
- `params`: JSON string of method parameters (default: "{}")
- `proxyBase`: Proxy server URL (default: "http://localhost:8002")

### Output

Pretty-printed JSON response from the MCP server:

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": ["file1.txt", "file2.txt"]
}
```

## 🚀 Starting All Services

### Development Mode

```bash
# Terminal 1: MCP Proxy Server
pnpm dev:proxy

# Terminal 2-5: Mock Servers  
pnpm dev:filesystem
pnpm dev:github
pnpm dev:atlassian
pnpm dev:gdrive

# Terminal 6: Web UI
pnpm dev:ui

# Terminal 7: Test with agent
pnpm dev:agent "filesystem list_files"
```

### Production Mode

```bash
# Build all services
pnpm build

# Start proxy and UI
pnpm start &
pnpm start:ui &

# Start mock servers
node dist/servers/filesystem-mock.js &
node dist/servers/github-mock.js &
node dist/servers/atlassian-mock.js &
node dist/servers/gdrive-mock.js &
```

## 🔍 Health Checks

### Service Status
Check if services are running:

```bash
# Proxy server
curl http://localhost:8002/mcp/get_methods

# Mock servers
curl -X POST http://localhost:7001 -d '{"jsonrpc":"2.0","method":"get_methods","id":"1"}'
curl -X POST http://localhost:7002 -d '{"jsonrpc":"2.0","method":"get_methods","id":"1"}'
curl -X POST http://localhost:7003 -d '{"jsonrpc":"2.0","method":"get_methods","id":"1"}'
curl -X POST http://localhost:7004 -d '{"jsonrpc":"2.0","method":"get_methods","id":"1"}'

# Web UI
curl http://localhost:3000
```

### System Integration Test

```bash
# Full system test via UI
curl -X POST http://localhost:3000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "filesystem list_files"}'
```

## 🐛 Troubleshooting

### Common Issues

1. **Port conflicts**: Services use fixed ports, ensure they're available
2. **Missing dependencies**: Run `pnpm install` before starting
3. **Proxy timeout**: Increase timeout in `src/proxy/server.ts` if needed
4. **RAG embeddings**: Set `GOOGLE_API_KEY` for real embeddings vs fake

### Logs

Each service logs to console:
- Startup messages with port information
- Request/response details
- Error messages with stack traces

### Debug Mode

Add debug logging to any service:

```typescript
// Enable debug logging
process.env.DEBUG = 'mcp:*';
```