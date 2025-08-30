import express from 'express';
import path from 'path';
import { handleQuery } from '../agent/agent';

export function createApp() {
  const app = express();
  app.use(express.json());

  const indexPath = path.join(__dirname, '..', '..', 'public', 'index.html');

  app.get('/', (_req, res) => {
    res.sendFile(indexPath);
  });

  app.post('/api/query', async (req, res) => {
    const { query } = req.body || {};
    if (!query) return res.status(400).json({ error: 'query required' });
    try {
      const result = await handleQuery(query);
      res.json(result);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  return app;
}

if (process.env.NODE_ENV !== 'test') {
  const port = Number(process.env.UI_PORT || 3000);
  createApp().listen(port, () =>
    console.log(`UI server listening on http://localhost:${port}`)
  );
}
