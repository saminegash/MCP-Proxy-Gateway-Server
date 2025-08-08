# Commit: jkl012 - Enhanced embedding strategy for RAG (NEX-101)
# Advanced embedding and vector similarity for better document retrieval

import numpy as np
from typing import List, Dict, Any, Tuple
import json
import pickle
from pathlib import Path

class SimpleEmbedding:
    """Simple word embedding implementation for demonstration"""
    
    def __init__(self, vocab_size: int = 10000, embed_dim: int = 128):
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.word_to_idx = {}
        self.idx_to_word = {}
        self.embeddings = None
        self.vocab_built = False
    
    def build_vocabulary(self, documents: List[str]) -> None:
        """Build vocabulary from documents"""
        word_freq = {}
        
        for doc in documents:
            words = doc.lower().split()
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and take top words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Reserve indices for special tokens
        self.word_to_idx = {'<UNK>': 0, '<PAD>': 1}
        self.idx_to_word = {0: '<UNK>', 1: '<PAD>'}
        
        for i, (word, _) in enumerate(sorted_words[:self.vocab_size-2]):
            idx = i + 2
            self.word_to_idx[word] = idx
            self.idx_to_word[idx] = word
        
        # Initialize random embeddings
        np.random.seed(42)
        self.embeddings = np.random.normal(0, 0.1, (len(self.word_to_idx), self.embed_dim))
        self.vocab_built = True
    
    def encode_text(self, text: str) -> np.ndarray:
        """Convert text to embedding vector"""
        if not self.vocab_built:
            raise ValueError("Vocabulary not built. Call build_vocabulary first.")
        
        words = text.lower().split()
        vectors = []
        
        for word in words:
            idx = self.word_to_idx.get(word, 0)  # Use <UNK> for unknown words
            vectors.append(self.embeddings[idx])
        
        if not vectors:
            return np.zeros(self.embed_dim)
        
        # Average word embeddings to get document embedding
        return np.mean(vectors, axis=0)
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return np.dot(vec1, vec2) / (norm1 * norm2)

class VectorStore:
    """Simple vector store for document embeddings"""
    
    def __init__(self, embedding_model: SimpleEmbedding):
        self.embedding_model = embedding_model
        self.documents = {}
        self.vectors = {}
        self.metadata = {}
    
    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """Add document to vector store"""
        vector = self.embedding_model.encode_text(content)
        
        self.documents[doc_id] = content
        self.vectors[doc_id] = vector
        self.metadata[doc_id] = metadata or {}
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar documents"""
        query_vector = self.embedding_model.encode_text(query)
        similarities = []
        
        for doc_id, doc_vector in self.vectors.items():
            similarity = self.embedding_model.cosine_similarity(query_vector, doc_vector)
            similarities.append((doc_id, similarity, self.metadata[doc_id]))
        
        # Sort by similarity score
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def save(self, filepath: str) -> None:
        """Save vector store to file"""
        data = {
            'documents': self.documents,
            'vectors': {k: v.tolist() for k, v in self.vectors.items()},
            'metadata': self.metadata
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filepath: str) -> None:
        """Load vector store from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.documents = data['documents']
        self.vectors = {k: np.array(v) for k, v in data['vectors'].items()}
        self.metadata = data['metadata']

class EnhancedRAGPipeline:
    """Enhanced RAG pipeline with vector similarity"""
    
    def __init__(self, knowledge_base_path: str):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.embedding_model = SimpleEmbedding()
        self.vector_store = VectorStore(self.embedding_model)
        self.indexed = False
    
    def index_documents(self) -> Dict[str, Any]:
        """Index all documents with embeddings"""
        documents = []
        doc_info = []
        
        # Collect all documents
        for file_path in self.knowledge_base_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in ['.md', '.txt', '.py', '.json']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    doc_id = str(file_path.relative_to(self.knowledge_base_path))
                    documents.append(content)
                    doc_info.append({
                        'id': doc_id,
                        'path': str(file_path),
                        'content': content,
                        'type': file_path.suffix
                    })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
        
        # Build vocabulary and embeddings
        print("Building vocabulary...")
        self.embedding_model.build_vocabulary(documents)
        
        # Add documents to vector store
        print("Creating document embeddings...")
        for doc in doc_info:
            metadata = {
                'path': doc['path'],
                'type': doc['type'],
                'size': len(doc['content'])
            }
            self.vector_store.add_document(doc['id'], doc['content'], metadata)
        
        self.indexed = True
        
        return {
            'total_documents': len(doc_info),
            'vocabulary_size': len(self.embedding_model.word_to_idx),
            'embedding_dimension': self.embedding_model.embed_dim
        }
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents using vector similarity"""
        if not self.indexed:
            raise ValueError("Documents not indexed. Call index_documents first.")
        
        results = self.vector_store.search(query, top_k)
        
        formatted_results = []
        for doc_id, similarity, metadata in results:
            content = self.vector_store.documents[doc_id]
            formatted_results.append({
                'document_id': doc_id,
                'similarity_score': float(similarity),
                'metadata': metadata,
                'content_preview': content[:300] + '...' if len(content) > 300 else content
            })
        
        return formatted_results
    
    def get_context_for_query(self, query: str, max_context_length: int = 1000) -> str:
        """Get formatted context for LLM from retrieved documents"""
        results = self.search(query, top_k=3)
        
        context_parts = []
        current_length = 0
        
        for result in results:
            doc_header = f"Source: {result['document_id']} (relevance: {result['similarity_score']:.3f})\n"
            doc_content = result['content_preview']
            
            if current_length + len(doc_header) + len(doc_content) > max_context_length:
                break
            
            context_parts.append(doc_header + doc_content)
            current_length += len(doc_header) + len(doc_content)
        
        return "\n\n---\n\n".join(context_parts)

# Example usage
if __name__ == "__main__":
    pipeline = EnhancedRAGPipeline("./mock_knowledge_base")
    
    # Index documents
    stats = pipeline.index_documents()
    print(f"Indexed {stats['total_documents']} documents")
    print(f"Vocabulary size: {stats['vocabulary_size']}")
    
    # Test queries
    test_queries = [
        "login authentication mobile",
        "MCP server protocol implementation",
        "vector embedding similarity"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = pipeline.search(query, top_k=3)
        for result in results:
            print(f"  {result['document_id']}: {result['similarity_score']:.3f}")
        
        context = pipeline.get_context_for_query(query)
        print(f"Context length: {len(context)} characters")