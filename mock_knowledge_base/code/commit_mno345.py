# Commit: mno345 - GitHub MCP server setup and configuration (NEX-202)
# GitHub MCP server integration for repository access

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import os
from datetime import datetime

@dataclass
class GitHubIssue:
    """GitHub issue model"""
    number: int
    title: str
    body: str
    state: str
    assignee: Optional[str]
    labels: List[str]
    created_at: str
    updated_at: str
    url: str

@dataclass
class GitHubPullRequest:
    """GitHub pull request model"""
    number: int
    title: str
    body: str
    state: str
    head_branch: str
    base_branch: str
    author: str
    created_at: str
    merged_at: Optional[str]
    url: str

class GitHubAPIClient:
    """GitHub API client for MCP server"""
    
    def __init__(self, token: Optional[str] = None, repo: str = "nexusai/agent-platform"):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.session = None
    
    async def __aenter__(self):
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'NexusAI-MCP-Server/1.0'
        }
        if self.token:
            headers['Authorization'] = f'token {self.token}'
        
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_issues(self, state: str = "open", limit: int = 10) -> List[GitHubIssue]:
        """Fetch repository issues"""
        url = f"{self.base_url}/repos/{self.repo}/issues"
        params = {
            'state': state,
            'per_page': limit,
            'sort': 'updated',
            'direction': 'desc'
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return [self._parse_issue(item) for item in data if 'pull_request' not in item]
            else:
                raise Exception(f"GitHub API error: {response.status}")
    
    async def get_issue(self, issue_number: int) -> Optional[GitHubIssue]:
        """Fetch specific issue"""
        url = f"{self.base_url}/repos/{self.repo}/issues/{issue_number}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return self._parse_issue(data)
            elif response.status == 404:
                return None
            else:
                raise Exception(f"GitHub API error: {response.status}")
    
    async def get_pull_requests(self, state: str = "open", limit: int = 10) -> List[GitHubPullRequest]:
        """Fetch repository pull requests"""
        url = f"{self.base_url}/repos/{self.repo}/pulls"
        params = {
            'state': state,
            'per_page': limit,
            'sort': 'updated',
            'direction': 'desc'
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return [self._parse_pull_request(item) for item in data]
            else:
                raise Exception(f"GitHub API error: {response.status}")
    
    async def get_pull_request(self, pr_number: int) -> Optional[GitHubPullRequest]:
        """Fetch specific pull request"""
        url = f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return self._parse_pull_request(data)
            elif response.status == 404:
                return None
            else:
                raise Exception(f"GitHub API error: {response.status}")
    
    def _parse_issue(self, data: Dict[str, Any]) -> GitHubIssue:
        """Parse GitHub issue API response"""
        return GitHubIssue(
            number=data['number'],
            title=data['title'],
            body=data['body'] or '',
            state=data['state'],
            assignee=data['assignee']['login'] if data['assignee'] else None,
            labels=[label['name'] for label in data['labels']],
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            url=data['html_url']
        )
    
    def _parse_pull_request(self, data: Dict[str, Any]) -> GitHubPullRequest:
        """Parse GitHub pull request API response"""
        return GitHubPullRequest(
            number=data['number'],
            title=data['title'],
            body=data['body'] or '',
            state=data['state'],
            head_branch=data['head']['ref'],
            base_branch=data['base']['ref'],
            author=data['user']['login'],
            created_at=data['created_at'],
            merged_at=data['merged_at'],
            url=data['html_url']
        )

class GitHubMCPServer:
    """MCP Server for GitHub integration"""
    
    def __init__(self, github_token: Optional[str] = None, repo: str = "nexusai/agent-platform"):
        self.github_token = github_token
        self.repo = repo
        self.methods = {
            "get_issues": self._get_issues,
            "get_issue": self._get_issue,
            "get_pull_requests": self._get_pull_requests,
            "get_pull_request": self._get_pull_request,
            "search_issues": self._search_issues
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
    
    async def _get_issues(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository issues"""
        state = params.get("state", "open")
        limit = params.get("limit", 10)
        
        async with GitHubAPIClient(self.github_token, self.repo) as client:
            issues = await client.get_issues(state, limit)
            return {
                "success": True,
                "issues": [self._serialize_issue(issue) for issue in issues]
            }
    
    async def _get_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific issue"""
        issue_number = params.get("issue_number")
        if not issue_number:
            return {"error": "issue_number parameter required"}
        
        async with GitHubAPIClient(self.github_token, self.repo) as client:
            issue = await client.get_issue(issue_number)
            if issue:
                return {
                    "success": True,
                    "issue": self._serialize_issue(issue)
                }
            else:
                return {"error": f"Issue #{issue_number} not found"}
    
    async def _get_pull_requests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository pull requests"""
        state = params.get("state", "open")
        limit = params.get("limit", 10)
        
        async with GitHubAPIClient(self.github_token, self.repo) as client:
            prs = await client.get_pull_requests(state, limit)
            return {
                "success": True,
                "pull_requests": [self._serialize_pr(pr) for pr in prs]
            }
    
    async def _get_pull_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific pull request"""
        pr_number = params.get("pr_number")
        if not pr_number:
            return {"error": "pr_number parameter required"}
        
        async with GitHubAPIClient(self.github_token, self.repo) as client:
            pr = await client.get_pull_request(pr_number)
            if pr:
                return {
                    "success": True,
                    "pull_request": self._serialize_pr(pr)
                }
            else:
                return {"error": f"Pull request #{pr_number} not found"}
    
    async def _search_issues(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search issues by keywords"""
        # Simplified search implementation
        query = params.get("query", "")
        state = params.get("state", "open")
        
        async with GitHubAPIClient(self.github_token, self.repo) as client:
            issues = await client.get_issues(state, 50)  # Get more for searching
            
            # Simple text matching
            matching_issues = []
            for issue in issues:
                if query.lower() in issue.title.lower() or query.lower() in issue.body.lower():
                    matching_issues.append(issue)
            
            return {
                "success": True,
                "query": query,
                "matches": len(matching_issues),
                "issues": [self._serialize_issue(issue) for issue in matching_issues[:10]]
            }
    
    def _serialize_issue(self, issue: GitHubIssue) -> Dict[str, Any]:
        """Serialize issue for JSON response"""
        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "state": issue.state,
            "assignee": issue.assignee,
            "labels": issue.labels,
            "created_at": issue.created_at,
            "updated_at": issue.updated_at,
            "url": issue.url
        }
    
    def _serialize_pr(self, pr: GitHubPullRequest) -> Dict[str, Any]:
        """Serialize pull request for JSON response"""
        return {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body,
            "state": pr.state,
            "head_branch": pr.head_branch,
            "base_branch": pr.base_branch,
            "author": pr.author,
            "created_at": pr.created_at,
            "merged_at": pr.merged_at,
            "url": pr.url
        }

# Server configuration and startup
async def start_github_mcp_server(host: str = "localhost", port: int = 8001):
    """Start the GitHub MCP server"""
    from aiohttp import web
    
    server = GitHubMCPServer()
    
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
    
    print(f"Starting GitHub MCP server on {host}:{port}")
    return await web._run_app(app, host=host, port=port)

if __name__ == "__main__":
    asyncio.run(start_github_mcp_server())