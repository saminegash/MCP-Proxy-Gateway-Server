import 'dotenv/config';
import { handleQuery } from './agent';

const query = process.argv.slice(2).join(' ') || 'filesystem list files';
console.log(query)
handleQuery(query).then(r => console.log(JSON.stringify(r, null, 2))).catch(console.error);
