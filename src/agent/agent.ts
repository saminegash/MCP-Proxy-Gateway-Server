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

  let mcpPayload: any;
  let mcpResult: any;

  // Handle special case for listing available tools
  if (action === 'get_methods' || action === 'list_tools') {
    mcpPayload = { jsonrpc: '2.0', method: 'tools/list', id: 'demo' };
  } else {
    // For tool calls, use tools/call with proper format
    mcpPayload = { 
      jsonrpc: '2.0', 
      method: 'tools/call', 
      params: { 
        name: action, 
        arguments: args 
      }, 
      id: 'demo' 
    };
  }

  try {
    const { data } = await axios.post(`${proxyBase}/mcp/${tool}`, mcpPayload);
    mcpResult = data;
  } catch (error: any) {
    mcpResult = {
      error: {
        code: -32000,
        message: `Failed to call MCP server: ${error.message}`
      }
    };
  }

  const retriever = await getRetriever();
  const ragDocs = await retriever.getRelevantDocuments(query);

  return {
    parsed: { tool, action, args },
    mcpSnippet: mcpResult?.result ?? mcpResult,
    ragContextPreview: ragDocs.slice(0, 2).map(d => ({ file: d.metadata?.file, text: d.pageContent.slice(0, 30000) }))
  };
}
