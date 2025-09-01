import express from "express";

const app = express();
app.use(express.json());

// MCP Tools Definition
const TOOLS = [
  {
    name: "list_repos",
    description: "List repositories for the authenticated user",
    inputSchema: {
      type: "object",
      properties: {},
      required: []
    }
  },
  {
    name: "get_repo",
    description: "Get repository details",
    inputSchema: {
      type: "object",
      properties: {
        name: {
          type: "string",
          description: "Repository name"
        }
      },
      required: ["name"]
    }
  },
  {
    name: "search_code",
    description: "Search for code in repositories",
    inputSchema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "Search query"
        },
        repo: {
          type: "string",
          description: "Repository name (optional)"
        }
      },
      required: ["query"]
    }
  }
];

app.post("/", async (req, res) => {
  const { method, params, id } = req.body || {};
  
  try {
    // MCP Protocol: tools/list
    if (method === "tools/list") {
      return res.json({
        jsonrpc: "2.0",
        id,
        result: {
          tools: TOOLS
        }
      });
    }

    // MCP Protocol: tools/call
    if (method === "tools/call") {
      const { name, arguments: args } = params || {};
      
      if (name === "list_repos") {
        return res.json({
          jsonrpc: "2.0",
          id,
          result: {
            content: [
              {
                type: "text",
                text: JSON.stringify([
                  { name: "example-repo", stars: 42, description: "An example repository" },
                  { name: "another-repo", stars: 15, description: "Another example repository" }
                ], null, 2)
              }
            ]
          }
        });
      }

      if (name === "get_repo") {
        const repoName = args?.name ?? "example-repo";
        return res.json({
          jsonrpc: "2.0",
          id,
          result: {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  name: repoName,
                  stars: 42,
                  forks: 7,
                  description: `Details for ${repoName}`,
                  url: `https://github.com/user/${repoName}`
                }, null, 2)
              }
            ]
          }
        });
      }

      if (name === "search_code") {
        const query = args?.query ?? "";
        const repo = args?.repo;
        return res.json({
          jsonrpc: "2.0",
          id,
          result: {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  query,
                  repository: repo || "all",
                  results: [
                    {
                      file: "src/index.js",
                      line: 15,
                      snippet: `function ${query}() { return "example"; }`
                    },
                    {
                      file: "test/test.js", 
                      line: 3,
                      snippet: `describe('${query}', function() {`
                    }
                  ]
                }, null, 2)
              }
            ]
          }
        });
      }

      return res.json({
        jsonrpc: "2.0",
        id,
        error: {
          code: -32601,
          message: `Unknown tool: ${name}`
        }
      });
    }

    // Legacy compatibility for older method names
    if (method === "get_methods") {
      return res.json({ jsonrpc: "2.0", id, result: TOOLS });
    }

    return res.json({
      jsonrpc: "2.0",
      id,
      error: {
        code: -32601,
        message: `Unknown method: ${method}`
      }
    });
  } catch (e: any) {
    return res.status(500).json({
      jsonrpc: "2.0",
      id,
      error: {
        code: -32000,
        message: e?.message || "Internal server error"
      }
    });
  }
});

const port = 7002;
app.listen(port, () => console.log(`Mock MCP GitHub server on http://localhost:${port}`));