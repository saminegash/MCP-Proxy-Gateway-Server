# RAG Architecture Documentation

This document describes the Retrieval-Augmented Generation (RAG) architecture for the NexusAI developer assistant platform.

## Overview

The RAG pipeline enables AI agents to provide contextually relevant responses by retrieving information from a comprehensive knowledge base containing code, documentation, and project artifacts.

## Architecture Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │    │  RAG Pipeline   │    │ Knowledge Base  │
│                 │───►│                 │◄──►│                 │
│ "Fix login bug" │    │ 1. Retrieval    │    │ - Code          │
│                 │    │ 2. Ranking      │    │ - Docs          │
│                 │    │ 3. Context      │    │ - JIRA tickets  │
│                 │    │ 4. Generation   │    │ - Commit logs   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                      ┌─────────────────┐
                      │   LLM Response  │
                      │                 │
                      │ Contextual      │
                      │ Answer with     │
                      │ Code Examples   │
                      └─────────────────┘
```

## Pipeline Stages

### 1. Document Ingestion

#### Supported Document Types
- **Source Code**: .py, .js, .ts, .java, .cpp, .go, .rs
- **Documentation**: .md, .rst, .txt
- **Configuration**: .json, .yaml, .yml, .toml
- **Project Files**: README, CHANGELOG, requirements.txt

#### Processing Pipeline
```python
def process_document(file_path: str, content: str) -> Document:
    """Process a single document for indexing"""
    
    # 1. Extract metadata
    metadata = {
        'file_path': file_path,
        'file_type': Path(file_path).suffix,
        'language': detect_language(file_path),
        'size': len(content),
        'last_modified': get_file_mtime(file_path)
    }
    
    # 2. Parse content structure
    if metadata['language'] == 'python':
        structure = parse_python_ast(content)
    elif metadata['file_type'] == '.md':
        structure = parse_markdown_structure(content)
    else:
        structure = extract_basic_structure(content)
    
    # 3. Chunk content
    chunks = chunk_content(content, metadata['file_type'])
    
    # 4. Generate embeddings
    embeddings = []
    for chunk in chunks:
        embedding = embedding_model.encode(chunk)
        embeddings.append(embedding)
    
    return Document(
        content=content,
        metadata=metadata,
        structure=structure,
        chunks=chunks,
        embeddings=embeddings
    )
```

### 2. Embedding Generation

#### Embedding Strategy
- **Model**: Code-aware embedding model (e.g., CodeBERT, StarEncoder)
- **Chunk Size**: 512 tokens with 50-token overlap
- **Dimension**: 768-dimensional vectors
- **Normalization**: L2 normalized for cosine similarity

#### Code-Specific Features
```python
class CodeAwareEmbedding:
    def __init__(self):
        self.base_model = SentenceTransformer('microsoft/codebert-base')
        self.code_tokenizer = CodeTokenizer()
    
    def encode_code(self, code: str, language: str) -> np.ndarray:
        """Generate embeddings optimized for code"""
        
        # Extract code features
        features = self.code_tokenizer.extract_features(code, language)
        
        # Combine base embedding with code features
        base_embedding = self.base_model.encode(code)
        
        # Weight important code elements
        weighted_features = self.weight_code_features(features)
        
        # Concatenate and normalize
        enhanced_embedding = np.concatenate([
            base_embedding,
            weighted_features
        ])
        
        return enhanced_embedding / np.linalg.norm(enhanced_embedding)
    
    def weight_code_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Apply weights to different code features"""
        weights = {
            'function_names': 2.0,
            'class_names': 2.0,
            'imports': 1.5,
            'method_calls': 1.2,
            'variables': 1.0,
            'comments': 0.8
        }
        
        weighted_vector = np.zeros(256)  # Feature vector size
        
        for feature_type, items in features.items():
            weight = weights.get(feature_type, 1.0)
            feature_vector = self.vectorize_features(items)
            weighted_vector += feature_vector * weight
        
        return weighted_vector
```

### 3. Vector Storage

#### Vector Database Schema
```sql
-- Vector store schema
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding VECTOR(768),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_embedding_similarity 
ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX idx_document_metadata 
ON document_embeddings 
USING GIN (metadata);
```

#### Retrieval Implementation
```python
class VectorRetriever:
    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
    
    async def search(self, query_vector: np.ndarray, 
                    top_k: int = 10,
                    filters: Dict[str, Any] = None) -> List[Document]:
        """Retrieve most similar documents"""
        
        # Build filter conditions
        filter_conditions = []
        params = [query_vector.tolist(), top_k]
        
        if filters:
            if 'file_type' in filters:
                filter_conditions.append("metadata->>'file_type' = %s")
                params.append(filters['file_type'])
            
            if 'language' in filters:
                filter_conditions.append("metadata->>'language' = %s")
                params.append(filters['language'])
        
        where_clause = ""
        if filter_conditions:
            where_clause = "WHERE " + " AND ".join(filter_conditions)
        
        query = f"""
        SELECT document_id, chunk_index, embedding, metadata,
               1 - (embedding <=> %s) as similarity
        FROM document_embeddings
        {where_clause}
        ORDER BY embedding <=> %s
        LIMIT %s
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            doc_id, chunk_idx, embedding, metadata, similarity = row
            results.append({
                'document_id': doc_id,
                'chunk_index': chunk_idx,
                'similarity': similarity,
                'metadata': metadata
            })
        
        return results
