import { handleQuery } from './agent.js';

const query = process.argv.slice(2).join(' ') || 'filesystem list files';
handleQuery(query).then(r => console.log(JSON.stringify(r, null, 2))).catch(console.error);
