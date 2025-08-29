import request from 'supertest';
import { createServer } from '../src/ui/server';

test('POST /query requires query', async () => {
  const app = createServer(async () => ({}));
  const res = await request(app).post('/query').send({});
  expect(res.status).toBe(400);
});

test('POST /query returns handler result', async () => {
  const mock = jest.fn().mockResolvedValue({ ok: true });
  const app = createServer(mock);
  const res = await request(app).post('/query').send({ query: 'hello' });
  expect(res.status).toBe(200);
  expect(res.body).toEqual({ ok: true });
  expect(mock).toHaveBeenCalledWith('hello');
});
