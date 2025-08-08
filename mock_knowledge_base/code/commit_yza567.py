# Commit: yza567 - Optimize vector embeddings for code search (NEX-606)
# Advanced embedding optimization for improved code similarity search

import numpy as np
import ast
import tokenize
import io
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
import hashlib

class CodeTokenizer:
    """Advanced tokenizer for source code"""
    
    def __init__(self):
        self.python_keywords = {
            'def', 'class', 'import', 'from', 'if', 'else', 'elif', 'for', 'while',
            'try', 'except', 'finally', 'with', 'return', 'yield', 'async', 'await'
        }
        
        self.code_patterns = {
            'function_def': r'def\s+(\w+)',
            'class_def': r'class\s+(\w+)',
            'variable': r'(\w+)\s*=',
            'method_call': r'(\w+)\s*\(',
            'import_stmt': r'(?:from\s+)?(\w+(?:\.\w+)*)\s*import'
        }
    
    def extract_code_features(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """Extract semantic features from code"""
        features = {
            'functions': [],
            'classes': [],
            'imports': [],
            'variables': [],
            'method_calls': [],
            'keywords': [],
            'comments': [],
            'docstrings': []
        }
        
        if language == 'python':
            features.update(self._parse_python_code(code))
        else:
            features.update(self._parse_generic_code(code))
        
        return features
    
    def _parse_python_code(self, code: str) -> Dict[str, Any]:
        """Parse Python code using AST"""
        features = defaultdict(list)
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    features['functions'].append({
                        'name': node.name,
                        'args': [arg.arg for arg in node.args.args],
                        'lineno': node.lineno,
                        'docstring': ast.get_docstring(node)
                    })
                
                elif isinstance(node, ast.ClassDef):
                    features['classes'].append({
                        'name': node.name,
                        'bases': [self._ast_to_string(base) for base in node.bases],
                        'lineno': node.lineno,
                        'docstring': ast.get_docstring(node)
                    })
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        features['imports'].append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        features['imports'].append(f"{module}.{alias.name}")
                
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        features['method_calls'].append(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        features['method_calls'].append(node.func.attr)
                
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            features['variables'].append(target.id)
        
        except SyntaxError:
            # Fallback to regex parsing if AST fails
            features.update(self._parse_generic_code(code))
        
        return dict(features)
    
    def _parse_generic_code(self, code: str) -> Dict[str, Any]:
        """Parse code using regex patterns"""
        import re
        
        features = defaultdict(list)
        lines = code.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Extract function definitions
            func_match = re.search(r'(?:def|function|func)\s+(\w+)', line)
            if func_match:
                features['functions'].append({'name': func_match.group(1)})
            
            # Extract class definitions  
            class_match = re.search(r'class\s+(\w+)', line)
            if class_match:
                features['classes'].append({'name': class_match.group(1)})
            
            # Extract import statements
            import_match = re.search(r'(?:import|require|include)\s+([\'"]?[\w./]+[\'"]?)', line)
            if import_match:
                features['imports'].append(import_match.group(1).strip('\'"'))
            
            # Extract comments
            if line.startswith('#') or line.startswith('//'):
                features['comments'].append(line)
        
        return dict(features)
    
    def _ast_to_string(self, node) -> str:
        """Convert AST node to string"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._ast_to_string(node.value)}.{node.attr}"
        else:
            return str(node)

class SemanticCodeEmbedding:
    """Semantic embedding model optimized for code"""
    
    def __init__(self, embedding_dim: int = 256):
        self.embedding_dim = embedding_dim
        self.tokenizer = CodeTokenizer()
        
        # Vocabulary mappings
        self.token_to_idx = {}
        self.idx_to_token = {}
        self.embeddings = None
        
        # Feature weights for different code elements
        self.feature_weights = {
            'functions': 2.0,
            'classes': 2.0,
            'imports': 1.5,
            'method_calls': 1.2,
            'variables': 1.0,
            'keywords': 0.8,
            'comments': 0.5
        }
    
    def build_vocabulary(self, code_documents: List[Dict[str, str]]) -> None:
        """Build vocabulary from code documents"""
        all_tokens = set()
        
        for doc in code_documents:
            content = doc.get('content', '')
            language = self._detect_language(doc.get('path', ''))
            
            features = self.tokenizer.extract_code_features(content, language)
            
            # Add all extracted features as tokens
            for feature_type, items in features.items():
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            all_tokens.add(item.get('name', ''))
                        else:
                            all_tokens.add(str(item))
                else:
                    all_tokens.add(str(items))
            
            # Add basic word tokens
            words = content.lower().split()
            all_tokens.update(words)
        
        # Filter and create vocabulary
        filtered_tokens = [token for token in all_tokens if token and len(token) > 1]
        
        # Special tokens
        self.token_to_idx = {'<UNK>': 0, '<PAD>': 1, '<CODE>': 2}
        self.idx_to_token = {0: '<UNK>', 1: '<PAD>', 2: '<CODE>'}
        
        for i, token in enumerate(sorted(filtered_tokens)):
            idx = i + 3
            self.token_to_idx[token] = idx
            self.idx_to_token[idx] = token
        
        # Initialize embeddings with better initialization for code
        np.random.seed(42)
        vocab_size = len(self.token_to_idx)
        
        # Xavier initialization
        limit = np.sqrt(6.0 / (vocab_size + self.embedding_dim))
        self.embeddings = np.random.uniform(-limit, limit, (vocab_size, self.embedding_dim))
        
        # Special handling for code-related tokens
        self._enhance_code_embeddings()
    
    def _detect_language(self, filepath: str) -> str:
        """Detect programming language from file extension"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust'
        }
        
        for ext, lang in extension_map.items():
            if filepath.endswith(ext):
                return lang
        
        return 'generic'
    
    def _enhance_code_embeddings(self):
        """Enhance embeddings for code-specific tokens"""
        # Group similar tokens together in embedding space
        function_keywords = ['def', 'function', 'func', 'method']
        class_keywords = ['class', 'struct', 'interface']
        
        # Make similar tokens have similar embeddings
        for keyword_group in [function_keywords, class_keywords]:
            if len(keyword_group) > 1:
                indices = [self.token_to_idx.get(kw) for kw in keyword_group if kw in self.token_to_idx]
                if len(indices) > 1:
                    # Average the embeddings
                    avg_embedding = np.mean([self.embeddings[idx] for idx in indices], axis=0)
                    for idx in indices:
                        self.embeddings[idx] = avg_embedding + np.random.normal(0, 0.01, self.embedding_dim)
    
    def encode_document(self, content: str, filepath: str = '') -> np.ndarray:
        """Encode document to embedding vector"""
        language = self._detect_language(filepath)
        features = self.tokenizer.extract_code_features(content, language)
        
        # Create weighted feature vectors
        feature_vectors = []
        
        for feature_type, items in features.items():
            weight = self.feature_weights.get(feature_type, 1.0)
            
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        token = item.get('name', '')
                    else:
                        token = str(item)
                    
                    if token in self.token_to_idx:
                        idx = self.token_to_idx[token]
                        feature_vectors.append(self.embeddings[idx] * weight)
            
        # Add basic token embeddings with lower weight
        words = content.lower().split()
        for word in words:
            if word in self.token_to_idx:
                idx = self.token_to_idx[word]
                feature_vectors.append(self.embeddings[idx] * 0.5)
        
        if not feature_vectors:
            return np.zeros(self.embedding_dim)
        
        # Return mean of all feature vectors
        return np.mean(feature_vectors, axis=0)
    
    def compute_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute enhanced similarity for code vectors"""
        # Standard cosine similarity
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        cosine_sim = np.dot(vec1, vec2) / (norm1 * norm2)
        
        # Apply sigmoid to make similarities more discriminative
        return 1 / (1 + np.exp(-5 * (cosine_sim - 0.5)))

class OptimizedCodeSearchPipeline:
    """Optimized search pipeline for code documents"""
    
    def __init__(self, embedding_dim: int = 256):
        self.embedding_model = SemanticCodeEmbedding(embedding_dim)
        self.document_vectors = {}
        self.document_metadata = {}
        self.indexed = False
    
    def index_code_documents(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """Index code documents with optimized embeddings"""
        print(f"Building vocabulary from {len(documents)} documents...")
        self.embedding_model.build_vocabulary(documents)
        
        print("Generating document embeddings...")
        for doc in documents:
            doc_id = doc['id']
            content = doc['content']
            filepath = doc.get('path', '')
            
            # Generate embedding
            vector = self.embedding_model.encode_document(content, filepath)
            self.document_vectors[doc_id] = vector
            
            # Store metadata
            self.document_metadata[doc_id] = {
                'path': filepath,
                'language': self.embedding_model._detect_language(filepath),
                'size': len(content),
                'features': self.embedding_model.tokenizer.extract_code_features(content)
            }
        
        self.indexed = True
        
        return {
            'indexed_documents': len(documents),
            'vocabulary_size': len(self.embedding_model.token_to_idx),
            'embedding_dimension': self.embedding_model.embedding_dim
        }
    
    def search(self, query: str, top_k: int = 5, language_filter: str = None) -> List[Dict[str, Any]]:
        """Search for similar code documents"""
        if not self.indexed:
            raise ValueError("Documents not indexed")
        
        # Generate query embedding
        query_vector = self.embedding_model.encode_document(query)
        
        # Compute similarities
        similarities = []
        for doc_id, doc_vector in self.document_vectors.items():
            metadata = self.document_metadata[doc_id]
            
            # Apply language filter if specified
            if language_filter and metadata['language'] != language_filter:
                continue
            
            similarity = self.embedding_model.compute_similarity(query_vector, doc_vector)
            similarities.append((doc_id, similarity, metadata))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Format results
        results = []
        for doc_id, similarity, metadata in similarities[:top_k]:
            results.append({
                'document_id': doc_id,
                'similarity_score': float(similarity),
                'path': metadata['path'],
                'language': metadata['language'],
                'features': metadata['features']
            })
        
        return results
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the search pipeline"""
        if not self.indexed:
            return {"error": "Not indexed"}
        
        # Calculate some basic metrics
        vector_norms = [np.linalg.norm(vec) for vec in self.document_vectors.values()]
        
        return {
            'total_documents': len(self.document_vectors),
            'avg_vector_norm': float(np.mean(vector_norms)),
            'std_vector_norm': float(np.std(vector_norms)),
            'vocabulary_size': len(self.embedding_model.token_to_idx),
            'languages': list(set(meta['language'] for meta in self.document_metadata.values()))
        }

# Example usage and benchmarking
if __name__ == "__main__":
    import time
    
    # Sample code documents
    sample_docs = [
        {
            'id': 'doc1',
            'path': 'utils.py',
            'content': '''
def calculate_similarity(vec1, vec2):
    """Calculate cosine similarity between vectors"""
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return np.dot(vec1, vec2) / (norm1 * norm2)

class VectorStore:
    def __init__(self):
        self.vectors = {}
    
    def add_vector(self, key, vector):
        self.vectors[key] = vector
'''
        },
        {
            'id': 'doc2',
            'path': 'search.py',
            'content': '''
import numpy as np
from typing import List, Dict

def search_documents(query_vector, document_vectors, top_k=5):
    """Search for most similar documents"""
    similarities = []
    for doc_id, doc_vector in document_vectors.items():
        sim = calculate_similarity(query_vector, doc_vector)
        similarities.append((doc_id, sim))
    
    return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]
'''
        }
    ]
    
    # Initialize and test pipeline
    pipeline = OptimizedCodeSearchPipeline()
    
    start_time = time.time()
    stats = pipeline.index_code_documents(sample_docs)
    index_time = time.time() - start_time
    
    print(f"Indexing completed in {index_time:.3f}s")
    print(f"Stats: {stats}")
    
    # Test search
    search_queries = [
        "calculate similarity between vectors",
        "search documents by similarity",
        "numpy vector operations"
    ]
    
    for query in search_queries:
        start_time = time.time()
        results = pipeline.search(query, top_k=2)
        search_time = time.time() - start_time
        
        print(f"\nQuery: {query}")
        print(f"Search time: {search_time:.3f}s")
        for result in results:
            print(f"  {result['document_id']}: {result['similarity_score']:.3f}")
    
    # Performance metrics
    metrics = pipeline.get_performance_metrics()
    print(f"\nPerformance metrics: {metrics}")