import express from 'express';
import axios from 'axios';
import { z } from 'zod';
import { TARGETS, type TargetKey } from '../config/targets';
import 'dotenv/config';

const app = express();
app.use(express.json({ limit: '2mb' }));

const JsonRpcSchema = z.object({
  jsonrpc: z.literal('2.0'),
  method: z.string(),
  params: z.any().optional(),
  id: z.union([z.string(), z.number()]).optional()
});

// Route style: /mcp/:target/invoke (for JSON-RPC pass-through)
app.post('/mcp/:target', async (req, res) => {
  try {
    const { target } = req.params as { target: TargetKey };
    const downstream = TARGETS[target];
    console.log("downstream",downstream)
    if (!downstream) return res.status(404).json({ error: `Unknown target ${target}` });

    const payload = JsonRpcSchema.parse(req.body);
    const { data } = await axios.post(downstream, payload, { timeout: 15000 });

    return res.status(200).json(data);
  } catch (err: any) {
    const status = err?.response?.status ?? 500;
    return res.status(status).json({ error: err?.message ?? 'Proxy error', details: err?.response?.data });
  }
});

// Optional: aggregate get_methods
app.get('/mcp/get_methods', async (_req, res) => {
  const entries = Object.entries(TARGETS) as [TargetKey, string][];
  const results = await Promise.allSettled(entries.map(async ([key, url]) => {
    const payload = { jsonrpc: '2.0', method: 'get_methods', id: `gm-${key}` };
    console.log(payload, entries)
    const { data } = await axios.post(url, payload, { timeout: 10000 });
    return [key, data] as const;
  }));
  const aggregated = results.map(r => r.status === 'fulfilled' ? r.value : r.reason?.message);
  res.json({ aggregated });
});

const port = Number(process.env.PORT || 8002);
app.listen(port, () => console.log(`MCP Proxy listening on http://localhost:${port}`));
