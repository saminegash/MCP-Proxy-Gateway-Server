import axios from 'axios';
async function main() {
  const [,, url='http://localhost:7001', method='get_methods', params='{}'] = process.argv;
  const payload = { jsonrpc:'2.0', method, id:'1', params: JSON.parse(params) };
  const { data } = await axios.post(url, payload);
  console.log(JSON.stringify(data, null, 2));
}
main().catch(e=>{console.error(e);process.exit(1);});
