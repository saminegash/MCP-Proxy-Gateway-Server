# Task API Specification

This document provides the complete API specification for the Task Management service in the NexusAI platform.

## Base URL
```
https://api.nexusai.com/v1/tasks
```

## Authentication
All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Rate Limits
- Standard users: 100 requests per minute
- Premium users: 500 requests per minute
- Admin users: 1000 requests per minute

## Data Models

### Task Object
```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "status": "todo|in_progress|review|done|cancelled",
  "priority": "low|medium|high|critical",
  "assignee_id": "string|null",
  "reporter_id": "string",
  "project_id": "string",
  "created_at": "2024-01-20T09:15:00Z",
  "updated_at": "2024-01-25T14:20:00Z", 
  "due_date": "2024-02-01T00:00:00Z|null",
  "estimated_hours": "number|null",
  "actual_hours": "number|null",
  "labels": ["string"],
  "dependencies": ["string"],
  "attachments": [
    {
      "id": "string",
      "filename": "string",
      "url": "string",
      "size": "number"
    }
  ],
  "comments": [
    {
      "id": "string",
      "author_id": "string",
      "content": "string",
      "created_at": "2024-01-20T09:15:00Z"
    }
  ]
}
```

### User Object
```json
{
  "id": "string",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "avatar_url": "string|null",
  "role": "developer|designer|manager|admin",
  "active": "boolean"
}
```

### Project Object
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "status": "active|archived|completed",
  "owner_id": "string",
  "created_at": "2024-01-20T09:15:00Z"
}
```

## Endpoints

### Tasks

#### GET /tasks
Retrieve a list of tasks.

**Query Parameters:**
- `status` (optional): Filter by status
- `assignee_id` (optional): Filter by assignee
- `project_id` (optional): Filter by project
- `priority` (optional): Filter by priority
- `labels` (optional): Comma-separated list of labels
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)
- `sort` (optional): Sort field (created_at, updated_at, priority, due_date)
- `order` (optional): Sort order (asc, desc, default: desc)

**Example Request:**
```bash
GET /tasks?status=in_progress&assignee_id=user_123&limit=10
```

**Response:**
```json
{
  "data": [
    {
      "id": "task_001",
      "title": "Implement user authentication",
      "status": "in_progress",
      "priority": "high",
      "assignee_id": "user_123",
      "created_at": "2024-01-20T09:15:00Z"
    }
  ],
  "pagination": {
    "total": 150,
    "limit": 10,
    "offset": 0,
    "has_more": true
  }
}
```

#### POST /tasks
Create a new task.

**Request Body:**
```json
{
  "title": "string (required)",
  "description": "string (optional)",
  "priority": "low|medium|high|critical (optional, default: medium)",
  "assignee_id": "string (optional)",
  "project_id": "string (required)",
  "due_date": "string (optional, ISO 8601)",
  "estimated_hours": "number (optional)",
  "labels": ["string"] (optional),
  "dependencies": ["string"] (optional)
}
```

**Response:**
```json
{
  "data": {
    "id": "task_001",
    "title": "Implement user authentication",
    "description": "Add OAuth 2.0 support",
    "status": "todo",
    "priority": "high",
    "assignee_id": "user_123",
    "reporter_id": "user_456", 
    "project_id": "proj_001",
    "created_at": "2024-01-20T09:15:00Z",
    "updated_at": "2024-01-20T09:15:00Z"
  }
}
```

#### GET /tasks/{task_id}
Retrieve a specific task.

**Path Parameters:**
- `task_id`: Task identifier

**Response:**
```json
{
  "data": {
    "id": "task_001",
    "title": "Implement user authentication",
    "description": "Add OAuth 2.0 support",
    "status": "in_progress",
    "priority": "high",
    "assignee_id": "user_123",
    "reporter_id": "user_456",
    "project_id": "proj_001",
    "created_at": "2024-01-20T09:15:00Z",
    "updated_at": "2024-01-25T14:20:00Z",
    "due_date": "2024-02-01T00:00:00Z",
    "estimated_hours": 8,
    "actual_hours": 3.5,
    "labels": ["authentication", "security"],
    "dependencies": ["task_002"],
    "attachments": [],
    "comments": []
  }
}
```

#### PUT /tasks/{task_id}
Update a task.

**Path Parameters:**
- `task_id`: Task identifier

**Request Body:** (all fields optional)
```json
{
  "title": "string",
  "description": "string", 
  "status": "todo|in_progress|review|done|cancelled",
  "priority": "low|medium|high|critical",
  "assignee_id": "string|null",
  "due_date": "string|null",
  "estimated_hours": "number|null",
  "actual_hours": "number|null",
  "labels": ["string"],
  "dependencies": ["string"]
}
```

**Response:**
```json
{
  "data": {
    "id": "task_001", 
    "title": "Implement user authentication",
    "status": "done",
    "updated_at": "2024-01-26T10:30:00Z"
  }
}
```

#### DELETE /tasks/{task_id}
Delete a task.

**Path Parameters:**
- `task_id`: Task identifier

**Response:**
```json
{
  "message": "Task deleted successfully"
}
```

### Comments

#### POST /tasks/{task_id}/comments
Add a comment to a task.

**Request Body:**
```json
{
  "content": "string (required)"
}
```

**Response:**
```json
{
  "data": {
    "id": "comment_001",
    "content": "Added authentication flow diagram",
    "author_id": "user_123",
    "created_at": "2024-01-26T10:30:00Z"
  }
}
```

#### GET /tasks/{task_id}/comments
Get comments for a task.

**Query Parameters:**
- `limit` (optional): Number of results (default: 20)
- `offset` (optional): Pagination offset

### Attachments

#### POST /tasks/{task_id}/attachments
Upload an attachment to a task.

**Request:** Multipart form data
- `file`: File to upload (max 10MB)
- `description`: Optional description

**Response:**
```json
{
  "data": {
    "id": "attachment_001",
    "filename": "auth_diagram.png",
    "url": "https://storage.nexusai.com/attachments/auth_diagram.png",
    "size": 245760
  }
}
```

#### DELETE /tasks/{task_id}/attachments/{attachment_id}
Delete an attachment.

### Search

#### GET /tasks/search
Search tasks by content.

**Query Parameters:**
- `q` (required): Search query
- `fields` (optional): Fields to search (title,description,comments)
- `project_id` (optional): Limit to specific project
- `limit` (optional): Number of results

**Example:**
```bash
GET /tasks/search?q=authentication&fields=title,description&limit=10
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "title",
        "message": "Title is required"
      }
    ]
  }
}
```

### Error Codes
- `VALIDATION_ERROR` (400): Invalid request parameters
- `UNAUTHORIZED` (401): Invalid or missing authentication
- `FORBIDDEN` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `CONFLICT` (409): Resource conflict (e.g., duplicate)
- `RATE_LIMITED` (429): Rate limit exceeded
- `INTERNAL_ERROR` (500): Server error

## Webhooks

### Webhook Events
The API supports webhooks for real-time notifications:

- `task.created`: New task created
- `task.updated`: Task updated
- `task.deleted`: Task deleted
- `task.assigned`: Task assigned to user
- `task.completed`: Task marked as complete

### Webhook Payload
```json
{
  "event": "task.updated",
  "timestamp": "2024-01-26T10:30:00Z",
  "data": {
    "task": {
      "id": "task_001",
      "title": "Implement user authentication"
    },
    "changes": {
      "status": {
        "from": "in_progress",
        "to": "done"
      }
    },
    "actor": {
      "id": "user_123",
      "username": "johndoe"
    }
  }
}
```

## SDK Examples

### Python
```python
import requests

