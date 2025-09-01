import axios from 'axios';
import { buildRetriever } from '../rag/setup';

type ToolTarget = 'github' | 'filesystem' | 'atlassian' | 'gdrive';

// lazily build and reuse the RAG retriever
let retrieverPromise: ReturnType<typeof buildRetriever> | null = null;
async function getRetriever() {
  if (!retrieverPromise) retrieverPromise = buildRetriever();
  return retrieverPromise;
}

export function parseQuery(query: string): { tool: ToolTarget; action: string; args: Record<string, string> } {
  const parts = query.trim().split(/\s+/);
  const tool = (['github', 'filesystem', 'atlassian', 'gdrive'].includes(parts[0]) ? parts[0] : 'filesystem') as ToolTarget;
  const action = parts[1] ?? 'get_methods';
  const argsParts = parts.slice(2);
  const args: Record<string, string> = {};
  for (const p of argsParts) {
    const [k, v] = p.split('=');
    if (k) args[k] = v ?? '';
  }
  return { tool, action, args };
}

export async function handleQuery(query: string, proxyBase = 'http://localhost:8002') {
  const { tool, action, args } = parseQuery(query);

  const mcpPayload = { jsonrpc: '2.0', method: 'invoke_method', params: { method: action, ...args }, id: 'demo' };
  const { data: mcpResult } = await axios.post(`${proxyBase}/mcp/${tool}`, mcpPayload);

  const retriever = await getRetriever();
  const ragDocs = await retriever.getRelevantDocuments(query);

  return {
    parsed: { tool, action, args },
    mcpSnippet: mcpResult?.result ?? mcpResult,
    ragContextPreview: ragDocs.slice(0, 2).map(d => ({ file: d.metadata?.file, text: d.pageContent.slice(0, 30000) }))
  };
}
