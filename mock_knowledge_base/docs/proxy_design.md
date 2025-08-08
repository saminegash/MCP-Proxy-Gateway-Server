# MCP Proxy Server Design

This document outlines the design and implementation of the central MCP proxy server that provides unified access to multiple downstream MCP servers.

## Overview

The MCP proxy acts as a centralized gateway that routes requests to appropriate downstream MCP servers, providing a single point of access for AI agents while maintaining the flexibility of distributed MCP services.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Agents     │    │   MCP Proxy     │    │ Downstream      │
│                 │◄──►│                 │◄──►│ MCP Servers     │
│ - Dev Assistant │    │ - Routing       │    │                 │
│ - Code Analyzer │    │ - Load Balance  │    │ - GitHub MCP    │
│ - Task Manager  │    │ - Auth Proxy    │    │ - Filesystem    │
│ - Doc Generator │    │ - Health Check  │    │ - JIRA MCP      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Components

### 1. Request Router

The router determines which downstream server should handle each request based on:

- **URL Path Prefix**: `/proxy/{server_prefix}/method`
- **Method Name Prefix**: Method names like `github_get_issues` or `fs_list_files`
- **Header-Based Routing**: Custom headers indicating target server

#### Routing Implementation
```python
class RequestRouter:
    def __init__(self, server_configs: Dict[str, ServerConfig]):
        self.servers = server_configs
        self.method_mappings = self._build_method_mappings()
    
    def route_request(self, path: str, method: str) -> str:
        """Determine target server for request"""
        
        # Try path-based routing first
        server_prefix = self._extract_server_prefix(path)
        if server_prefix and server_prefix in self.servers:
            return server_prefix
        
        # Fall back to method-based routing
        return self._route_by_method(method)
    
    def _route_by_method(self, method: str) -> str:
        """Route based on method name patterns"""
        
        for prefix, server in self.method_mappings.items():
            if method.startswith(prefix):
                return server
        
        # Default routing logic
        method_to_server = {
            'get_issues': 'github',
            'list_files': 'filesystem',
            'create_task': 'jira',
            'search_documents': 'docs'
        }
        
        return method_to_server.get(method, 'default')
```

### 2. Load Balancing

For high availability, the proxy supports multiple instances of downstream servers:

#### Health-Based Load Balancing
```python
class LoadBalancer:
    def __init__(self):
        self.server_health = {}
        self.request_counts = defaultdict(int)
    
    async def select_server(self, server_type: str) -> ServerConfig:
        """Select best available server instance"""
        
        available_servers = [
            server for server in self.servers[server_type]
            if self.is_healthy(server)
        ]
        
        if not available_servers:
            raise ServiceUnavailableError(f"No healthy {server_type} servers")
        
        # Use weighted round-robin with health scores
        return self._weighted_selection(available_servers)
    
    def _weighted_selection(self, servers: List[ServerConfig]) -> ServerConfig:
        """Select server based on health and load"""
        
        weights = []
        for server in servers:
            health_score = self.server_health.get(server.url, 1.0)
            load_factor = 1.0 / (self.request_counts[server.url] + 1)
            weight = health_score * load_factor
            weights.append(weight)
        
        return random.choices(servers, weights=weights)[0]
```

### 3. Authentication Proxy

The proxy handles authentication and passes credentials to downstream servers:

#### Token Passthrough
```python
class AuthenticationProxy:
    def __init__(self, jwt_verifier: JWTVerifier):
        self.jwt_verifier = jwt_verifier
        
    async def process_request(self, request: Request) -> Dict[str, Any]:
        """Process authentication for proxy request"""
        
        # Extract and verify token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            raise AuthenticationError("Missing authorization header")
        
        token = auth_header.replace('Bearer ', '')
        payload = self.jwt_verifier.verify_token(token)
        
        # Determine required scopes for target server
        target_server = request.path_params.get('server')
        required_scopes = self.get_required_scopes(target_server, request.method)
        
        # Check permissions
        user_scopes = set(payload.get('scopes', []))
        if not set(required_scopes).issubset(user_scopes):
            raise AuthorizationError("Insufficient permissions")
        
        return {
            'user_id': payload.get('user_id'),
            'agent_id': payload.get('agent_id'),
            'scopes': list(user_scopes),
            'token': token
        }
```

