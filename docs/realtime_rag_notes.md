# Real-Time RAG Notes

Pathway enables live indexing for retrieval augmented generation (RAG) by continuously syncing data sources with a vector store.

## Core Ideas
- **Streaming ingestion** – connectors watch files, databases, or message queues and push updates as they happen.
- **Incremental embedding** – only new or changed records are embedded and written to the index, keeping operations fast.
- **Data pipeline primitives** – Pathway builds a DAG of transformations (parsing, chunking, embedding) that reruns automatically when upstream data changes.
- **Low-latency queries** – the index is always current, so RAG agents can answer with the most recent information.

## Example Flow
1. A document lands in object storage.
2. A Pathway watcher detects the change.
3. The document is chunked and embedded.
4. The vector store is updated without downtime.
5. Subsequent RAG queries instantly retrieve the new content.

## Benefits
- No manual re-indexing cycles.
- Handles late or out-of-order data.
- Scales to many sources and high update rates.

Pathway's approach ensures that knowledge bases used by agents remain synchronized with reality, enabling trustworthy real-time responses.