```

### 4. Query Processing

#### Query Analysis
```python
class QueryProcessor:
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
    
    def analyze_query(self, query: str) -> QueryIntent:
        """Analyze user query to understand intent"""
        
        # Classify intent
        intent = self.intent_classifier.predict(query)
        
        # Extract entities
        entities = self.entity_extractor.extract(query)
        
        # Determine search strategy
        search_strategy = self.determine_search_strategy(intent, entities)
        
        return QueryIntent(
            original_query=query,
            intent_type=intent,
            entities=entities,
            search_strategy=search_strategy,
            filters=self.build_filters(entities)
        )
    
    def determine_search_strategy(self, intent: str, entities: Dict[str, Any]) -> str:
        """Choose optimal search strategy based on query analysis"""
        
        if intent == "code_search":
            return "semantic_code_search"
        elif intent == "debug_help":
            return "error_context_search"
        elif intent == "api_usage":
            return "documentation_search"
        else:
            return "hybrid_search"
```

#### Multi-Modal Retrieval
```python
class HybridRetriever:
    def __init__(self):
        self.vector_retriever = VectorRetriever()
        self.keyword_retriever = KeywordRetriever()
        self.graph_retriever = GraphRetriever()
    
    async def retrieve(self, query: QueryIntent, top_k: int = 10) -> List[Document]:
        """Combine multiple retrieval strategies"""
        
        # Vector search
        vector_results = await self.vector_retriever.search(
            query.embedding, 
            top_k=top_k,
            filters=query.filters
        )
        
        # Keyword search
        keyword_results = await self.keyword_retriever.search(
            query.original_query,
            top_k=top_k
        )
        
        # Graph-based search (for code relationships)
        if query.intent_type == "code_search":
            graph_results = await self.graph_retriever.search(
                query.entities,
                top_k=top_k//2
            )
        else:
            graph_results = []
        
        # Fusion ranking
        fused_results = self.fuse_results([
            vector_results,
            keyword_results, 
            graph_results
        ])
        
        return fused_results[:top_k]
    
    def fuse_results(self, result_sets: List[List[Document]]) -> List[Document]:
        """Fuse multiple result sets using Reciprocal Rank Fusion"""
        
        doc_scores = defaultdict(float)
        
        for rank_position, result_set in enumerate(result_sets):
            weight = 1.0 / (rank_position + 1)  # Higher weight for first result set
            
            for rank, doc in enumerate(result_set):
                doc_id = doc['document_id']
                rr_score = weight / (rank + 1)
                doc_scores[doc_id] += rr_score
        
        # Sort by fused score
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [self.get_document(doc_id) for doc_id, score in sorted_docs]
```

### 5. Context Generation

#### Context Assembly
```python
class ContextBuilder:
    def __init__(self, max_context_length: int = 4000):
        self.max_context_length = max_context_length
    
    def build_context(self, query: str, retrieved_docs: List[Document]) -> str:
        """Build context for LLM from retrieved documents"""
        
        context_parts = []
        current_length = 0
        
        # Add query
        query_section = f"User Query: {query}\n\nRelevant Information:\n\n"
        context_parts.append(query_section)
        current_length += len(query_section)
        
        # Group documents by type
        grouped_docs = self.group_documents_by_type(retrieved_docs)
        
        # Prioritize code files for code-related queries
        type_priority = self.determine_type_priority(query)
        
        for doc_type in type_priority:
            if doc_type not in grouped_docs:
                continue
                
            docs = grouped_docs[doc_type]
            type_header = f"=== {doc_type.upper()} ===\n"
            
            if current_length + len(type_header) > self.max_context_length:
                break
                
            context_parts.append(type_header)
            current_length += len(type_header)
            
            for doc in docs:
                doc_section = self.format_document(doc)
                
                if current_length + len(doc_section) > self.max_context_length:
                    # Truncate if necessary
                    remaining_space = self.max_context_length - current_length
                    if remaining_space > 100:  # Minimum useful content
                        doc_section = doc_section[:remaining_space-3] + "..."
                        context_parts.append(doc_section)
                    break
                
                context_parts.append(doc_section)
                current_length += len(doc_section)
        
        return "\n".join(context_parts)
    
    def format_document(self, doc: Document) -> str:
        """Format document for inclusion in context"""
        
        file_path = doc['metadata']['file_path']
        content = doc['content']
        
        if doc['metadata']['file_type'] in ['.py', '.js', '.ts']:
            # Format code with syntax highlighting info
            return f"File: {file_path}\n```{doc['metadata']['language']}\n{content}\n```\n\n"
        else:
            # Format documentation
            return f"Document: {file_path}\n{content}\n\n"
