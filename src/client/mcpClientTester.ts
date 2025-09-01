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
  const [,, target = 'filesystem', method = 'get_methods', params = '{}', proxyBase = 'http://localhost:8002'] = process.argv;

  let parsedParams: any = {};
  try {
    parsedParams = JSON.parse(params);
  } catch (err) {
    console.error('Failed to parse params JSON:', err);
    process.exit(1);
  }

  const payload = { jsonrpc: '2.0', method, id: '1', params: parsedParams };
  const url = `${proxyBase}/mcp/${target}`;
  const { data } = await axios.post(url, payload);
  console.log(JSON.stringify(data, null, 2));
}

main().catch(e => { console.error(e); process.exit(1); });
