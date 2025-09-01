import express from "express";

const app = express();
app.use(express.json());

// MCP Tools Definition
const TOOLS = [
  {
    name: "list_projects",
    description: "List Atlassian projects",
    inputSchema: {
      type: "object",
      properties: {},
      required: []
    }
  },
  {
    name: "get_project",
    description: "Get project details",
    inputSchema: {
      type: "object",
      properties: {
        key: {
          type: "string",
          description: "Project key"
        }
      },
      required: ["key"]
    }
  },
  {
    name: "list_issues",
    description: "List issues in a project",
    inputSchema: {
      type: "object",
      properties: {
        projectKey: {
          type: "string",
          description: "Project key"
        },
        limit: {
          type: "number",
          description: "Maximum number of issues to return",
          default: 10
        }
      },
      required: ["projectKey"]
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
      
      if (name === "list_projects") {
        return res.json({
          jsonrpc: "2.0",
          id,
          result: {
            content: [
              {
                type: "text",
                text: JSON.stringify([
                  { key: "TEST", name: "Test Project", description: "A test project" },
                  { key: "DEMO", name: "Demo Project", description: "Demo project for MCP" }
                ], null, 2)
              }
            ]
          }
        });
      }

      if (name === "get_project") {
        const key = args?.key ?? "TEST";
        return res.json({
          jsonrpc: "2.0",
          id,
          result: {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  key,
                  name: `${key} Project`,
                  description: `Project with key ${key}`,
                  lead: "john.doe@example.com",
                  url: `https://example.atlassian.net/browse/${key}`
                }, null, 2)
              }
            ]
          }
        });
      }

      if (name === "list_issues") {
        const projectKey = args?.projectKey;
        const limit = args?.limit ?? 10;
        
        if (!projectKey) {
          return res.json({
            jsonrpc: "2.0",
            id,
            error: {
              code: -32602,
              message: "Missing required parameter: projectKey"
            }
          });
        }

        return res.json({
          jsonrpc: "2.0",
          id,
          result: {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  projectKey,
                  issues: Array.from({ length: Math.min(limit, 3) }, (_, i) => ({
                    key: `${projectKey}-${i + 1}`,
                    summary: `Sample issue ${i + 1}`,
                    status: i === 0 ? "Open" : i === 1 ? "In Progress" : "Done",
                    assignee: "jane.smith@example.com"
                  }))
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

const port = 7003;
app.listen(port, () => console.log(`Mock MCP Atlassian server on http://localhost:${port}`));