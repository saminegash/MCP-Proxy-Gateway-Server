# Model Context Protocol (MCP) Documentation

## Overview

The Model Context Protocol (MCP) is an open standard that enables secure connections between host applications (like Claude Desktop, IDEs, or AI tools) and data sources (like content management systems, business tools, or development servers). It provides a standardized way for AI applications to securely connect to and interact with various data sources and tools.

## Core Concepts

### Architecture

MCP follows a client-server architecture where:

- **MCP Hosts/Clients**: Applications like Claude Desktop, IDEs, or AI tools that want to access data
- **MCP Servers**: Programs that provide access to specific data sources or tools
- **Transport Layer**: Communication mechanism between clients and servers

### Key Components

1. **Resources**: File-like objects that servers can provide (documents, database records, API responses)
2. **Tools**: Functions that clients can invoke on servers (database queries, API calls, file operations)
3. **Prompts**: Templates that help clients interact with resources effectively

## Transport Methods

### 1. STDIO Transport (Recommended for Local Use)

STDIO transport runs the MCP server as a subprocess and communicates through standard input/output streams.

**Configuration Example:**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--mount", "type=bind,src=/home/sam/Documents,dst=/project",
        "mcp/filesystem",
        "/project"
      ],
      "env": {}
    }
  }
}
```

**Advantages:**
- Lower latency
- Simpler setup for local integrations
- No network configuration required
- Preferred method by Anthropic

**Use Cases:**
- Local file system access
- Desktop applications
- Development tools
- Single-user scenarios

### 2. HTTP/SSE Transport

HTTP transport with Server-Sent Events for real-time communication over HTTP.

**Configuration Example:**
```json
{
  "mcpServers": {
    "web-service": {
      "url": "http://localhost:8001/sse",
      "name": "My Web Service"
    }
  }
}
```

**Advantages:**
- Network accessible
- Multi-client support
- Standard web protocols
- Better for distributed systems

**Use Cases:**
- Remote data sources
- Web services
- Multi-user environments
- Cloud deployments

### 3. Streamable HTTP Transport (Latest)

Introduced in 2025-03-26, this is the newest transport method for HTTP-based communication.

**Configuration Example:**
```json
{
  "mcpServers": {
    "streamable-service": {
      "type": "streamable-http",
      "url": "http://localhost:3000"
    }
  }
}
```

## Protocol Specification

### Version: 2025-06-18 (Current)

MCP uses JSON-RPC 2.0 as its base communication protocol with specific message types:

#### Request Messages
```json
{
  "jsonrpc": "2.0",
  "id": "string|number",
  "method": "string",
  "params": {
    "key": "value"
  }
}
```

#### Response Messages
```json
{
  "jsonrpc": "2.0",
  "id": "string|number",
  "result": {
    "data": "value"
  }
}
```

#### Notification Messages
```json
{
  "jsonrpc": "2.0",
  "method": "string",
  "params": {
    "key": "value"
  }
}
```

### Lifecycle Management

1. **Initialization**: Client and server establish connection and negotiate capabilities
2. **Capability Negotiation**: Exchange of supported features and protocol versions
3. **Operation**: Normal request/response cycles for tools, resources, and prompts
4. **Termination**: Graceful connection closure

## Configuration

### Claude Desktop Configuration

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Example Configuration:**
```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "github-mcp-server"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"
      }
    },
    "filesystem": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--mount", "type=bind,src=/home/sam/Documents,dst=/project",
        "mcp/filesystem",
        "/project"
      ],
      "env": {}
    },
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--isolated",
        "--vision"
      ]
    }
  }
}
```

### Environment Variables

Common environment variables used in MCP configurations:

- `GITHUB_PERSONAL_ACCESS_TOKEN`: For GitHub MCP server
- `CONFLUENCE_URL`, `CONFLUENCE_USERNAME`, `CONFLUENCE_API_TOKEN`: For Atlassian servers
- `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`: For JIRA integration
- `CLIENT_ID`, `CLIENT_SECRET`: For OAuth-based services

## Implementation Examples

### Python Server Example

```python
from mcp import Server, StdioServerTransport
import asyncio

# Initialize server
server = Server("my-server")

@server.tool()
async def add_numbers(a: int, b: int) -> str:
    """Add two numbers together."""
    result = a + b
    return f"The sum of {a} and {b} is {result}"

async def main():
    # Create stdio transport
    transport = StdioServerTransport()
    
    # Connect server to transport
    await server.connect(transport)

if __name__ == "__main__":
    asyncio.run(main())
```

### TypeScript Server Example

```typescript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