```

## Performance Optimization

### Indexing Performance
- **Batch Processing**: Process documents in batches of 100
- **Parallel Embedding**: Generate embeddings using multiple GPU cores
- **Incremental Updates**: Only reprocess changed documents
- **Compression**: Use quantized embeddings for reduced storage

### Query Performance
- **Caching**: Cache frequent query embeddings
- **Index Optimization**: Use approximate nearest neighbor search (FAISS, Annoy)
- **Query Optimization**: Pre-filter documents before vector search
- **Connection Pooling**: Reuse database connections

### Memory Management
```python
class MemoryOptimizedRAG:
    def __init__(self, cache_size: int = 1000):
        self.embedding_cache = LRUCache(cache_size)
        self.document_cache = LRUCache(cache_size // 2)
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding with caching"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        if text_hash in self.embedding_cache:
            return self.embedding_cache[text_hash]
        
        embedding = self.embedding_model.encode(text)
        self.embedding_cache[text_hash] = embedding
        
        return embedding
    
    def cleanup_memory(self):
        """Periodic memory cleanup"""
        gc.collect()
        torch.cuda.empty_cache()  # If using GPU
```

## Real-Time Updates

### Change Detection
```python
class RealTimeIndexer:
    def __init__(self, knowledge_base_path: str):
        self.watcher = FileWatcher(knowledge_base_path)
        self.update_queue = asyncio.Queue()
    
    async def start_watching(self):
        """Start real-time file monitoring"""
        
        async def handle_file_change(event):
            if event.event_type == 'modified':
                await self.update_queue.put({
                    'action': 'update',
                    'file_path': event.src_path,
                    'timestamp': time.time()
                })
            elif event.event_type == 'deleted':
                await self.update_queue.put({
                    'action': 'delete',
                    'file_path': event.src_path,
                    'timestamp': time.time()
                })
        
        self.watcher.on_file_change = handle_file_change
        await self.watcher.start()
    
    async def process_updates(self):
        """Process file updates in real-time"""
        
        while True:
            try:
                update = await self.update_queue.get()
                
                if update['action'] == 'update':
                    await self.reindex_document(update['file_path'])
                elif update['action'] == 'delete':
                    await self.remove_document(update['file_path'])
                
            except Exception as e:
                logger.error(f"Error processing update: {e}")
```

## Evaluation & Metrics

### Retrieval Metrics
- **Recall@K**: Percentage of relevant documents in top-K results
- **Precision@K**: Percentage of top-K results that are relevant
- **MRR**: Mean Reciprocal Rank of first relevant result
- **NDCG**: Normalized Discounted Cumulative Gain

### Generation Metrics
- **BLEU**: N-gram overlap with reference answers
- **ROUGE**: Recall-oriented metric for text summarization
- **BERTScore**: Semantic similarity using BERT embeddings
- **Human Evaluation**: Expert assessment of response quality

### Performance Metrics
```python
class RAGMetrics:
    def __init__(self):
        self.retrieval_times = []
        self.generation_times = []
        self.total_times = []
    
    def evaluate_retrieval(self, query: str, retrieved_docs: List[Document], 
                          relevant_docs: List[str]) -> Dict[str, float]:
        """Evaluate retrieval performance"""
        
        retrieved_ids = [doc['document_id'] for doc in retrieved_docs]
        
        # Calculate metrics
        relevant_retrieved = set(retrieved_ids) & set(relevant_docs)
        
        precision = len(relevant_retrieved) / len(retrieved_ids) if retrieved_ids else 0
        recall = len(relevant_retrieved) / len(relevant_docs) if relevant_docs else 0
        
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'retrieved_count': len(retrieved_ids),
            'relevant_count': len(relevant_docs)
        }
```

## Security Considerations

### Access Control
- **Document-Level Permissions**: Control access to sensitive documents
- **Query Filtering**: Filter results based on user permissions
- **Audit Logging**: Track all query and retrieval activities

### Data Privacy
- **Content Anonymization**: Remove sensitive data from embeddings
- **Secure Storage**: Encrypt embeddings and metadata at rest
- **Access Logs**: Monitor and log all data access

## Deployment Architecture

### Production Setup
```yaml
# docker-compose.yml
version: '3.8'
services:
  rag-api:
    image: nexusai/rag-api:latest
    environment:
      - POSTGRES_URL=postgresql://user:pass@db:5432/rag
      - REDIS_URL=redis://cache:6379
      - EMBEDDING_MODEL_PATH=/models/codebert
    depends_on:
      - db
      - cache
    ports:
      - "8080:8080"
  
  db:
    image: pgvector/pgvector:pg15
    environment:
      - POSTGRES_DB=rag
      - POSTGRES_USER=rag_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  cache:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
```

### Scaling Strategies
- **Horizontal Scaling**: Multiple RAG API instances behind load balancer
- **Database Sharding**: Partition embeddings across multiple databases
- **Caching Layers**: Multi-level caching (application, Redis, CDN)
- **Async Processing**: Background document processing queues

## Related Documentation
- [Embedding Strategy](embedding_strategy.md)
- [Vector Store Design](vector_store_design.md)
- [Performance Metrics](performance_metrics.md)
- [Real-time Indexing with Pathway](pathway_integration.md)