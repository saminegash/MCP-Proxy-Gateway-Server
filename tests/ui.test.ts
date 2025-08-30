import request from 'supertest';
import { createApp } from '../src/ui/server';

jest.mock('../src/agent/agent', () => ({
  handleQuery: jest.fn().mockResolvedValue({ ok: true })
}));

const { handleQuery } = jest.requireMock('../src/agent/agent');

describe('UI query endpoint', () => {
  test('returns agent result', async () => {
    const app = createApp();
    const res = await request(app).post('/api/query').send({ query: 'test' });
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ ok: true });
    expect(handleQuery).toHaveBeenCalledWith('test');
  });

  test('requires query', async () => {
    const app = createApp();
    const res = await request(app).post('/api/query').send({});
    expect(res.status).toBe(400);
  });
});
