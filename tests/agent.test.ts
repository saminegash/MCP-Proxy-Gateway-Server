
describe('agent query handling', () => {
  beforeEach(() => {
    jest.resetModules();
  });

  test('parses query, invokes MCP and synthesizes', async () => {
    const mockRetriever = {
      getRelevantDocuments: jest.fn().mockResolvedValue([
        { metadata: { file: 'a.txt' }, pageContent: 'hello world' }
      ])
    };

    jest.doMock('axios', () => ({ post: jest.fn().mockResolvedValue({ data: { result: 'ok' } }) }));
    jest.doMock('../src/rag/setup', () => ({ buildRetriever: jest.fn().mockResolvedValue(mockRetriever) }));

    const { handleQuery } = require('../src/agent/agent');
    const axios = require('axios');
    const { buildRetriever } = require('../src/rag/setup');

    const res = await handleQuery('github get_user user=octocat');

    expect(res.parsed).toEqual({ tool: 'github', action: 'get_user', args: { user: 'octocat' } });
    expect((axios.post as jest.Mock)).toHaveBeenCalledWith('http://localhost:8002/mcp/github', {
      jsonrpc: '2.0',
      method: 'invoke_method',
      params: { method: 'get_user', user: 'octocat' },
      id: 'demo'
    });
    expect(mockRetriever.getRelevantDocuments).toHaveBeenCalledWith('github get_user user=octocat');
    expect(res.mcpSnippet).toBe('ok');
    expect(res.ragContextPreview).toEqual([{ file: 'a.txt', text: 'hello world' }]);
    expect((buildRetriever as jest.Mock)).toHaveBeenCalledTimes(1);
  });

  test('reuses retriever between calls', async () => {
    const mockRetriever = {
      getRelevantDocuments: jest.fn().mockResolvedValue([])
    };

    jest.doMock('axios', () => ({ post: jest.fn().mockResolvedValue({ data: { result: 'ok' } }) }));
    jest.doMock('../src/rag/setup', () => ({ buildRetriever: jest.fn().mockResolvedValue(mockRetriever) }));

    const { handleQuery } = require('../src/agent/agent');
    const { buildRetriever } = require('../src/rag/setup');

    await handleQuery('filesystem read path=/a');
    await handleQuery('filesystem read path=/b');

    expect((buildRetriever as jest.Mock)).toHaveBeenCalledTimes(1);
    expect(mockRetriever.getRelevantDocuments).toHaveBeenCalledTimes(2);
  });
});
