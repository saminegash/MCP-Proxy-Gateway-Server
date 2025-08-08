# Commit: pqr678 - Filesystem MCP server implementation (NEX-303)
# Secure filesystem access MCP server for local code and documentation

import os
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import mimetypes
import hashlib
import json
from datetime import datetime

class FileSystemSecurity:
    """Security manager for filesystem access"""
    
    def __init__(self, allowed_paths: List[str], blocked_patterns: List[str] = None):
        self.allowed_paths = [Path(p).resolve() for p in allowed_paths]
        self.blocked_patterns = blocked_patterns or [
            '.*\\.env',
            '.*\\.key',
            '.*\\.pem',
            '.*\\.secret',
            '.*password.*',
            '.*token.*'
        ]
    
    def is_path_allowed(self, path: Union[str, Path]) -> bool:
        """Check if path access is allowed"""
        try:
            resolved_path = Path(path).resolve()
            
            # Check if path is within allowed directories
            for allowed_path in self.allowed_paths:
                try:
                    resolved_path.relative_to(allowed_path)
                    return True
                except ValueError:
                    continue
            
            return False
        except Exception:
            return False
    
    def is_file_blocked(self, path: Union[str, Path]) -> bool:
        """Check if file matches blocked patterns"""
        import re
        filename = str(path).lower()
        
        for pattern in self.blocked_patterns:
            if re.match(pattern, filename):
                return True
        
        return False

