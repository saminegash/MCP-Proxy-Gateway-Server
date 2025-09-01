import express from "express";

const app = express();
app.use(express.json());

const METHODS = [
  { name: "list_projects", params: {}, description: "List Atlassian projects" },
  { name: "get_project", params: { key: "string" }, description: "Get project details" }
];

app.post("/", async (req, res) => {
  const { method, params, id } = req.body || {};
  try {
    if (method === "get_methods") {
      return res.json({ jsonrpc: "2.0", id, result: METHODS });
    }
    if (method === "invoke_method") {
      const { name, arguments: args } = params || {};
      if (name === "list_projects") {
        return res.json({ jsonrpc: "2.0", id, result: [{ key: "TEST", name: "Test Project" }] });
      }
      if (name === "get_project") {
        const key = args?.key ?? "TEST";
        return res.json({ jsonrpc: "2.0", id, result: { key, name: "Test Project" } });
      }
      return res.json({ jsonrpc: "2.0", id, error: { code: -32601, message: "Unknown method name" } });
    }
    return res.json({ jsonrpc: "2.0", id, error: { code: -32601, message: "Unknown RPC method" } });
  } catch (e: any) {
    return res.status(500).json({ jsonrpc: "2.0", id, error: { code: -32000, message: e?.message } });
  }
});

const port = 7003;
app.listen(port, () => console.log(`Mock MCP Atlassian server on http://localhost:${port}`));
