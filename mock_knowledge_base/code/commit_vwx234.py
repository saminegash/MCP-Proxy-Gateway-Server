# Commit: vwx234 - MCP proxy server implementation (NEX-404)
# Central MCP proxy for unified tool access

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from urllib.parse import urljoin
import logging

@dataclass
class MCPServerConfig:
    """Configuration for downstream MCP server"""
    name: str
    url: str
    prefix: str
    timeout: int = 30
    headers: Dict[str, str] = None

class MCPProxyServer:
    """Central MCP proxy server for routing requests"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.servers: Dict[str, MCPServerConfig] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
        
        # Default server configurations
        self._load_default_config()
        
        if config_file:
            self._load_config_file(config_file)
    
    def _load_default_config(self):
        """Load default MCP server configurations"""
        default_servers = [
            MCPServerConfig(
                name="github",
                url="http://localhost:8001/mcp",
                prefix="github"
            ),
            MCPServerConfig(
                name="filesystem",
                url="http://localhost:8002/mcp",
                prefix="fs"
            ),
            MCPServerConfig(
                name="jira",
                url="http://localhost:8003/mcp",
                prefix="jira"
            ),
            MCPServerConfig(
                name="gdrive",
                url="http://localhost:8004/mcp",
                prefix="docs"
            )
        ]
        
        for server in default_servers:
            self.servers[server.prefix] = server
    
    def _load_config_file(self, config_file: str):
        """Load server configurations from file"""
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            for server_data in config_data.get('servers', []):
                config = MCPServerConfig(**server_data)
                self.servers[config.prefix] = config
        
        except Exception as e:
            self.logger.error(f"Failed to load config file {config_file}: {e}")
    
    async def start(self):
        """Start the proxy server"""
        self.session = aiohttp.ClientSession()
    
    async def stop(self):
        """Stop the proxy server"""
        if self.session:
            await self.session.close()
    
    def _parse_route(self, path: str) -> tuple[str, str]:
        """Parse routing information from request path"""
        # Expected format: /proxy/{server_prefix}/{method}
        # or /proxy/mcp for unified access
        
        parts = path.strip('/').split('/')
        
        if len(parts) < 2:
            raise ValueError("Invalid path format")
        
        if parts[0] != 'proxy':
            raise ValueError("Path must start with /proxy")
        
        if len(parts) == 2 and parts[1] == 'mcp':
            # Unified MCP endpoint - routing determined by method prefix
            return None, None
        
        if len(parts) >= 3:
            server_prefix = parts[1]
            remaining_path = '/'.join(parts[2:])
            return server_prefix, remaining_path
        
        raise ValueError("Invalid path format")
    
    def _determine_server_from_method(self, method: str) -> Optional[str]:
        """Determine target server from method name"""
        method_prefixes = {
            'github_': 'github',
            'fs_': 'fs',
            'file_': 'fs',
            'jira_': 'jira',
            'docs_': 'docs',
            'gdrive_': 'docs'
        }
        
        for prefix, server in method_prefixes.items():
            if method.startswith(prefix):
                return server
        
        # Default mappings for common methods
        method_mappings = {
            'get_issues': 'github',
            'get_issue': 'github',
            'get_pull_requests': 'github',
            'list_files': 'fs',
            'read_file': 'fs',
            'search_files': 'fs',
            'get_tickets': 'jira',
            'create_ticket': 'jira'
        }
        
        return method_mappings.get(method)
    
    async def route_request(self, path: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route MCP request to appropriate downstream server"""
        try:
            server_prefix, remaining_path = self._parse_route(path)
            
            # If no explicit server prefix, try to determine from method
            if server_prefix is None:
                method = request_data.get('method')
                if method:
                    server_prefix = self._determine_server_from_method(method)
                    if not server_prefix:
                        return {"error": f"Cannot determine target server for method: {method}"}
                else:
                    return {"error": "No method specified and no server prefix in path"}
            
            # Get server configuration
            if server_prefix not in self.servers:
                return {"error": f"Unknown server prefix: {server_prefix}"}
            
            server_config = self.servers[server_prefix]
            
            # Forward request to downstream server
            response = await self._forward_request(server_config, request_data)
            
            # Add routing metadata to response
            if isinstance(response, dict):
                response['_proxy_info'] = {
                    'routed_to': server_config.name,
                    'server_url': server_config.url,
                    'method': request_data.get('method')
                }
            
            return response
        
        except Exception as e:
            self.logger.error(f"Routing error: {e}")
            return {"error": f"Routing failed: {str(e)}"}
    
    async def _forward_request(self, server_config: MCPServerConfig, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Forward request to downstream MCP server"""
        try:
            headers = {
                'Content-Type': 'application/json',
                **(server_config.headers or {})
            }
            
            timeout = aiohttp.ClientTimeout(total=server_config.timeout)
            
            async with self.session.post(
                server_config.url,
                json=request_data,
                headers=headers,
                timeout=timeout
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {
                        "error": f"Downstream server error: {response.status}",
                        "details": error_text
                    }
        
        except asyncio.TimeoutError:
            return {"error": f"Timeout connecting to {server_config.name}"}
        
        except aiohttp.ClientError as e:
            return {"error": f"Connection error to {server_config.name}: {str(e)}"}
        
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    async def get_all_methods(self) -> Dict[str, Any]:
        """Get methods from all configured servers"""
        all_methods = {}
        
        for prefix, server_config in self.servers.items():
            try:
                request_data = {"method": "get_methods", "params": {}}
                response = await self._forward_request(server_config, request_data)
                
                if response.get("success"):
                    methods = response.get("methods", [])
                    all_methods[prefix] = {
                        "server": server_config.name,
                        "url": server_config.url,
                        "methods": methods,
                        "status": "available"
                    }
                else:
                    all_methods[prefix] = {
                        "server": server_config.name,
                        "url": server_config.url,
                        "methods": [],
                        "status": "error",
                        "error": response.get("error")
                    }
            
            except Exception as e:
                all_methods[prefix] = {
                    "server": server_config.name,
                    "url": server_config.url,
                    "methods": [],
                    "status": "unavailable",
                    "error": str(e)
                }
        
        return {
            "success": True,
            "servers": all_methods,
            "total_servers": len(self.servers)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all downstream servers"""
        health_status = {}
        
        for prefix, server_config in self.servers.items():
            try:
                start_time = asyncio.get_event_loop().time()
                
                # Simple ping with get_methods
                request_data = {"method": "get_methods", "params": {}}
                response = await self._forward_request(server_config, request_data)
                
                end_time = asyncio.get_event_loop().time()
                response_time = (end_time - start_time) * 1000  # Convert to ms
                
                if response.get("success") or "methods" in response:
                    health_status[prefix] = {
                        "status": "healthy",
                        "response_time_ms": round(response_time, 2),
                        "server": server_config.name
                    }
                else:
                    health_status[prefix] = {
                        "status": "unhealthy",
                        "response_time_ms": round(response_time, 2),
                        "server": server_config.name,
                        "error": response.get("error", "Unknown error")
                    }
            
            except Exception as e:
                health_status[prefix] = {
                    "status": "unavailable",
                    "server": server_config.name,
                    "error": str(e)
                }
        
        return {
            "proxy_status": "healthy",
            "servers": health_status,
            "timestamp": asyncio.get_event_loop().time()
        }

# Web server implementation
async def create_proxy_app() -> 'web.Application':
    """Create aiohttp application for MCP proxy"""
    from aiohttp import web
    
    proxy = MCPProxyServer()
    await proxy.start()
    
    async def handle_proxy_request(request):
        """Handle proxied MCP requests"""
        try:
            path = request.path
            request_data = await request.json()
            
            response = await proxy.route_request(path, request_data)
            return web.json_response(response)
        
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_methods_request(request):
        """Handle get all methods request"""
        try:
            response = await proxy.get_all_methods()
            return web.json_response(response)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_health_request(request):
        """Handle health check request"""
        try:
            response = await proxy.health_check()
            return web.json_response(response)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def cleanup_proxy(app):
        """Cleanup proxy resources"""
        await proxy.stop()
    
    app = web.Application()
    
    # Route patterns
    app.router.add_post('/proxy/mcp', handle_proxy_request)
    app.router.add_post('/proxy/{server}/{path:.*}', handle_proxy_request)
    app.router.add_get('/proxy/methods', handle_methods_request)
    app.router.add_get('/proxy/health', handle_health_request)
    
    # Cleanup handler
    app.on_cleanup.append(cleanup_proxy)
    
    return app

async def start_proxy_server(host: str = "localhost", port: int = 8000):
    """Start the MCP proxy server"""
    from aiohttp import web
    
    app = await create_proxy_app()
    
    print(f"Starting MCP Proxy Server on {host}:{port}")
    print("Available endpoints:")
    print(f"  POST http://{host}:{port}/proxy/mcp - Unified MCP endpoint")
    print(f"  POST http://{host}:{port}/proxy/{{server}}/mcp - Server-specific endpoint")
    print(f"  GET  http://{host}:{port}/proxy/methods - List all methods")
    print(f"  GET  http://{host}:{port}/proxy/health - Health check")
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("Shutting down proxy server...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_proxy_server())