class FileSystemMCPServer:
    """MCP Server for secure filesystem access"""
    
    def __init__(self, allowed_paths: List[str] = None):
        if allowed_paths is None:
            allowed_paths = ["./", "./mock_knowledge_base", "./src", "./docs"]
        
        self.security = FileSystemSecurity(allowed_paths)
        self.methods = {
            "list_files": self._list_files,
            "read_file": self._read_file,
            "get_file_info": self._get_file_info,
            "search_files": self._search_files,
            "get_directory_tree": self._get_directory_tree
        }
    
    async def get_methods(self) -> List[str]:
        """Return available MCP methods"""
        return list(self.methods.keys())
    
    async def invoke_method(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke MCP method"""
        if method not in self.methods:
            return {"error": f"Unknown method: {method}"}
        
        try:
            return await self.methods[method](params)
        except Exception as e:
            return {"error": str(e)}
    
    async def _list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List files in directory"""
        path = params.get("path", ".")
        include_hidden = params.get("include_hidden", False)
        file_types = params.get("file_types", None)  # e.g., [".py", ".md"]
        
        if not self.security.is_path_allowed(path):
            return {"error": f"Access denied to path: {path}"}
        
        try:
            dir_path = Path(path)
            if not dir_path.exists():
                return {"error": f"Directory not found: {path}"}
            
            if not dir_path.is_dir():
                return {"error": f"Path is not a directory: {path}"}
            
            files = []
            directories = []
            
            for item in dir_path.iterdir():
                # Skip hidden files unless requested
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                # Check security
                if self.security.is_file_blocked(item):
                    continue
                
                if item.is_file():
                    # Filter by file types if specified
                    if file_types and item.suffix not in file_types:
                        continue
                    
                    file_info = {
                        "name": item.name,
                        "path": str(item),
                        "size": item.stat().st_size,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                        "type": item.suffix,
                        "mime_type": mimetypes.guess_type(str(item))[0]
                    }
                    files.append(file_info)
                
                elif item.is_dir():
                    dir_info = {
                        "name": item.name,
                        "path": str(item),
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    }
                    directories.append(dir_info)
            
            return {
                "success": True,
                "path": str(dir_path),
                "files": sorted(files, key=lambda x: x["name"]),
                "directories": sorted(directories, key=lambda x: x["name"]),
                "total_files": len(files),
                "total_directories": len(directories)
            }
        
        except Exception as e:
            return {"error": f"Failed to list directory: {str(e)}"}
    
    async def _read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read file contents"""
        path = params.get("path")
        if not path:
            return {"error": "path parameter required"}
        
        encoding = params.get("encoding", "utf-8")
        max_size = params.get("max_size", 1024 * 1024)  # 1MB default limit
        
        if not self.security.is_path_allowed(path):
            return {"error": f"Access denied to path: {path}"}
        
        if self.security.is_file_blocked(path):
            return {"error": f"File type blocked: {path}"}
        
        try:
            file_path = Path(path)
            
            if not file_path.exists():
                return {"error": f"File not found: {path}"}
            
            if not file_path.is_file():
                return {"error": f"Path is not a file: {path}"}
            
            file_size = file_path.stat().st_size
            if file_size > max_size:
                return {"error": f"File too large: {file_size} bytes (max: {max_size})"}
            
            # Try to read as text first
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                
                return {
                    "success": True,
                    "path": str(file_path),
                    "content": content,
                    "size": file_size,
                    "encoding": encoding,
                    "lines": len(content.splitlines()),
                    "hash": hashlib.md5(content.encode()).hexdigest()
                }
            
            except UnicodeDecodeError:
                # If text reading fails, try binary
                with open(file_path, 'rb') as f:
                    binary_content = f.read()
                
                return {
                    "success": True,
                    "path": str(file_path),
                    "content": None,
                    "binary_hash": hashlib.md5(binary_content).hexdigest(),
                    "size": file_size,
                    "encoding": "binary",
                    "error": "Binary file - content not readable as text"
                }
        
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}
    
    async def _get_file_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get file metadata"""
        path = params.get("path")
        if not path:
            return {"error": "path parameter required"}
        
        if not self.security.is_path_allowed(path):
            return {"error": f"Access denied to path: {path}"}
        
        try:
            file_path = Path(path)
            
            if not file_path.exists():
                return {"error": f"Path not found: {path}"}
            
            stat = file_path.stat()
            
            info = {
                "path": str(file_path),
                "name": file_path.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "is_file": file_path.is_file(),
                "is_directory": file_path.is_dir(),
                "permissions": oct(stat.st_mode)[-3:]
            }
            
            if file_path.is_file():
                info.update({
                    "extension": file_path.suffix,
                    "mime_type": mimetypes.guess_type(str(file_path))[0],
                    "is_text": self._is_text_file(file_path)
                })
            
            return {"success": True, "info": info}
        
        except Exception as e:
            return {"error": f"Failed to get file info: {str(e)}"}
    
    async def _search_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for files by name pattern"""
        query = params.get("query")
        path = params.get("path", ".")
        recursive = params.get("recursive", True)
        file_types = params.get("file_types", None)
        
        if not query:
            return {"error": "query parameter required"}
        
        if not self.security.is_path_allowed(path):
            return {"error": f"Access denied to path: {path}"}
        
        try:
            search_path = Path(path)
            if not search_path.exists():
                return {"error": f"Search path not found: {path}"}
            
            matches = []
            pattern = f"*{query}*"
            
            if recursive:
                search_pattern = search_path.rglob(pattern)
            else:
                search_pattern = search_path.glob(pattern)
            
            for match in search_pattern:
                if self.security.is_file_blocked(match):
                    continue
                
                if not self.security.is_path_allowed(match):
                    continue
                
                if file_types and match.is_file() and match.suffix not in file_types:
                    continue
                
                match_info = {
                    "path": str(match),
                    "name": match.name,
                    "type": "file" if match.is_file() else "directory",
                    "size": match.stat().st_size if match.is_file() else None,
                    "modified": datetime.fromtimestamp(match.stat().st_mtime).isoformat()
                }
                matches.append(match_info)
            
            return {
                "success": True,
                "query": query,
                "search_path": str(search_path),
                "recursive": recursive,
                "matches": sorted(matches, key=lambda x: x["name"]),
                "total_matches": len(matches)
            }
        
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    async def _get_directory_tree(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get directory tree structure"""
        path = params.get("path", ".")
        max_depth = params.get("max_depth", 3)
        include_files = params.get("include_files", True)
        
        if not self.security.is_path_allowed(path):
            return {"error": f"Access denied to path: {path}"}
        
        try:
            root_path = Path(path)
            if not root_path.exists():
                return {"error": f"Path not found: {path}"}
            
            def build_tree(current_path: Path, current_depth: int = 0) -> Dict[str, Any]:
                if current_depth >= max_depth:
                    return None
                
                node = {
                    "name": current_path.name,
                    "path": str(current_path),
                    "type": "directory" if current_path.is_dir() else "file"
                }
                
                if current_path.is_dir():
                    children = []
                    try:
                        for child in current_path.iterdir():
                            if child.name.startswith('.'):  # Skip hidden
                                continue
                            
                            if self.security.is_file_blocked(child):
                                continue
                            
                            if child.is_dir():
                                child_tree = build_tree(child, current_depth + 1)
                                if child_tree:
                                    children.append(child_tree)
                            elif include_files and child.is_file():
                                children.append({
                                    "name": child.name,
                                    "path": str(child),
                                    "type": "file",
                                    "size": child.stat().st_size,
                                    "extension": child.suffix
                                })
                    except PermissionError:
                        pass  # Skip directories we can't read
                    
                    node["children"] = children
                    node["child_count"] = len(children)
                
                return node
            
            tree = build_tree(root_path)
            
            return {
                "success": True,
                "tree": tree,
                "root_path": str(root_path),
                "max_depth": max_depth
            }
        
        except Exception as e:
            return {"error": f"Failed to build directory tree: {str(e)}"}
    
    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is likely a text file"""
        text_extensions = {
            '.txt', '.md', '.py', '.js', '.ts', '.json', '.xml', '.yml', '.yaml',
            '.html', '.css', '.sql', '.sh', '.bat', '.ini', '.cfg', '.conf'
        }
        
        if file_path.suffix.lower() in text_extensions:
            return True
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type.startswith('text/'):
            return True
        
        return False

# Example server startup
async def start_filesystem_mcp_server(host: str = "localhost", port: int = 8002):
    """Start the filesystem MCP server"""
    from aiohttp import web
    
    server = FileSystemMCPServer()
    
    async def handle_mcp_request(request):
        """Handle MCP requests"""
        try:
            data = await request.json()
            method = data.get('method')
            params = data.get('params', {})
            
            if method == 'get_methods':
                methods = await server.get_methods()
                response = {"success": True, "methods": methods}
            else:
                response = await server.invoke_method(method, params)
            
            return web.json_response(response)
        
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    app = web.Application()
    app.router.add_post('/mcp', handle_mcp_request)
    
    print(f"Starting Filesystem MCP server on {host}:{port}")
    return await web._run_app(app, host=host, port=port)

if __name__ == "__main__":
    asyncio.run(start_filesystem_mcp_server())