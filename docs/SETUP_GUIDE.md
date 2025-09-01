# Complete Setup and Run Guide

This guide provides step-by-step instructions to set up and run the MCP Agent Proxy System.

## 📋 Prerequisites

### Required Software

1. **Node.js 18+**
   ```bash
   # Check version
   node --version  # Should be 18.0.0 or higher
   
   # Install if needed (using nvm)
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
   nvm install 18
   nvm use 18
   ```

2. **pnpm Package Manager**
   ```bash
   # Install pnpm globally
   npm install -g pnpm
   
   # Verify installation
   pnpm --version
   ```

3. **Git** (for cloning the repository)
   ```bash
   git --version
   ```

### Optional Software

- **Google API Key** - For real embeddings instead of fake ones
- **Docker** - For containerized deployment
- **Visual Studio Code** - For development with Cursor IDE integration

## 🚀 Installation

### Step 1: Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd agent-proxy

# Verify structure
ls -la
```

Expected structure:
```
agent-proxy/
├── src/           # Source code
├── tests/         # Test suites
├── docs/          # Documentation
├── mock_knowledge_base/  # Sample data
├── public/        # Web UI assets
├── package.json   # Dependencies
└── README.md      # Main documentation
```

### Step 2: Install Dependencies

```bash
# Install all dependencies
pnpm install

# Verify installation
pnpm list
```

This installs:
- **Runtime Dependencies**: Express, Axios, LangChain, Zod
- **Development Dependencies**: TypeScript, Jest, Nodemon, ESLint
- **MCP Libraries**: FastMCP for TypeScript MCP utilities

### Step 3: Environment Configuration (Optional)

Create a `.env` file for custom configuration:

```bash
# Create environment file
cp .env.example .env  # If example exists, or create new file
nano .env
```

Add your configuration:

```bash
# .env file contents

# API Keys
GOOGLE_API_KEY=your_google_api_key_here
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here

# Server Ports
PORT=8002                    # MCP Proxy Server
UI_PORT=3000                 # Web UI Server

# MCP Server URLs (optional - defaults to localhost)
MCP_FILESYSTEM_URL=http://localhost:7001
MCP_GITHUB_URL=http://localhost:7002
MCP_ATLASSIAN_URL=http://localhost:7003
MCP_GDRIVE_URL=http://localhost:7004

# Debug (optional)
DEBUG=mcp:*
NODE_ENV=development
```

### Step 4: Build Project (Optional)

```bash
# Compile TypeScript to JavaScript
pnpm build

# Check build output
ls dist/
```

## 🏃‍♂️ Running the System

### Method 1: Development Mode (Recommended)

Start each service in a separate terminal for easier debugging:

#### Terminal 1: MCP Proxy Server
```bash
cd agent-proxy
pnpm dev:proxy
```

Expected output:
```
MCP Proxy listening on http://localhost:8002
```

#### Terminal 2: Mock Filesystem Server
```bash
cd agent-proxy
pnpm dev:filesystem
```

Expected output:
```
Mock MCP filesystem server on http://localhost:7001
```

#### Terminal 3: Mock GitHub Server
```bash
cd agent-proxy
pnpm dev:github
```

Expected output:
```
Mock MCP GitHub server on http://localhost:7002
```

#### Terminal 4: Mock Atlassian Server
```bash
cd agent-proxy
pnpm dev:atlassian
```

Expected output:
```
Mock MCP Atlassian server on http://localhost:7003
```

#### Terminal 5: Mock Google Drive Server
```bash
cd agent-proxy
pnpm dev:gdrive
```

Expected output:
```
Mock MCP Google Drive server on http://localhost:7004
```

#### Terminal 6: Web UI Server
```bash
cd agent-proxy
pnpm dev:ui
```

Expected output:
```
UI server listening on http://localhost:3000
```

### Method 2: Background Mode

Start all services in the background:

```bash
cd agent-proxy

# Start all mock servers in background
pnpm dev:filesystem &
pnpm dev:github &
pnpm dev:atlassian &
pnpm dev:gdrive &

# Start proxy and UI
pnpm dev:proxy &
pnpm dev:ui &

