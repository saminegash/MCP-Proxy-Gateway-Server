import { RecursiveCharacterTextSplitter } from 'langchain/text_splitter';
import { MemoryVectorStore } from 'langchain/vectorstores/memory';
import { GoogleGenerativeAIEmbeddings } from '@langchain/google-genai';
import fs from 'fs';
import path from 'path';
import { config } from 'dotenv';

// Load environment variables from .env file
config();

export async function buildRetriever(kbDir = 'mock_knowledge_base') {
  const files: string[] = [];
  const walk = (p: string) => {
    for (const f of fs.readdirSync(p)) {
      const full = path.join(p, f);
      const stat = fs.statSync(full);
      if (stat.isDirectory()) walk(full);
      else files.push(full);
    }
  };
  walk(kbDir);

  const splitter = new RecursiveCharacterTextSplitter({ chunkSize: 1000, chunkOverlap: 200 });
  const docs = [];
  for (const file of files) {
    const text = fs.readFileSync(file, 'utf8');
    const splits = await splitter.splitText(text);
    docs.push(...splits.map((t, i) => ({ pageContent: t, metadata: { file, i } })));
  }
  console.log(process.env.GOOGLE_API_KEY);

  const embeddings = new GoogleGenerativeAIEmbeddings({
    apiKey: process.env.GOOGLE_API_KEY,
    model: "models/embedding-001", // uses GOOGLE_API_KEY
  });
  const store = await MemoryVectorStore.fromDocuments(docs as any, embeddings);
  return store.asRetriever(5);
}
