# IDE MCP Integration

## Configuration
1. Start the proxy server:
   ```bash
   pnpm dev:proxy
   ```
2. In your IDE (e.g., Cursor or VS Code with an MCP client), add a server entry:
   ```json
   {
     "mcpServers": {
       "gateway": {
         "url": "http://localhost:3000/mcp/proxy"
       }
     }
   }
   ```
3. Reload the IDE so it connects to the proxy.

## Testing
1. Open the IDE's MCP console or chat.
2. Issue a request such as listing resources from the filesystem server.
3. Confirm the response is returned through the proxy without errors.

These steps verify that the IDE can reach the gateway and exercise downstream MCP servers.
