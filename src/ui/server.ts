import express from 'express';
import path from 'path';
import { handleQuery } from '../agent/agent.js';

export function createServer(queryHandler: (q: string) => Promise<any> = handleQuery) {
  const app = express();
  app.use(express.json());

  const publicDir = path.join(process.cwd(), 'public');
  app.use(express.static(publicDir));

  app.post('/query', async (req, res) => {
    const { query } = req.body || {};
    if (typeof query !== 'string' || !query.trim()) {
      return res.status(400).json({ error: 'query required' });
    }
    try {
      const result = await queryHandler(query);
      return res.json(result);
    } catch (err: any) {
      return res.status(500).json({ error: err?.message || 'handler error' });
    }
  });

  return app;
}
