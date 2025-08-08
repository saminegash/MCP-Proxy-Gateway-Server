# Agent-to-Agent (A2A) Protocol Specification

This document outlines the implementation and usage of the Agent-to-Agent (A2A) protocol for secure inter-agent communication in the NexusAI platform.

## Overview

The A2A protocol enables different AI agents to discover, communicate, and collaborate with each other in a secure and standardized manner. It builds upon web standards like HTTP, WebSockets, and JSON-RPC while adding agent-specific capabilities.

## Protocol Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agent A       │    │  A2A Gateway    │    │   Agent B       │
│                 │◄──►│                 │◄──►│                 │
│  - Discovery    │    │ - Routing       │    │ - Capabilities  │
│  - Auth         │    │ - Security      │    │ - Processing    │
│  - Messaging    │    │ - Monitoring    │    │ - Responses     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Transport Layers

1. **HTTP/HTTPS**: For request-response interactions
2. **WebSockets**: For real-time bidirectional communication
3. **Server-Sent Events (SSE)**: For push notifications and updates

## Agent Discovery

### Agent Card Format

Each agent publishes an Agent Card describing its capabilities:

```json
{
  "agent_id": "nexus-task-agent-v1",
  "name": "NexusAI Task Management Agent",
  "version": "1.2.0",
  "description": "Manages tasks, projects, and team collaboration",
  "capabilities": [
    {
      "name": "task_management",
      "methods": ["create_task", "update_task", "list_tasks", "delete_task"],
      "description": "Complete task lifecycle management"
    },
    {
      "name": "project_coordination", 
      "methods": ["create_project", "assign_resources", "track_progress"],
      "description": "Project planning and coordination"
    }
  ],
  "interfaces": {
    "http": {
      "base_url": "https://agents.nexusai.com/task-agent/v1",
      "auth_required": true,
      "rate_limits": {
        "requests_per_minute": 100,
        "burst_limit": 20
      }
    },
    "websocket": {
      "url": "wss://agents.nexusai.com/task-agent/v1/ws",
      "protocols": ["a2a-v1", "json-rpc-2.0"]
    }
  },
  "authentication": {
    "methods": ["oauth2", "jwt"],
    "scopes": ["task:read", "task:write", "project:read", "project:write"]
  },
  "schemas": {
    "task": "https://schemas.nexusai.com/task.json",
    "project": "https://schemas.nexusai.com/project.json"
  },
  "metadata": {
    "tags": ["productivity", "collaboration", "project-management"],
    "owner": "NexusAI Platform Team",
    "contact": "support@nexusai.com",
    "documentation": "https://docs.nexusai.com/agents/task-agent",
    "status": "production"
  },
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-25T14:30:00Z"
}
```

### Discovery Endpoints

#### GET /agents
List available agents with filtering capabilities.

**Query Parameters:**
- `capability`: Filter by capability name
- `tags`: Comma-separated list of tags
- `status`: Filter by status (development, staging, production)

**Response:**
```json
{
  "agents": [
    {
      "agent_id": "nexus-task-agent-v1",
      "name": "NexusAI Task Management Agent",
      "status": "production",
      "capabilities": ["task_management", "project_coordination"]
    }
  ],
  "total": 1,
  "page": 1
}
```

#### GET /agents/{agent_id}
Get detailed information about a specific agent.

## Communication Protocols

### JSON-RPC 2.0 over HTTP

Standard request format:
```json
{
  "jsonrpc": "2.0",
  "method": "task_management.create_task",
  "params": {
    "title": "Implement A2A authentication",
    "description": "Add OAuth 2.0 support for agent-to-agent communication",
    "priority": "high",
    "assignee": "security_team"
  },
  "id": "req_12345"
}
```

Response format:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "task_id": "task_789",
    "status": "created",
    "created_at": "2024-01-26T10:30:00Z"
  },
  "id": "req_12345"
}
```

Error response:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "field": "priority",
      "reason": "Must be one of: low, medium, high, critical"
    }
  },
  "id": "req_12345"
}
```

