import express from "express";

const app = express();
app.use(express.json());

const METHODS = [
  { name: "list_files", params: {}, description: "List Google Drive files" },
  { name: "get_file", params: { id: "string" }, description: "Get file contents" }
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
        return res.json({ jsonrpc: "2.0", id, result: [{ id: "1", name: "Doc1" }, { id: "2", name: "Sheet1" }] });
      }
      if (name === "get_file") {
        const fileId = args?.id ?? "1";
        return res.json({ jsonrpc: "2.0", id, result: { id: fileId, name: "Doc1", content: "Hello world" } });
      }
      return res.json({ jsonrpc: "2.0", id, error: { code: -32601, message: "Unknown method name" } });
    }
    return res.json({ jsonrpc: "2.0", id, error: { code: -32601, message: "Unknown RPC method" } });
  } catch (e: any) {
    return res.status(500).json({ jsonrpc: "2.0", id, error: { code: -32000, message: e?.message } });
  }
});

const port = 7004;
app.listen(port, () => console.log(`Mock MCP Google Drive server on http://localhost:${port}`));
