import request from 'supertest';
import express from 'express';
import axios from 'axios';
import http from 'http';
import { createApp } from '../src/ui/server';

jest.mock('../src/rag/setup', () => ({
  buildRetriever: jest.fn().mockResolvedValue({
    getRelevantDocuments: jest.fn().mockResolvedValue([
      { pageContent: 'hello world', metadata: { file: 'mock.txt' } }
    ])
  })
}));

describe('end-to-end query flow', () => {
  let fsServer: http.Server;
  let proxyServer: http.Server;

  beforeAll(async () => {
    const fsApp = express();
    fsApp.use(express.json());
    fsApp.post('/', (req, res) => {
      res.json({ jsonrpc: '2.0', id: req.body.id, result: { methods: ['get_methods'] } });
    });
    await new Promise<void>(resolve => {
      fsServer = fsApp.listen(7001, () => resolve());
    });

    const proxyApp = express();
    proxyApp.use(express.json());
    proxyApp.post('/mcp/:target', async (req, res) => {
      if (req.params.target !== 'filesystem') return res.status(404).json({ error: 'Unknown target' });
      const { data } = await axios.post('http://localhost:7001', req.body);
      res.json(data);
    });
    await new Promise<void>(resolve => {
      proxyServer = proxyApp.listen(8002, () => resolve());
    });
  });

  afterAll(() => {
    fsServer.close();
    proxyServer.close();
  });

  test('query succeeds through full stack', async () => {
    const app = createApp();
    const res = await request(app).post('/api/query').send({ query: 'filesystem question' });
    expect(res.status).toBe(200);
    expect(res.body.parsed).toBeDefined();
    expect(res.body.parsed.tool).toBe('filesystem');
    expect(res.body.mcpSnippet).toBeDefined();
    expect(res.body.ragContextPreview).toBeDefined();
    expect(res.body.ragContextPreview[0].text).toContain('hello world');
  });
});