### WebSocket Communication

#### Connection Establishment
```javascript
const ws = new WebSocket('wss://agents.nexusai.com/task-agent/v1/ws', ['a2a-v1']);

ws.onopen = function() {
  // Send authentication
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'jwt_token_here'
  }));
};
```

#### Real-time Updates
```json
{
  "jsonrpc": "2.0",
  "method": "task_management.task_updated",
  "params": {
    "task_id": "task_789",
    "changes": {
      "status": "completed",
      "completed_at": "2024-01-26T15:45:00Z"
    },
    "updated_by": "nexus-dev-agent-v2"
  }
}
```

### Server-Sent Events

For one-way notifications:
```
GET /agents/task-agent/v1/events
Accept: text/event-stream
Authorization: Bearer jwt_token

event: task_created
data: {"task_id": "task_790", "title": "New security review"}

event: project_milestone
data: {"project_id": "proj_123", "milestone": "Phase 1 Complete"}
```

## Authentication & Authorization

### OAuth 2.0 Client Credentials Flow

1. **Agent Registration**: Agents register with the A2A platform
2. **Client Credentials**: Receive client_id and client_secret
3. **Token Request**: Request access tokens for communication
4. **Token Usage**: Include tokens in requests

#### Token Request
```bash
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_id=nexus-data-agent&
client_secret=agent_secret&
scope=task:read+task:write
```

#### Token Response
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "task:read task:write"
}
```

### JWT Token Structure

```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT"
  },
  "payload": {
    "iss": "https://auth.nexusai.com",
    "sub": "nexus-data-agent",
    "aud": ["nexus-task-agent", "nexus-notification-agent"],
    "exp": 1706278800,
    "iat": 1706275200,
    "scope": ["task:read", "task:write"],
    "agent_id": "nexus-data-agent-v1",
    "agent_type": "data_processing"
  }
}
```

## Security Considerations

### Transport Security
- **TLS 1.3**: All communications encrypted in transit
- **Certificate Pinning**: Prevent man-in-the-middle attacks
- **HSTS**: Force HTTPS connections

### Authentication Security
- **Token Rotation**: Regular token refresh (1-hour expiry)
- **Scope Limitation**: Principle of least privilege
- **Audit Logging**: All inter-agent communications logged

### Rate Limiting
- **Per-Agent Limits**: Configurable rate limits per agent
- **Burst Protection**: Handle traffic spikes gracefully
- **Circuit Breakers**: Prevent cascade failures

### Request Validation
- **Schema Validation**: All requests validated against schemas
- **Input Sanitization**: Prevent injection attacks
- **Message Signing**: Optional request signing for high-security scenarios

## Error Handling

### Standard Error Codes

| Code | Description | Action |
|------|-------------|--------|
| -32700 | Parse error | Fix JSON syntax |
| -32600 | Invalid Request | Check request format |
| -32601 | Method not found | Verify method name and agent capabilities |
| -32602 | Invalid params | Check parameter types and values |
| -32603 | Internal error | Contact agent maintainer |
| -40001 | Authentication failed | Refresh token or check credentials |
| -40003 | Insufficient permissions | Request additional scopes |
| -42900 | Rate limit exceeded | Reduce request frequency |

### Retry Strategies

1. **Exponential Backoff**: For transient failures
2. **Circuit Breaker**: For persistent failures
3. **Dead Letter Queue**: For unrecoverable messages

## Monitoring & Observability

### Metrics Collection
- **Request Latency**: P50, P95, P99 response times
- **Error Rates**: Success/failure ratios
- **Agent Availability**: Uptime and health checks
- **Message Volume**: Requests per second, data transfer

### Distributed Tracing
- **Trace ID**: Unique identifier for request chains
- **Span Context**: Correlation across agent boundaries
- **Baggage**: Metadata propagation

Example trace header:
```
X-Trace-Id: 1234567890abcdef
X-Span-Id: fedcba0987654321
X-Agent-Chain: nexus-ui-agent->nexus-task-agent->nexus-notification-agent
```

### Health Checks

#### Agent Health Endpoint
```
GET /health

