import http from 'http';
import request from 'supertest';
import nock from 'nock';

let server: http.Server;

beforeAll(async () => {
  process.env.MCP_FILESYSTEM_URL = 'http://localhost:7101';
  process.env.MCP_GITHUB_URL = 'http://localhost:7102';
  process.env.MCP_ATLASSIAN_URL = 'http://localhost:7103';
  process.env.MCP_GDRIVE_URL = 'http://localhost:7104';
  process.env.MCP_PLAYWRIGHT_URL = 'http://localhost:7105';

  const mod = await import('../src/proxy/server');
  server = http.createServer(mod.app);
  await new Promise<void>(resolve => server.listen(0, resolve));
});

afterAll(() => {
  server.close();
});

afterEach(() => {
  nock.cleanAll();
});

test('proxy rejects unknown target', async () => {
  const res = await request(server)
    .post('/mcp/unknown')
    .send({ jsonrpc: '2.0', method: 'ping' });
  expect(res.status).toBe(404);
  expect(res.body.error).toMatch(/Unknown target/);
});

test('forwards payload and returns downstream response', async () => {
  nock('http://localhost:7101')
    .post('/', { jsonrpc: '2.0', method: 'ping', id: 1 })
    .reply(200, { jsonrpc: '2.0', result: 'pong', id: 1 });

  const res = await request(server)
    .post('/mcp/filesystem')
    .send({ jsonrpc: '2.0', method: 'ping', id: 1 });

  expect(res.status).toBe(200);
  expect(res.body).toEqual({ jsonrpc: '2.0', result: 'pong', id: 1 });
});

test('propagates downstream error responses', async () => {
  nock('http://localhost:7101')
    .post('/').reply(500, { error: 'downstream failure' });

  const res = await request(server)
    .post('/mcp/filesystem')
    .send({ jsonrpc: '2.0', method: 'ping' });

  expect(res.status).toBe(500);
  expect(res.body.error).toBeDefined();
});

test('aggregates get_methods across configured targets', async () => {
  const targets = [
    ['filesystem', 'http://localhost:7101', 'fs methods'],
    ['github', 'http://localhost:7102', 'gh methods'],
    ['atlassian', 'http://localhost:7103', 'atl methods'],
    ['gdrive', 'http://localhost:7104', 'gd methods'],
    ['playwright', 'http://localhost:7105', 'pw methods']
  ] as const;

  for (const [key, url, result] of targets) {
    nock(url)
      .post('/', { jsonrpc: '2.0', method: 'get_methods', id: `gm-${key}` })
      .reply(200, { jsonrpc: '2.0', id: `gm-${key}`, result });
  }

  const res = await request(server).get('/mcp/get_methods');

  expect(res.status).toBe(200);
  expect(res.body.aggregated).toEqual(
    targets.map(([key, _url, result]) => [key, { jsonrpc: '2.0', id: `gm-${key}`, result }])
  );
});