# Check running processes
ps aux | grep node
```

### Method 3: Production Mode

```bash
cd agent-proxy

# Build the project
pnpm build

# Start services
pnpm start &           # Proxy server
pnpm start:ui &        # UI server

# Start mock servers
node dist/servers/filesystem-mock.js &
node dist/servers/github-mock.js &
node dist/servers/atlassian-mock.js &
node dist/servers/gdrive-mock.js &
```

## ✅ Verification

### Step 1: Check Service Health

Verify each service is running:

```bash
# Check proxy server
curl http://localhost:8002/mcp/get_methods

# Check mock servers
curl -X POST http://localhost:7001 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"get_methods","id":"1"}'

curl -X POST http://localhost:7002 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"get_methods","id":"1"}'

curl -X POST http://localhost:7003 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"get_methods","id":"1"}'

curl -X POST http://localhost:7004 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"get_methods","id":"1"}'

# Check web UI
curl http://localhost:3000
```

### Step 2: Test MCP Client

```bash
# Test basic functionality
cd agent-proxy

# Get available methods from filesystem server
pnpm dev:client filesystem get_methods

# List files in current directory
pnpm dev:client filesystem list_files '{"path":"."}'

# Test GitHub server
pnpm dev:client github list_repos

# Test Atlassian server
pnpm dev:client atlassian list_projects

# Test Google Drive server
pnpm dev:client gdrive list_files
```

Expected outputs:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": [
    {
      "name": "list_files",
      "params": {"path": "string"},
      "description": "List files in a directory"
    },
    {
      "name": "read_file",
      "params": {"path": "string"}, 
      "description": "Read a file"
    }
  ]
}
```

### Step 3: Test Agent

```bash
cd agent-proxy

# Test agent with various queries
pnpm dev:agent "filesystem list_files"
pnpm dev:agent "github list_repos"
pnpm dev:agent "atlassian list_projects"
pnpm dev:agent "filesystem read_file path=package.json"
```

Expected output:
```json
{
  "parsed": {
    "tool": "filesystem",
    "action": "list_files",
    "args": {}
  },
  "mcpSnippet": [
    "src", "tests", "docs", "mock_knowledge_base", "public", "package.json"
  ],
  "ragContextPreview": [
    {
      "file": "mock_knowledge_base/docs/proxy_design.md",
      "text": "# MCP Proxy Server Design..."
    }
  ]
}
```

### Step 4: Test Web UI

1. **Open browser**: Navigate to http://localhost:3000
2. **Enter query**: Type "filesystem list_files" in the input field
3. **Submit**: Click the "Send" button
4. **Check result**: Verify JSON response appears below

Example queries to try:
- `filesystem list_files`
- `github list_repos`
- `atlassian list_projects path=./src`
- `gdrive list_files`

## 🧪 Running Tests

### Full Test Suite

```bash
cd agent-proxy

# Run all tests
pnpm test

# Run with coverage
pnpm test:coverage

# Run in watch mode (for development)
pnpm test:watch
```

### Individual Test Suites

```bash
# Test specific components
pnpm test agent.test.ts
pnpm test proxy.test.ts
pnpm test ui.test.ts
pnpm test e2e.test.ts
```

Expected test output:
```
 PASS  tests/agent.test.ts
 PASS  tests/proxy.test.ts  
 PASS  tests/ui.test.ts
 PASS  tests/e2e.test.ts

Test Suites: 4 passed, 4 total
Tests:       12 passed, 12 total
Snapshots:   0 total
Time:        3.284 s
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error**: `EADDRINUSE: address already in use :::8002`

**Solution**:
```bash
# Find process using the port
lsof -i :8002

# Kill the process
kill -9 <PID>

# Or use different port
PORT=8003 pnpm dev:proxy
```

#### 2. Dependencies Not Found

**Error**: `Cannot find module 'express'`

**Solution**:
```bash
# Clean and reinstall
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

#### 3. TypeScript Compilation Errors

**Error**: `TS2307: Cannot find module`

**Solution**:
```bash
# Check TypeScript configuration
cat tsconfig.json

# Rebuild
pnpm build
```

#### 4. RAG System Errors