{
  "status": "healthy",
  "timestamp": "2024-01-26T10:30:00Z",
  "version": "1.2.0",
  "dependencies": {
    "database": "healthy",
    "cache": "healthy", 
    "external_api": "degraded"
  },
  "metrics": {
    "requests_per_minute": 45,
    "avg_response_time_ms": 120,
    "error_rate": 0.02
  }
}
```

## Implementation Examples

### Python Agent Implementation
```python
import aiohttp
import asyncio
from typing import Dict, Any

class A2AAgent:
    def __init__(self, agent_id: str, auth_token: str):
        self.agent_id = agent_id
        self.auth_token = auth_token
        self.session = aiohttp.ClientSession()
    
    async def send_message(self, target_agent: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send A2A message to another agent"""
        
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'X-Agent-ID': self.agent_id
        }
        
        payload = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': f'req_{uuid.uuid4()}'
        }
        
        url = f'https://agents.nexusai.com/{target_agent}/rpc'
        
        async with self.session.post(url, json=payload, headers=headers) as response:
            result = await response.json()
            
            if 'error' in result:
                raise A2AError(result['error'])
            
            return result['result']

# Usage example
agent = A2AAgent('nexus-data-agent-v1', 'jwt_token')

task_result = await agent.send_message(
    target_agent='nexus-task-agent-v1',
    method='task_management.create_task',
    params={
        'title': 'Process user data',
        'priority': 'medium'
    }
)
```

### JavaScript Agent Implementation
```javascript
class A2AAgent {
  constructor(agentId, authToken) {
    this.agentId = agentId;
    this.authToken = authToken;
  }
  
  async sendMessage(targetAgent, method, params) {
    const payload = {
      jsonrpc: '2.0',
      method: method,
      params: params,
      id: `req_${Date.now()}`
    };
    
    const response = await fetch(`https://agents.nexusai.com/${targetAgent}/rpc`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.authToken}`,
        'Content-Type': 'application/json',
        'X-Agent-ID': this.agentId
      },
      body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    
    if (result.error) {
      throw new Error(`A2A Error: ${result.error.message}`);
    }
    
    return result.result;
  }
}

// Usage
const agent = new A2AAgent('nexus-ui-agent-v1', 'jwt_token');

const tasks = await agent.sendMessage(
  'nexus-task-agent-v1',
  'task_management.list_tasks',
  { status: 'in_progress', limit: 10 }
);
```

## Best Practices

### Design Principles
1. **Idempotency**: Operations should be safely retryable
2. **Backwards Compatibility**: Maintain API versioning
3. **Graceful Degradation**: Handle partial failures
4. **Resource Limits**: Prevent resource exhaustion

### Performance Optimization
1. **Connection Pooling**: Reuse HTTP connections
2. **Request Batching**: Group related operations
3. **Caching**: Cache frequently accessed data
4. **Compression**: Use gzip for large payloads

### Security Best Practices
1. **Principle of Least Privilege**: Minimal required permissions
2. **Defense in Depth**: Multiple security layers
3. **Regular Audits**: Security reviews and penetration testing
4. **Incident Response**: Procedures for security incidents

## Future Enhancements

### Planned Features
- **Protocol Versioning**: Support for protocol evolution
- **Message Queuing**: Asynchronous message delivery
- **Federation**: Cross-platform agent communication
- **AI-Native Features**: Semantic routing and intelligent load balancing

### Research Areas
- **Zero-Trust Architecture**: Enhanced security models
- **Federated Learning**: Cross-agent knowledge sharing
- **Autonomous Negotiation**: Agent-to-agent capability exchange

## Related Documentation
- [Authentication Design](auth_design.md)
- [Security Considerations](security_considerations.md)
- [MCP Server Design](mcp_server_design.md)
- [Agent Development Guide](agent_development_guide.md)