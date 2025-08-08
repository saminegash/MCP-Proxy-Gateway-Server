# Commit: def456 - Implement MCP server for Task API (NEX-456)
# MCP Server implementation for Task Management API

import asyncio
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

@dataclass
class Task:
    """Task model for the Task Management API"""
    id: str
    title: str
    description: str
    status: str
    assignee: Optional[str] = None
    priority: str = "Medium"
    created_at: str = ""
    updated_at: str = ""

class TaskAPI:
    """Internal Task Management API"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
    
    async def create_task(self, task_data: Dict[str, Any]) -> Task:
        """Create a new task"""
        task = Task(**task_data)
        self.tasks[task.id] = task
        return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    async def list_tasks(self, status: Optional[str] = None) -> List[Task]:
        """List all tasks, optionally filtered by status"""
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[Task]:
        """Update an existing task"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        return task

class MCPTaskServer:
    """MCP Server wrapper for Task API"""
    
    def __init__(self):
        self.task_api = TaskAPI()
        self.methods = {
            "create_task": self._create_task,
            "get_task": self._get_task,
            "list_tasks": self._list_tasks,
            "update_task": self._update_task
        }
    
    async def get_methods(self) -> List[str]:
        """Return available MCP methods"""
        return list(self.methods.keys())
    
    async def invoke_method(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke MCP method"""
        if method not in self.methods:
            raise ValueError(f"Unknown method: {method}")
        
        return await self.methods[method](params)
    
    async def _create_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        task = await self.task_api.create_task(params)
        return {"success": True, "task": asdict(task)}
    
    async def _get_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        task_id = params.get("task_id")
        task = await self.task_api.get_task(task_id)
        if task:
            return {"success": True, "task": asdict(task)}
        return {"success": False, "error": "Task not found"}
    
    async def _list_tasks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        status = params.get("status")
        tasks = await self.task_api.list_tasks(status)
        return {"success": True, "tasks": [asdict(t) for t in tasks]}
    
    async def _update_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        task_id = params.get("task_id")
        updates = params.get("updates", {})
        task = await self.task_api.update_task(task_id, updates)
        if task:
            return {"success": True, "task": asdict(task)}
        return {"success": False, "error": "Task not found"}

# Example usage
async def main():
    server = MCPTaskServer()
    
    # Create a task
    result = await server.invoke_method("create_task", {
        "id": "TASK-001",
        "title": "Setup CI/CD pipeline",
        "description": "Configure automated testing and deployment",
        "status": "To Do",
        "assignee": "devops_eng"
    })
    print("Created task:", result)

if __name__ == "__main__":
    asyncio.run(main())