### 4. Circuit Breaker

Protects against cascade failures from downstream services:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
            
            raise e
```

## Request Processing Flow

### 1. Request Ingestion
```
1. Receive HTTP request from agent
2. Parse path and extract routing information
3. Validate request format and authentication
4. Determine target downstream server
```

### 2. Server Selection
```
1. Check server health status
2. Apply load balancing algorithm
3. Select optimal server instance
4. Check circuit breaker status
```

### 3. Request Forwarding
```
1. Transform request for downstream server
2. Add/modify headers as needed
3. Forward request with timeout
4. Handle connection pooling
```

### 4. Response Processing
```
1. Receive response from downstream
2. Transform response format if needed
3. Add proxy metadata
4. Return to requesting agent
```

## Configuration Management

### Server Configuration
```yaml
# proxy-config.yaml
proxy:
  host: "0.0.0.0"
  port: 8000
  max_concurrent_requests: 1000
  request_timeout: 30

servers:
  github:
    - url: "http://github-mcp-1:8001"
      weight: 1.0
      health_check_path: "/health"
    - url: "http://github-mcp-2:8001"
      weight: 1.0
      health_check_path: "/health"
  
  filesystem:
    - url: "http://fs-mcp-1:8002"
      weight: 1.0
    
  jira:
    - url: "http://jira-mcp-1:8003"
      weight: 1.0

routing:
  default_server: "filesystem"
  method_prefixes:
    "github_": "github"
    "fs_": "filesystem"
    "file_": "filesystem"
    "jira_": "jira"
    "task_": "jira"

health_checks:
  interval: 30  # seconds
  timeout: 5
  failure_threshold: 3

circuit_breaker:
  failure_threshold: 5
  timeout: 60
  half_open_max_calls: 3
```

### Dynamic Configuration
```python
class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self.load_config()
        self.file_watcher = FileWatcher(config_path, self.on_config_change)
    
    async def on_config_change(self, event):
        """Handle configuration file changes"""
        try:
            new_config = self.load_config()
            await self.validate_config(new_config)
            
            old_config = self.config
            self.config = new_config
            
            await self.apply_config_changes(old_config, new_config)
            
        except Exception as e:
            logger.error(f"Failed to reload config: {e}")
    
    async def apply_config_changes(self, old_config, new_config):
        """Apply configuration changes without restart"""
        
        # Update server configurations
        if old_config['servers'] != new_config['servers']:
            await self.update_server_pool(new_config['servers'])
        
        # Update routing rules
        if old_config['routing'] != new_config['routing']:
            self.update_routing_rules(new_config['routing'])
```

## Monitoring & Observability

### Metrics Collection
```python
class ProxyMetrics:
    def __init__(self):
        self.request_counter = Counter('proxy_requests_total', 
                                     ['server', 'method', 'status'])
        self.request_duration = Histogram('proxy_request_duration_seconds',
                                        ['server', 'method'])
        self.active_connections = Gauge('proxy_active_connections', ['server'])
    
    def record_request(self, server: str, method: str, 
                      status: str, duration: float):
        """Record request metrics"""
        self.request_counter.labels(server=server, method=method, 
                                  status=status).inc()
        self.request_duration.labels(server=server, method=method).observe(duration)
    
    def update_connections(self, server: str, count: int):
        """Update active connection count"""
        self.active_connections.labels(server=server).set(count)
```

### Distributed Tracing
```python
class TracingMiddleware:
    def __init__(self, tracer):
        self.tracer = tracer
    
    async def __call__(self, request: Request, call_next):
        """Add tracing to proxy requests"""
        
        with self.tracer.start_span('proxy_request') as span:
            span.set_tag('http.method', request.method)
            span.set_tag('http.url', str(request.url))
            
            # Extract incoming trace context
            span_context = self.tracer.extract(
                opentracing.Format.HTTP_HEADERS,
                request.headers
            )
            
            response = await call_next(request)
            
            span.set_tag('http.status_code', response.status_code)
            
            return response
