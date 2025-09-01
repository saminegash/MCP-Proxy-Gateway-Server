// import axios from 'axios';
// async function main() {
//   const [,, url='http://localhost:7001', method='get_methods', params='{}'] = process.argv;
//   const payload = { jsonrpc:'2.0', method, id:'1', params: JSON.parse(params) };
//   const { data } = await axios.post(url, payload);
//   console.log(JSON.stringify(data, null, 2));
// }
// main().catch(e=>{console.error(e);process.exit(1);});


import axios from 'axios';

async function main() {
  const [,, target = 'filesystem', method = 'tools/list', toolName = '', args = '{}', proxyBase = 'http://localhost:8002'] = process.argv;

  let payload: any;

  // Handle different MCP method types
  if (method === 'tools/list' || method === 'get_methods') {
    payload = { jsonrpc: '2.0', method: 'tools/list', id: '1' };
  } else if (method === 'tools/call') {
    let parsedArgs: any = {};
    try {
      parsedArgs = JSON.parse(args);
    } catch (err) {
      console.error('Failed to parse arguments JSON:', err);
      process.exit(1);
    }

    payload = { 
      jsonrpc: '2.0', 
      method: 'tools/call', 
      params: { 
        name: toolName, 
        arguments: parsedArgs 
      }, 
      id: '1' 
    };
  } else {
    // Legacy support - treat as custom method
    let parsedParams: any = {};
    try {
      parsedParams = JSON.parse(args);
    } catch (err) {
      console.error('Failed to parse params JSON:', err);
      process.exit(1);
    }
    payload = { jsonrpc: '2.0', method, id: '1', params: parsedParams };
  }

  const url = `${proxyBase}/mcp/${target}`;
  console.log(`Calling ${url} with payload:`, JSON.stringify(payload, null, 2));
  
  try {
    const { data } = await axios.post(url, payload);
    console.log('Response:', JSON.stringify(data, null, 2));
  } catch (error: any) {
    console.error('Error:', error.response?.data || error.message);
  }
}

main().catch(e => { console.error(e); process.exit(1); });
