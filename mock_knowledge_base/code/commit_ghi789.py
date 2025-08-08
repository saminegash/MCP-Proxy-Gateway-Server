# Commit: ghi789 - RAG pipeline implementation for developer assistant (NEX-101)
# Retrieval-Augmented Generation pipeline for contextual assistance

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib

class DocumentIndexer:
    """Index documents for RAG retrieval"""
    
    def __init__(self, knowledge_base_path: str):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.index = {}
        self.documents = {}
    
    def hash_content(self, content: str) -> str:
        """Generate hash for document content"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def extract_text_from_file(self, file_path: Path) -> str:
        """Extract text content from various file types"""
        try:
            if file_path.suffix in ['.md', '.txt', '.py', '.js', '.json']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""
    
    def index_documents(self) -> Dict[str, Any]:
        """Index all documents in the knowledge base"""
        indexed_files = 0
        
        for file_path in self.knowledge_base_path.rglob('*'):
            if file_path.is_file():
                content = self.extract_text_from_file(file_path)
                if content:
                    doc_id = str(file_path.relative_to(self.knowledge_base_path))
                    doc_hash = self.hash_content(content)
                    
                    self.documents[doc_id] = {
                        'path': str(file_path),
                        'content': content,
                        'hash': doc_hash,
                        'type': file_path.suffix,
                        'size': len(content)
                    }
                    
                    # Simple keyword extraction for indexing
                    keywords = self._extract_keywords(content)
                    self.index[doc_id] = keywords
                    indexed_files += 1
        
        return {
            'indexed_files': indexed_files,
            'total_documents': len(self.documents),
            'index_size': len(self.index)
        }
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Simple keyword extraction"""
        # Basic tokenization and filtering
        words = content.lower().split()
        keywords = [w for w in words if len(w) > 3 and w.isalpha()]
        return list(set(keywords))  # Remove duplicates

class RAGRetriever:
    """Retrieve relevant documents for queries"""
    
    def __init__(self, indexer: DocumentIndexer):
        self.indexer = indexer
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        query_keywords = set(query.lower().split())
        scores = {}
        
        for doc_id, doc_keywords in self.indexer.index.items():
            # Simple keyword matching score
            matches = len(query_keywords.intersection(set(doc_keywords)))
            if matches > 0:
                scores[doc_id] = matches / len(query_keywords)
        
        # Sort by relevance score
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for doc_id, score in sorted_docs[:top_k]:
            doc = self.indexer.documents[doc_id]
            results.append({
                'document_id': doc_id,
                'score': score,
                'path': doc['path'],
                'type': doc['type'],
                'content_preview': doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content']
            })
        
        return results

class DeveloperAssistant:
    """RAG-powered developer assistant"""
    
    def __init__(self, knowledge_base_path: str):
        self.indexer = DocumentIndexer(knowledge_base_path)
        self.retriever = RAGRetriever(self.indexer)
        self.index_stats = {}
    
    def initialize(self) -> Dict[str, Any]:
        """Initialize the RAG pipeline"""
        print("Indexing knowledge base...")
        self.index_stats = self.indexer.index_documents()
        print(f"Indexed {self.index_stats['indexed_files']} files")
        return self.index_stats
    
    def query(self, user_query: str, max_results: int = 3) -> Dict[str, Any]:
        """Process user query and return relevant context"""
        print(f"Processing query: {user_query}")
        
        # Retrieve relevant documents
        relevant_docs = self.retriever.search(user_query, top_k=max_results)
        
        # Prepare context for LLM
        context = []
        for doc in relevant_docs:
            context.append({
                'source': doc['document_id'],
                'relevance_score': doc['score'],
                'content': doc['content_preview']
            })
        
        return {
            'query': user_query,
            'context': context,
            'retrieved_documents': len(relevant_docs),
            'index_stats': self.index_stats
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize the assistant
    assistant = DeveloperAssistant("./mock_knowledge_base")
    stats = assistant.initialize()
    
    # Example queries
    test_queries = [
        "login button mobile alignment",
        "MCP server implementation",
        "authentication security",
        "RAG pipeline architecture"
    ]
    
    for query in test_queries:
        result = assistant.query(query)
        print(f"\nQuery: {query}")
        print(f"Found {result['retrieved_documents']} relevant documents")
        for ctx in result['context']:
            print(f"  - {ctx['source']} (score: {ctx['relevance_score']:.2f})")