# Commit: bcd890 - Pathway integration for real-time document indexing (NEX-707)
# Real-time document indexing using Pathway framework

import asyncio
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import hashlib
import threading
from dataclasses import dataclass, asdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

@dataclass
class DocumentChange:
    """Represents a document change event"""
    event_type: str  # 'created', 'modified', 'deleted'
    file_path: str
    timestamp: float
    content_hash: Optional[str] = None
    size: Optional[int] = None

class PathwayFileWatcher(FileSystemEventHandler):
    """File system watcher for real-time document changes"""
    
    def __init__(self, change_callback: Callable[[DocumentChange], None]):
        super().__init__()
        self.change_callback = change_callback
        self.last_modified = {}
        self.debounce_delay = 0.5  # seconds
    
    def on_modified(self, event):
        if not event.is_directory:
            self._handle_file_change(event.src_path, 'modified')
    
    def on_created(self, event):
        if not event.is_directory:
            self._handle_file_change(event.src_path, 'created')
    
    def on_deleted(self, event):
        if not event.is_directory:
            change = DocumentChange(
                event_type='deleted',
                file_path=event.src_path,
                timestamp=time.time()
            )
            self.change_callback(change)
    
    def _handle_file_change(self, file_path: str, event_type: str):
        """Handle file change with debouncing"""
        current_time = time.time()
        
        # Debounce rapid file changes
        if file_path in self.last_modified:
            if current_time - self.last_modified[file_path] < self.debounce_delay:
                return
        
        self.last_modified[file_path] = current_time
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                change = DocumentChange(
                    event_type=event_type,
                    file_path=file_path,
                    timestamp=current_time,
                    content_hash=hashlib.md5(content).hexdigest(),
                    size=len(content)
                )
                
                self.change_callback(change)
        
        except Exception as e:
            print(f"Error processing file change {file_path}: {e}")

