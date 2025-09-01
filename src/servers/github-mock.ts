import express from "express";

const app = express();
app.use(express.json());

const METHODS = [
  { name: "list_repos", params: {}, description: "List repositories for the authenticated user" },
  { name: "get_repo", params: { name: "string" }, description: "Get repository details" }
];

app.post("/", async (req, res) => {
  const { method, params, id } = req.body || {};
  try {
    if (method === "get_methods") {
      return res.json({ jsonrpc: "2.0", id, result: METHODS });
    }
    if (method === "invoke_method") {
      const { name, arguments: args } = params || {};
      if (name === "list_repos") {
        return res.json({ jsonrpc: "2.0", id, result: ["example-repo", "another-repo"] });
      }
      if (name === "get_repo") {
        const repoName = args?.name ?? "example-repo";
        return res.json({ jsonrpc: "2.0", id, result: { name: repoName, stars: 42 } });
      }
      return res.json({ jsonrpc: "2.0", id, error: { code: -32601, message: "Unknown method name" } });
    }
    return res.json({ jsonrpc: "2.0", id, error: { code: -32601, message: "Unknown RPC method" } });
  } catch (e: any) {
    return res.status(500).json({ jsonrpc: "2.0", id, error: { code: -32000, message: e?.message } });
  }
});

const port = 7002;
app.listen(port, () => console.log(`Mock MCP GitHub server on http://localhost:${port}`));