**Error**: `GOOGLE_API_KEY not found`

**Solution**: This is expected - the system falls back to fake embeddings. To use real embeddings:
```bash
export GOOGLE_API_KEY=your_api_key_here
pnpm dev:agent "your query"
```

#### 5. MCP Communication Errors

**Error**: `connect ECONNREFUSED localhost:7001`

**Solution**:
```bash
# Ensure mock servers are running
pnpm dev:filesystem  # In separate terminal

# Check server status
curl http://localhost:7001
```

### Service-Specific Issues

#### Proxy Server Issues

```bash
# Check proxy logs
pnpm dev:proxy

# Test proxy directly
curl -X POST http://localhost:8002/mcp/filesystem \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"get_methods","id":"1"}'
```

#### Agent Issues

```bash
# Check agent with verbose output
DEBUG=* pnpm dev:agent "filesystem list_files"

# Test individual components
node -e "const {parseQuery} = require('./dist/agent/agent'); console.log(parseQuery('filesystem list_files'))"
```

#### UI Issues

```bash
# Check UI server logs
pnpm dev:ui

# Test API endpoint directly
curl -X POST http://localhost:3000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query":"filesystem list_files"}'
```

### Debugging Tips

1. **Check logs**: Each service outputs detailed logs to console
2. **Use curl**: Test API endpoints directly with curl commands
3. **Enable debug**: Set `DEBUG=*` for verbose logging
4. **Check network**: Ensure no firewall blocking local ports
5. **Verify JSON**: Use tools like `jq` to validate JSON responses

```bash
# Example debugging command
curl -s http://localhost:8002/mcp/get_methods | jq '.'
```

## 🔧 Advanced Configuration

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

EXPOSE 8002 3000 7001 7002 7003 7004

CMD ["pnpm", "start"]
```

Build and run:

```bash
# Build Docker image
docker build -t mcp-agent-proxy .

# Run container
docker run -p 8002:8002 -p 3000:3000 -p 7001:7001 -p 7002:7002 -p 7003:7003 -p 7004:7004 mcp-agent-proxy
```

### Process Management

Using PM2 for production:

```bash
# Install PM2
npm install -g pm2

# Create ecosystem file
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [
    {name: 'proxy', script: 'dist/proxy/server.js'},
    {name: 'ui', script: 'dist/ui/server.js'},
    {name: 'filesystem', script: 'dist/servers/filesystem-mock.js'},
    {name: 'github', script: 'dist/servers/github-mock.js'},
    {name: 'atlassian', script: 'dist/servers/atlassian-mock.js'},
    {name: 'gdrive', script: 'dist/servers/gdrive-mock.js'}
  ]
};
EOF

# Start all services
pnpm build && pm2 start ecosystem.config.js

# Monitor
pm2 status
pm2 logs
```

### Load Balancing

For high availability, use nginx:

```nginx
upstream mcp_proxy {
    server localhost:8002;
    server localhost:8003;  # Additional proxy instance
}

server {
    listen 80;
    location /mcp/ {
        proxy_pass http://mcp_proxy;
    }
}
```

## 📈 Performance Optimization

### Memory Usage

```bash
# Monitor memory usage
ps aux | grep node

# Adjust Node.js memory limits
NODE_OPTIONS="--max-old-space-size=4096" pnpm dev:proxy
```

### Concurrency

```bash
# Enable cluster mode for proxy
NODE_ENV=production CLUSTER=true pnpm start
```

### Caching

Add Redis for response caching:

```bash
# Install Redis client
pnpm add redis

# Configure in proxy server
const redis = require('redis');
const client = redis.createClient();
```

## 🔒 Security Considerations

### Production Checklist

1. **Environment Variables**: Never commit API keys to git
2. **HTTPS**: Use TLS in production
3. **Authentication**: Add auth middleware
4. **Rate Limiting**: Implement request rate limiting
5. **Input Validation**: Validate all user inputs
6. **Error Handling**: Don't expose internal errors

### Security Headers

Add to Express servers:

```typescript
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  next();
});
```

---

This completes the setup guide. For additional help, check the [Services Documentation](SERVICES.md) or open an issue in the repository.