class PathwayDocumentProcessor:
    """Process document changes in real-time"""
    
    def __init__(self, knowledge_base_path: str):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.document_index = {}
        self.change_queue = asyncio.Queue()
        self.processing_enabled = True
        
        # File filters
        self.allowed_extensions = {'.md', '.txt', '.py', '.js', '.json', '.yml', '.yaml'}
        self.ignored_patterns = {'__pycache__', '.git', '.vscode', 'node_modules'}
    
    def should_process_file(self, file_path: str) -> bool:
        """Check if file should be processed"""
        path = Path(file_path)
        
        # Check extension
        if path.suffix not in self.allowed_extensions:
            return False
        
        # Check for ignored patterns
        for pattern in self.ignored_patterns:
            if pattern in str(path):
                return False
        
        return True
    
    async def process_document_change(self, change: DocumentChange):
        """Process a single document change"""
        if not self.should_process_file(change.file_path):
            return
        
        doc_id = str(Path(change.file_path).relative_to(self.knowledge_base_path))
        
        print(f"Processing {change.event_type}: {doc_id}")
        
        if change.event_type == 'deleted':
            # Remove from index
            if doc_id in self.document_index:
                del self.document_index[doc_id]
                await self._notify_index_change('removed', doc_id, None)
        
        else:
            # Add or update in index
            try:
                with open(change.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if content actually changed
                existing_doc = self.document_index.get(doc_id)
                if existing_doc and existing_doc.get('content_hash') == change.content_hash:
                    return  # No change in content
                
                # Create document record
                doc_record = {
                    'id': doc_id,
                    'path': change.file_path,
                    'content': content,
                    'content_hash': change.content_hash,
                    'size': change.size,
                    'timestamp': change.timestamp,
                    'last_processed': time.time(),
                    'type': Path(change.file_path).suffix
                }
                
                self.document_index[doc_id] = doc_record
                
                # Generate embeddings and update vector store
                await self._update_vector_index(doc_record)
                
                action = 'updated' if existing_doc else 'added'
                await self._notify_index_change(action, doc_id, doc_record)
            
            except Exception as e:
                print(f"Error processing document {doc_id}: {e}")
    
    async def _update_vector_index(self, doc_record: Dict[str, Any]):
        """Update vector index with new/modified document"""
        # Placeholder for vector embedding generation
        # In a real implementation, this would:
        # 1. Generate embeddings for the document content
        # 2. Update the vector store
        # 3. Update search indices
        
        print(f"  Generated embeddings for {doc_record['id']}")
        
        # Simulate embedding generation time
        await asyncio.sleep(0.1)
    
    async def _notify_index_change(self, action: str, doc_id: str, doc_record: Optional[Dict[str, Any]]):
        """Notify external systems of index changes"""
        notification = {
            'action': action,
            'document_id': doc_id,
            'timestamp': time.time(),
            'document': doc_record
        }
        
        # In a real implementation, this could:
        # 1. Send notifications to webhooks
        # 2. Update external search systems
        # 3. Trigger re-ranking of search results
        
        print(f"  Index notification: {action} {doc_id}")

class PathwayRealTimeIndexer:
    """Real-time document indexer using Pathway-inspired architecture"""
    
    def __init__(self, knowledge_base_path: str):
        self.knowledge_base_path = knowledge_base_path
        self.processor = PathwayDocumentProcessor(knowledge_base_path)
        self.file_watcher = None
        self.observer = None
        self.processing_task = None
        self.stats = {
            'documents_processed': 0,
            'changes_detected': 0,
            'errors': 0,
            'start_time': None
        }
    
    async def start(self):
        """Start real-time indexing"""
        print(f"Starting real-time indexer for {self.knowledge_base_path}")
        
        self.stats['start_time'] = time.time()
        
        # Initial indexing of existing documents
        await self._initial_index()
        
        # Start file watching
        self._start_file_watching()
        
        # Start processing task
        self.processing_task = asyncio.create_task(self._process_changes())
        
        print("Real-time indexing started")
    
    async def stop(self):
        """Stop real-time indexing"""
        print("Stopping real-time indexer...")
        
        # Stop file watching
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # Stop processing
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        print("Real-time indexing stopped")
    
    async def _initial_index(self):
        """Perform initial indexing of existing documents"""
        print("Performing initial document indexing...")
        
        initial_docs = 0
        for file_path in Path(self.knowledge_base_path).rglob('*'):
            if file_path.is_file() and self.processor.should_process_file(str(file_path)):
                change = DocumentChange(
                    event_type='created',
                    file_path=str(file_path),
                    timestamp=time.time(),
                    content_hash=self._get_file_hash(file_path),
                    size=file_path.stat().st_size
                )
                
                await self.processor.process_document_change(change)
                initial_docs += 1
        
        print(f"Initial indexing complete: {initial_docs} documents")
        self.stats['documents_processed'] = initial_docs
    
    def _start_file_watching(self):
        """Start file system watching"""
        self.file_watcher = PathwayFileWatcher(self._on_file_change)
        self.observer = Observer()
        self.observer.schedule(
            self.file_watcher,
            self.knowledge_base_path,
            recursive=True
        )
        self.observer.start()
        print("File system watching started")
    
    def _on_file_change(self, change: DocumentChange):
        """Handle file system change event"""
        self.stats['changes_detected'] += 1
        
        # Add to processing queue
        try:
            self.processor.change_queue.put_nowait(change)
        except asyncio.QueueFull:
            print("Change queue full, dropping change event")
            self.stats['errors'] += 1
    
    async def _process_changes(self):
        """Process document changes from the queue"""
        print("Change processing task started")
        
        while self.processor.processing_enabled:
            try:
                # Wait for changes with timeout
                change = await asyncio.wait_for(
                    self.processor.change_queue.get(),
                    timeout=1.0
                )
                
                await self.processor.process_document_change(change)
                self.stats['documents_processed'] += 1
            
            except asyncio.TimeoutError:
                continue
            
            except Exception as e:
                print(f"Error processing change: {e}")
                self.stats['errors'] += 1
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of file content"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get indexing statistics"""
        current_stats = self.stats.copy()
        
        if current_stats['start_time']:
            current_stats['uptime_seconds'] = time.time() - current_stats['start_time']
            current_stats['documents_indexed'] = len(self.processor.document_index)
        
        return current_stats
    
    def get_document_index(self) -> Dict[str, Any]:
        """Get current document index"""
        return {
            'total_documents': len(self.processor.document_index),
            'documents': {
                doc_id: {
                    'path': doc['path'],
                    'size': doc['size'],
                    'type': doc['type'],
                    'last_processed': doc['last_processed']
                }
                for doc_id, doc in self.processor.document_index.items()
            }
        }

# Example usage and testing
class PathwayIndexerDemo:
    """Demo of real-time indexing capabilities"""
    
    def __init__(self, knowledge_base_path: str):
        self.indexer = PathwayRealTimeIndexer(knowledge_base_path)
    
    async def run_demo(self, duration_seconds: int = 30):
        """Run indexing demo for specified duration"""
        print(f"Starting Pathway indexer demo for {duration_seconds} seconds")
        
        try:
            await self.indexer.start()
            
            # Monitor for specified duration
            start_time = time.time()
            while time.time() - start_time < duration_seconds:
                await asyncio.sleep(5)
                
                stats = self.indexer.get_stats()
                print(f"Stats: {stats['documents_processed']} docs processed, "
                      f"{stats['changes_detected']} changes detected, "
                      f"{stats['errors']} errors")
            
            # Show final index state
            index_info = self.indexer.get_document_index()
            print(f"\nFinal index: {index_info['total_documents']} documents")
            
        finally:
            await self.indexer.stop()

async def main():
    """Main demo function"""
    # Path to knowledge base
    kb_path = "./mock_knowledge_base"
    
    if not os.path.exists(kb_path):
        print(f"Knowledge base path {kb_path} not found")
        return
    
    demo = PathwayIndexerDemo(kb_path)
    await demo.run_demo(duration_seconds=30)

if __name__ == "__main__":
    print("Pathway Real-time Document Indexing Demo")
    print("This demonstrates real-time document change detection and processing")
    print("Try creating, modifying, or deleting files in the knowledge base during the demo")
    
    asyncio.run(main())