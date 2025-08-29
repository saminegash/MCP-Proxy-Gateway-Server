import { createServer } from './server.js';

const port = Number(process.env.UI_PORT || 3000);
const app = createServer();
app.listen(port, () => console.log(`Dev Assistant UI at http://localhost:${port}`));
