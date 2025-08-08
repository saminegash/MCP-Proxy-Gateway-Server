import request from 'supertest';
import http from 'http';
import express from 'express';

test('proxy rejects unknown target', async () => {
  const app = express();
  app.use(express.json());
  app.post('/mcp/:target', (req, res) => res.status(404).json({ error: 'Unknown target foo' }));
  const server = http.createServer(app);
  await new Promise(r => server.listen(0, () => r(undefined)));
  const addr = server.address() as any;
  const base = `http://127.0.0.1:${addr.port}`;
  const res = await request(base).post('/mcp/foo').send({ jsonrpc: '2.0', method: 'get_methods' });
  expect(res.status).toBe(404);
  server.close();
});