```

## Error Handling

### Error Classification
```python
class ProxyErrorHandler:
    def __init__(self):
        self.error_mappings = {
            ConnectionError: ('SERVICE_UNAVAILABLE', 503),
            TimeoutError: ('GATEWAY_TIMEOUT', 504),
            AuthenticationError: ('UNAUTHORIZED', 401),
            AuthorizationError: ('FORBIDDEN', 403),
            CircuitBreakerOpenError: ('SERVICE_UNAVAILABLE', 503)
        }
    
    async def handle_error(self, error: Exception) -> Response:
        """Handle proxy errors with appropriate responses"""
        
        error_type = type(error)
        error_code, status_code = self.error_mappings.get(
            error_type, 
            ('INTERNAL_ERROR', 500)
        )
        
        response_data = {
            'error': {
                'code': error_code,
                'message': str(error),
                'timestamp': datetime.utcnow().isoformat(),
                'proxy_info': {
                    'version': '1.0.0',
                    'request_id': generate_request_id()
                }
            }
        }
        
        return JSONResponse(response_data, status_code=status_code)
```

## Performance Optimization

### Connection Pooling
```python
class ConnectionPoolManager:
    def __init__(self):
        self.pools = {}
        self.pool_config = {
            'connector_limit': 100,
            'limit_per_host': 30,
            'keepalive_timeout': 60
        }
    
    def get_session(self, server_url: str) -> aiohttp.ClientSession:
        """Get or create connection pool for server"""
        
        if server_url not in self.pools:
            connector = aiohttp.TCPConnector(**self.pool_config)
            session = aiohttp.ClientSession(connector=connector)
            self.pools[server_url] = session
        
        return self.pools[server_url]
```

### Request Batching
```python
class RequestBatcher:
    def __init__(self, batch_size: int = 10, batch_timeout: float = 0.1):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_requests = defaultdict(list)
    
    async def add_request(self, server: str, request: Request) -> Any:
        """Add request to batch for server"""
        
        future = asyncio.Future()
        self.pending_requests[server].append((request, future))
        
        # Trigger batch processing if size threshold reached
        if len(self.pending_requests[server]) >= self.batch_size:
            await self.process_batch(server)
        
        return await future
    
    async def process_batch(self, server: str):
        """Process batched requests for server"""
        
        requests = self.pending_requests[server]
        self.pending_requests[server] = []
        
        # Send batch request to server
        batch_data = [req.json() for req, _ in requests]
        
        try:
            results = await self.send_batch_request(server, batch_data)
            
            # Return results to individual futures
            for (_, future), result in zip(requests, results):
                future.set_result(result)
                
        except Exception as e:
            # Set exception for all requests in batch
            for _, future in requests:
                future.set_exception(e)
```

## Security Considerations

### Input Validation
- Validate all incoming requests against schemas
- Sanitize path parameters to prevent injection
- Rate limiting per client/agent
- Request size limits

### Transport Security
- TLS termination at proxy level
- Certificate validation for downstream servers
- Secure header forwarding

### Access Control
- Token validation and refresh
- Scope-based authorization
- Audit logging for all requests

## Deployment

### Docker Configuration
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "proxy.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-proxy
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-proxy
  template:
    metadata:
      labels:
        app: mcp-proxy
    spec:
      containers:
      - name: proxy
        image: nexusai/mcp-proxy:latest
        ports:
        - containerPort: 8000
        env:
        - name: CONFIG_PATH
          value: "/config/proxy-config.yaml"
        volumeMounts:
        - name: config
          mountPath: /config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: proxy-config
```

## Related Documentation
- [Routing Strategy](routing_strategy.md)
- [Error Handling](error_handling.md)
- [MCP Server Design](mcp_server_design.md)
- [Authentication Design](auth_design.md)