// Create server
const server = new Server(
  {
    name: "my-server",
    version: "1.0.0"
  },
  {
    capabilities: {
      tools: {
        add: {
          description: "Add two numbers",
          inputSchema: {
            type: "object",
            properties: {
              a: { type: "number" },
              b: { type: "number" }
            },
            required: ["a", "b"]
          }
        }
      }
    }
  }
);

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  if (name === "add") {
    const sum = args.a + args.b;
    return {
      content: [
        {
          type: "text",
          text: `${args.a} + ${args.b} = ${sum}`
        }
      ]
    };
  }
  
  throw new Error(`Unknown tool: ${name}`);
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Client Implementation

```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

// Create client
const client = new Client(
  {
    name: "my-client",
    version: "1.0.0"
  },
  {
    capabilities: {}
  }
);

// Create transport to server
const transport = new StdioClientTransport({
  command: "node",
  args: ["path/to/server.js"]
});

// Connect to server
await client.connect(transport);

// Call a tool
const result = await client.request(
  {
    method: "tools/call",
    params: {
      name: "add",
      arguments: { a: 5, b: 3 }
    }
  }
);

console.log(result);
```

## Popular MCP Servers

### Official Servers

1. **GitHub MCP Server**: Provides access to GitHub repositories, issues, and pull requests
2. **Filesystem MCP Server**: Local and remote file system access
3. **Brave Search MCP Server**: Web search capabilities
4. **Slack MCP Server**: Slack workspace integration

### Community Servers

1. **PostgreSQL MCP Server**: Database query and management
2. **Atlassian MCP Server**: JIRA and Confluence integration
3. **Google Drive MCP Server**: Google Drive file access
4. **Playwright MCP Server**: Web automation and testing

## Security Considerations

### Authentication

MCP supports multiple authentication strategies:

1. **Environment Variables**: For API keys and tokens
2. **OAuth 2.0**: For services requiring user consent
3. **Custom Authentication**: Server-specific auth mechanisms

### Best Practices

1. **Least Privilege**: Grant minimal necessary permissions
2. **Token Management**: Secure storage and rotation of API keys
3. **Network Security**: Use HTTPS for remote connections
4. **Input Validation**: Validate all user inputs on server side
5. **Rate Limiting**: Implement appropriate rate limiting

## Development Tools

### MCP Inspector

A debugging tool for MCP servers:

```bash
npm install -g @modelcontextprotocol/inspector
mcp-inspector
```

### SDK Documentation

- **TypeScript SDK**: `@modelcontextprotocol/sdk`
- **Python SDK**: `mcp` package
- **Go SDK**: Community maintained

## Common Patterns

### Resource Management

```typescript
// List resources
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "file:///example.txt",
        name: "Example File",
        description: "An example text file",
        mimeType: "text/plain"
      }
    ]
  };
});

// Read resource
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;
  
  if (uri === "file:///example.txt") {
    return {
      contents: [
        {
          uri: uri,
          mimeType: "text/plain",
          text: "Hello, World!"
        }
      ]
    };
  }
  
  throw new Error(`Resource not found: ${uri}`);
});
```

### Tool Implementation

```typescript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  switch (name) {
    case "file_operations":
      // Handle file operations
      break;
    case "database_query":
      // Handle database queries
      break;
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});
```

## Troubleshooting

### Common Issues

1. **Connection Failures**:
   - Check server process is running
   - Verify configuration file syntax
   - Ensure correct paths and commands

2. **Authentication Errors**:
   - Verify environment variables
   - Check token validity
   - Confirm permissions

3. **Tool Execution Failures**:
   - Validate input parameters
   - Check server logs
   - Verify tool implementation

### Debugging Tips

1. Use MCP Inspector for development
2. Enable verbose logging
3. Test servers independently
4. Validate JSON-RPC messages

## Future Considerations

### Upcoming Features

- Enhanced security models
- Improved streaming capabilities
- Better error handling
- Extended transport options

### Migration Guidelines

- Monitor protocol version updates
- Test backward compatibility
- Plan for deprecation cycles
- Update dependencies regularly

## Resources

### Official Documentation

- **MCP Specification**: https://spec.modelcontextprotocol.io/
- **GitHub Repository**: https://github.com/modelcontextprotocol/docs
- **TypeScript SDK**: https://www.npmjs.com/package/@modelcontextprotocol/sdk

### Community Resources

- **Claude MCP Community**: https://www.claudemcp.com/
- **Discord Community**: Various MCP development channels
- **GitHub Discussions**: Community Q&A and feature requests

### Examples and Tutorials

- **Quickstart Guide**: https://modelcontextprotocol.io/quickstart
- **Server Examples**: Multiple language implementations
- **Best Practices**: Community-driven guidelines

---

This documentation provides a comprehensive overview of the Model Context Protocol. For the most up-to-date information, always refer to the official specification and documentation.