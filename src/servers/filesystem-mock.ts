import express from "express";
import fs from "fs";
import path from "path";

const app = express();
app.use(express.json());

const METHODS = [
  { name: "list_files", params: { path: "string" }, description: "List files in a directory" },
  { name: "read_file",  params: { path: "string" }, description: "Read a file" }
];

app.post("/", async (req, res) => {
  const { method, params, id } = req.body || {};
  try {
    if (method === "get_methods") {
      return res.json({ jsonrpc: "2.0", id, result: METHODS });
    }
    if (method === "invoke_method") {
      const { name, arguments: args } = params || {};
      if (name === "list_files") {
        const p = args?.path ?? ".";
        const files = fs.readdirSync(p);
        return res.json({ jsonrpc: "2.0", id, result: files });
      }
      if (name === "read_file") {
        const p = args?.path;
        const content = fs.readFileSync(path.resolve(p), "utf8");
        return res.json({ jsonrpc: "2.0", id, result: content });
      }
      return res.json({ jsonrpc: "2.0", id, error: { code: -32601, message: "Unknown method name" } });
    }
    return res.json({ jsonrpc: "2.0", id, error: { code: -32601, message: "Unknown RPC method" } });
  } catch (e: any) {
    return res.status(500).json({ jsonrpc: "2.0", id, error: { code: -32000, message: e?.message } });
  }
});

const port = 7001;
app.listen(port, () => console.log(`Mock MCP filesystem server on http://localhost:${port}`));
