import express from "express";

const app = express();
app.use(express.json());

// MCP Tools Definition
const TOOLS = [
  {
    name: "list_files",
    description: "List Google Drive files",
    inputSchema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "Search query for files (optional)"
        },
        limit: {
          type: "number",
          description: "Maximum number of files to return",
          default: 10
        }
      },
      required: []
    }
  },
  {
    name: "get_file",
    description: "Get file contents or metadata",
    inputSchema: {
      type: "object",
      properties: {
        id: {
          type: "string",
          description: "File ID"
        }
      },
      required: ["id"]
    }
  },
  {
    name: "search_files",
    description: "Search for files in Google Drive",
    inputSchema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "Search query"
        },
        type: {
          type: "string",
          description: "File type filter (optional)",
          enum: ["document", "spreadsheet", "presentation", "folder"]
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
      
      if (name === "list_files") {
        const query = args?.query;
        const limit = args?.limit ?? 10;
        
        return res.json({
          jsonrpc: "2.0",
          id,
          result: {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  query: query || "all files",
                  files: Array.from({ length: Math.min(limit, 5) }, (_, i) => ({
                    id: `file_${i + 1}`,
                    name: `Document ${i + 1}${query ? ` (${query})` : ''}`,
                    type: i % 2 === 0 ? "document" : "spreadsheet",
                    size: `${(i + 1) * 1024} bytes`,
                    modified: new Date(Date.now() - i * 86400000).toISOString()
                  }))
                }, null, 2)
              }
            ]
          }
        });
      }

      if (name === "get_file") {
        const fileId = args?.id;
        
        if (!fileId) {
          return res.json({
            jsonrpc: "2.0",
            id,
            error: {
              code: -32602,
              message: "Missing required parameter: id"
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
                  id: fileId,
                  name: `Document ${fileId}`,
                  type: "document",
                  content: `This is the content of file ${fileId}. Lorem ipsum dolor sit amet, consectetur adipiscing elit.`,
                  url: `https://drive.google.com/file/d/${fileId}`,
                  size: "2048 bytes",
                  modified: new Date().toISOString()
                }, null, 2)
              }
            ]
          }
        });
      }

      if (name === "search_files") {
        const query = args?.query;
        const type = args?.type;
        
        if (!query) {
          return res.json({
            jsonrpc: "2.0",
            id,
            error: {
              code: -32602,
              message: "Missing required parameter: query"
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
                  query,
                  type: type || "all",
                  results: [
                    {
                      id: "search_1",
                      name: `${query} - Results Document`,
                      type: type || "document",
                      snippet: `This document contains information about ${query}...`,
                      url: "https://drive.google.com/file/d/search_1"
                    },
                    {
                      id: "search_2", 
                      name: `Analysis of ${query}`,
                      type: type || "spreadsheet",
                      snippet: `Spreadsheet with ${query} data analysis...`,
                      url: "https://drive.google.com/file/d/search_2"
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

const port = 7004;
app.listen(port, () => console.log(`Mock MCP Google Drive server on http://localhost:${port}`));