# Get tasks
response = requests.get(
    'https://api.nexusai.com/v1/tasks',
    headers={'Authorization': 'Bearer <token>'},
    params={'status': 'in_progress', 'limit': 10}
)
tasks = response.json()

# Create task
task_data = {
    'title': 'Implement feature X',
    'description': 'Add new functionality',
    'priority': 'high',
    'project_id': 'proj_001'
}
response = requests.post(
    'https://api.nexusai.com/v1/tasks',
    headers={'Authorization': 'Bearer <token>'},
    json=task_data
)
new_task = response.json()
```

### JavaScript
```javascript
// Using fetch API
const response = await fetch('https://api.nexusai.com/v1/tasks', {
  headers: {
    'Authorization': 'Bearer <token>',
    'Content-Type': 'application/json'
  }
});
const tasks = await response.json();

// Create task
const taskData = {
  title: 'Implement feature X',
  description: 'Add new functionality',
  priority: 'high',
  project_id: 'proj_001'
};

const createResponse = await fetch('https://api.nexusai.com/v1/tasks', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(taskData)
});
```

## Rate Limiting Headers

Responses include rate limiting information:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1642694400
```

## Changelog

### v1.2.0 (2024-01-26)
- Added search endpoint
- Added webhook support  
- Enhanced filtering options

### v1.1.0 (2024-01-15)
- Added attachment support
- Added comment functionality
- Improved error messages

### v1.0.0 (2024-01-01)
- Initial API release
- Basic CRUD operations
- Authentication support

## Related Documentation
- [MCP Server Design](mcp_server_design.md)
- [Authentication Guide](auth_design.md)
- [API Client Libraries](api_client_libraries.md)