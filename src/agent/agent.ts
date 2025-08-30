import axios from 'axios';
import { buildRetriever } from '../rag/setup';

type ToolTarget = 'github' | 'filesystem' | 'atlassian' | 'gdrive';

export async function handleQuery(query: string, proxyBase = 'http://localhost:8002') {
  // naive parse: look for "github|filesystem|atlassian|gdrive"
  const target = (['github','filesystem','atlassian','gdrive'].find(t => query.toLowerCase().includes(t)) ?? 'filesystem') as ToolTarget;

  // Example: translate to an MCP call
  const mcpPayload = { jsonrpc: '2.0', method: 'get_methods', id: 'demo' };
  const { data: mcpResult } = await axios.post(`${proxyBase}/mcp/${target}`, mcpPayload);
  const retriever = await buildRetriever();
  const ragDocs = await retriever.getRelevantDocuments(query);
  console.log(ragDocs)
  // super simple synthesis
  return {
    targetUsed: target,
    mcpSnippet: mcpResult?.result ?? mcpResult,
    ragContextPreview: ragDocs.slice(0, 2).map(d => ({ file: d.metadata?.file, text: d.pageContent.slice(0, 30000) }))
  };
}
