import express from "express";
import fs from "fs";
import path from "path";

const app = express();
app.use(express.json());

// MCP Tools Definition
const TOOLS = [
  {
    name: "list_files",
    description: "List files in a directory",
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          description: "Directory path to list files from",
          default: "."
        }
      },
      required: []
    }
  },
  {
    name: "read_file",
    description: "Read contents of a file",
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          description: "File path to read"
        }
      },
      required: ["path"]
    }
  },
  {
    name: "write_file",
    description: "Write content to a file",
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          description: "File path to write to"
        },
        content: {
          type: "string",
          description: "Content to write to the file"
        }
      },
      required: ["path", "content"]
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
        const dirPath = args?.path ?? ".";
        try {
          const files = fs.readdirSync(dirPath);
          const fileStats = files.map(file => {
            const fullPath = path.join(dirPath, file);
            const stats = fs.statSync(fullPath);
            return {
              name: file,
              path: fullPath,
              isDirectory: stats.isDirectory(),
              size: stats.size,
              modified: stats.mtime.toISOString()
            };
          });
          
          return res.json({
            jsonrpc: "2.0",
            id,
            result: {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(fileStats, null, 2)
                }
              ]
            }
          });
        } catch (error: any) {
          return res.json({
            jsonrpc: "2.0",
            id,
            error: {
              code: -32000,
              message: `Failed to list files: ${error.message}`
            }
          });
        }
      }

      if (name === "read_file") {
        const filePath = args?.path;
        if (!filePath) {
          return res.json({
            jsonrpc: "2.0",
            id,
            error: {
              code: -32602,
              message: "Missing required parameter: path"
            }
          });
        }
        
        try {
          const content = fs.readFileSync(path.resolve(filePath), "utf8");
          return res.json({
            jsonrpc: "2.0",
            id,
            result: {
              content: [
                {
                  type: "text",
                  text: content
                }
              ]
            }
          });
        } catch (error: any) {
          return res.json({
            jsonrpc: "2.0",
            id,
            error: {
              code: -32000,
              message: `Failed to read file: ${error.message}`
            }
          });
        }
      }

      if (name === "write_file") {
        const filePath = args?.path;
        const content = args?.content;
        
        if (!filePath || content === undefined) {
          return res.json({
            jsonrpc: "2.0",
            id,
            error: {
              code: -32602,
              message: "Missing required parameters: path and content"
            }
          });
        }
        
        try {
          fs.writeFileSync(path.resolve(filePath), content, "utf8");
          return res.json({
            jsonrpc: "2.0",
            id,
            result: {
              content: [
                {
                  type: "text",
                  text: `Successfully wrote to ${filePath}`
                }
              ]
            }
          });
        } catch (error: any) {
          return res.json({
            jsonrpc: "2.0",
            id,
            error: {
              code: -32000,
              message: `Failed to write file: ${error.message}`
            }
          });
        }
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

const port = 7001;
app.listen(port, () => console.log(`Mock MCP filesystem server on http://localhost:${port}`));