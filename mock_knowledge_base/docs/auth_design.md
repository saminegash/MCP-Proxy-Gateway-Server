# Authentication & Authorization Design

This document outlines the authentication and authorization architecture for the NexusAI platform, covering user authentication, agent authentication, and access control mechanisms.

## Overview

The authentication system provides secure access control for multiple types of entities:
- **Human Users**: Developers, managers, administrators
- **AI Agents**: Autonomous systems accessing APIs and services
- **External Systems**: Third-party integrations and webhooks

## Architecture Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client        │    │  Auth Gateway   │    │  Identity Store │
│                 │◄──►│                 │◄──►│                 │
│ - Users         │    │ - Authentication│    │ - User DB       │
│ - Agents        │    │ - Authorization │    │ - Agent Registry│
│ - External APIs │    │ - Token Mgmt    │    │ - Permissions   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                      ┌─────────────────┐
                      │  Resource APIs  │
                      │                 │
                      │ - Task API      │
                      │ - MCP Servers   │
                      │ - File System   │
                      └─────────────────┘
```

## Authentication Methods

### 1. Human User Authentication

#### Primary Methods
- **OAuth 2.0**: GitHub, Google, Microsoft integration
- **SAML 2.0**: Enterprise SSO integration
- **Local Credentials**: Username/password with MFA

#### OAuth 2.0 Implementation
```python
class OAuthProvider:
    def __init__(self, provider_name: str, config: Dict[str, str]):
        self.provider_name = provider_name
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.redirect_uri = config['redirect_uri']
        self.scope = config.get('scope', 'user:email')
    
    def get_authorization_url(self, state: str) -> str:
        """Generate OAuth authorization URL"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
            'state': state,
            'response_type': 'code'
        }
        
        base_url = self.get_authorization_endpoint()
        return f"{base_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.get_token_endpoint(),
                data=token_data
            ) as response:
                return await response.json()

# Provider configurations
OAUTH_PROVIDERS = {
    'github': {
        'client_id': os.getenv('GITHUB_CLIENT_ID'),
        'client_secret': os.getenv('GITHUB_CLIENT_SECRET'),
        'redirect_uri': 'https://nexusai.com/auth/github/callback',
        'scope': 'user:email,read:org'
    },
    'google': {
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'redirect_uri': 'https://nexusai.com/auth/google/callback',
        'scope': 'openid email profile'
    }
}
```

#### Multi-Factor Authentication
```python
class MFAManager:
    def __init__(self):
        self.totp = pyotp.TOTP
        
    def generate_secret(self, user_id: str) -> str:
        """Generate TOTP secret for user"""
        secret = pyotp.random_base32()
        
        # Store secret securely
        self.store_mfa_secret(user_id, secret)
        
        return secret
    
    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """Generate QR code for TOTP setup"""
        provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name="NexusAI"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for web display
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_totp(self, user_id: str, token: str) -> bool:
        """Verify TOTP token"""
        secret = self.get_mfa_secret(user_id)
        if not secret:
            return False
        
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
```

### 2. Agent Authentication

#### Client Credentials Flow
```python
class AgentAuthenticator:
    def __init__(self):
        self.token_store = TokenStore()
        self.agent_registry = AgentRegistry()
    
    async def authenticate_agent(self, client_id: str, client_secret: str, 
                               scopes: List[str]) -> Dict[str, Any]:
        """Authenticate agent using client credentials"""
        
        # Verify agent credentials
        agent = await self.agent_registry.get_agent(client_id)
        if not agent or not self.verify_secret(agent, client_secret):
            raise AuthenticationError("Invalid agent credentials")
        
        # Check requested scopes
        allowed_scopes = set(agent.allowed_scopes)
        requested_scopes = set(scopes)
        
        if not requested_scopes.issubset(allowed_scopes):
            raise AuthorizationError("Requested scopes not allowed")
        
        # Generate access token
        token_data = {
            'agent_id': agent.id,
            'agent_type': agent.type,
            'scopes': list(requested_scopes),
            'expires_in': 3600,  # 1 hour
            'issued_at': time.time()
        }
        
        access_token = self.generate_jwt_token(token_data)
        
        return {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': ' '.join(requested_scopes)
        }

# Agent registration
class AgentRegistry:
    async def register_agent(self, agent_data: Dict[str, Any]) -> Agent:
        """Register a new agent"""
        
        # Generate client credentials
        client_id = f"agent_{uuid.uuid4().hex[:16]}"
        client_secret = secrets.token_urlsafe(32)
        
        agent = Agent(
            id=client_id,
            name=agent_data['name'],
            type=agent_data['type'],
            description=agent_data.get('description', ''),
            client_secret_hash=bcrypt.hashpw(client_secret.encode(), bcrypt.gensalt()),
            allowed_scopes=agent_data.get('allowed_scopes', []),
            created_by=agent_data['created_by'],
            created_at=datetime.utcnow()
        )
        
        await self.store_agent(agent)
        
        # Return credentials (only time secret is visible)
        return {
            'client_id': client_id,
            'client_secret': client_secret,
            'agent': agent
        }
```

### 3. JWT Token Management

#### Token Structure
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "auth-key-2024-01"
  },
  "payload": {
    "iss": "https://auth.nexusai.com",
    "sub": "user_123",
    "aud": ["nexusai-api", "nexusai-agents"],
    "exp": 1706278800,
    "iat": 1706275200,
    "jti": "token_456",
    "scope": ["task:read", "task:write", "project:read"],
    "user_id": "user_123",
    "agent_id": null,
    "role": "developer",
    "permissions": {
      "projects": ["proj_001", "proj_002"],
      "teams": ["team_alpha"]
    }
  }
}
```

#### Token Generation
```python
class JWTManager:
    def __init__(self, private_key: str, public_key: str):
        self.private_key = private_key
        self.public_key = public_key
        self.algorithm = 'RS256'
    
    def generate_token(self, payload: Dict[str, Any], 
                      expires_in: int = 3600) -> str:
        """Generate JWT token"""
        
        now = int(time.time())
        
        token_payload = {
            'iss': 'https://auth.nexusai.com',
            'iat': now,
            'exp': now + expires_in,
            'jti': str(uuid.uuid4()),
            **payload
        }
        
        return jwt.encode(
            token_payload,
            self.private_key,
            algorithm=self.algorithm,
            headers={'kid': 'auth-key-2024-01'}
        )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm],
                audience=['nexusai-api', 'nexusai-agents']
            )
            
            # Check if token is revoked
            if self.is_token_revoked(payload.get('jti')):
                raise jwt.InvalidTokenError("Token has been revoked")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
```

## Authorization Model

### Role-Based Access Control (RBAC)

#### Role Definitions
```python
class Role:
    def __init__(self, name: str, permissions: List[str], 
                 description: str = ""):
        self.name = name
        self.permissions = set(permissions)
        self.description = description

# Predefined roles
ROLES = {
    'admin': Role('admin', [
        'user:*', 'agent:*', 'project:*', 'team:*', 'system:*'
    ], 'Full system access'),
    
    'manager': Role('manager', [
        'project:read', 'project:write', 'project:delete',
        'team:read', 'team:write', 'user:read',
        'task:*', 'agent:read'
    ], 'Project and team management'),
    
    'developer': Role('developer', [
        'project:read', 'task:*', 'agent:read', 'agent:write',
        'file:read', 'file:write'
    ], 'Development and task management'),
    
    'viewer': Role('viewer', [
        'project:read', 'task:read', 'file:read'
    ], 'Read-only access'),
    
    'agent': Role('agent', [
        'task:read', 'task:write', 'file:read', 'mcp:invoke'
    ], 'AI agent access')
}
```

#### Permission Checking
```python
class AuthorizationChecker:
    def __init__(self):
        self.permission_cache = TTLCache(maxsize=1000, ttl=300)
    
    def check_permission(self, user_token: Dict[str, Any], 
                        required_permission: str,
                        resource_id: str = None) -> bool:
        """Check if user has required permission"""
        
        # Cache key
        cache_key = f"{user_token.get('jti')}:{required_permission}:{resource_id}"
        
        if cache_key in self.permission_cache:
            return self.permission_cache[cache_key]
        
        # Get user permissions
        user_permissions = self.get_user_permissions(user_token)
        
        # Check direct permission
        has_permission = self.has_permission(user_permissions, required_permission)
        
        # Check resource-specific permissions
        if resource_id and not has_permission:
            has_permission = self.check_resource_permission(
                user_token, required_permission, resource_id
            )
        
        # Cache result
        self.permission_cache[cache_key] = has_permission
        
        return has_permission
    
    def has_permission(self, user_permissions: Set[str], 
                      required_permission: str) -> bool:
        """Check if permission set includes required permission"""
        
        # Check exact match
        if required_permission in user_permissions:
            return True
        
        # Check wildcard permissions
        for permission in user_permissions:
            if permission.endswith('*'):
                prefix = permission[:-1]
                if required_permission.startswith(prefix):
                    return True
        
        return False
    
    def check_resource_permission(self, user_token: Dict[str, Any],
                                permission: str, resource_id: str) -> bool:
        """Check resource-specific permissions"""
        
        user_id = user_token.get('user_id')
        
        # Check project membership
        if permission.startswith('project:'):
            return self.is_project_member(user_id, resource_id)
        
        # Check team membership
        if permission.startswith('team:'):
            return self.is_team_member(user_id, resource_id)
        
        # Check task assignment
        if permission.startswith('task:'):
            return self.is_task_accessible(user_id, resource_id)
        
        return False
```

### Attribute-Based Access Control (ABAC)

#### Policy Engine
```python
class PolicyEngine:
    def __init__(self):
        self.policies = []
        self.load_policies()
    
    def evaluate_policy(self, subject: Dict[str, Any],
                       action: str, resource: Dict[str, Any],
                       environment: Dict[str, Any] = None) -> bool:
        """Evaluate access policy"""
        
        for policy in self.policies:
            if policy.applies_to(subject, action, resource):
                result = policy.evaluate(subject, action, resource, environment)
                
                if result == PolicyResult.DENY:
                    return False
                elif result == PolicyResult.ALLOW:
                    return True
                # INDETERMINATE continues to next policy
        
        # Default deny
        return False

class Policy:
    def __init__(self, name: str, conditions: List[Condition], 
                 effect: PolicyResult):
        self.name = name
        self.conditions = conditions
        self.effect = effect
    
    def evaluate(self, subject: Dict[str, Any], action: str,
                resource: Dict[str, Any], environment: Dict[str, Any]) -> PolicyResult:
        """Evaluate all conditions"""
        
        for condition in self.conditions:
            if not condition.evaluate(subject, action, resource, environment):
                return PolicyResult.INDETERMINATE
        
        return self.effect

# Example policies
TIME_BASED_ACCESS_POLICY = Policy(
    name="business_hours_access",
    conditions=[
        TimeCondition(start_hour=9, end_hour=17),
        DayOfWeekCondition(days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday'])
    ],
    effect=PolicyResult.ALLOW
)

SENSITIVE_DATA_POLICY = Policy(
    name="sensitive_data_access",
    conditions=[
        ResourceAttributeCondition('classification', 'sensitive'),
        SubjectAttributeCondition('clearance_level', 'high'),
        MFACondition(required=True)
    ],
    effect=PolicyResult.ALLOW
)
```

## Security Measures

### Password Security
```python
class PasswordManager:
    def __init__(self):
        self.min_length = 12
        self.require_complexity = True
        self.bcrypt_rounds = 12
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        if not self.validate_password(password):
            raise ValueError("Password does not meet requirements")
        
        salt = bcrypt.gensalt(rounds=self.bcrypt_rounds)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def validate_password(self, password: str) -> bool:
        """Validate password against policy"""
        if len(password) < self.min_length:
            return False
        
        if self.require_complexity:
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
            
            if not all([has_upper, has_lower, has_digit, has_special]):
                return False
        
        return True
```

### Rate Limiting
```python
class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.limits = {
            'login': {'requests': 5, 'window': 900},  # 5 attempts per 15 minutes
            'api_call': {'requests': 100, 'window': 60},  # 100 calls per minute
            'password_reset': {'requests': 3, 'window': 3600}  # 3 resets per hour
        }
    
    async def check_rate_limit(self, key: str, action: str, 
                             identifier: str) -> bool:
        """Check if action is within rate limits"""
        
        if action not in self.limits:
            return True
        
        limit_config = self.limits[action]
        rate_key = f"rate_limit:{action}:{identifier}"
        
        # Get current count
        current = await self.redis.get(rate_key)
        if current is None:
            current = 0
        else:
            current = int(current)
        
        # Check limit
        if current >= limit_config['requests']:
            return False
        
        # Increment counter
        pipe = self.redis.pipeline()
        pipe.incr(rate_key)
        pipe.expire(rate_key, limit_config['window'])
        await pipe.execute()
        
        return True
```

### Session Management
```python
class SessionManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.session_timeout = 8 * 3600  # 8 hours
        
    async def create_session(self, user_id: str, 
                           additional_data: Dict[str, Any] = None) -> str:
        """Create new user session"""
        
        session_id = str(uuid.uuid4())
        session_data = {
            'user_id': user_id,
            'created_at': time.time(),
            'last_accessed': time.time(),
            'ip_address': additional_data.get('ip_address'),
            'user_agent': additional_data.get('user_agent')
        }
        
        if additional_data:
            session_data.update(additional_data)
        
        # Store session
        await self.redis.setex(
            f"session:{session_id}",
            self.session_timeout,
            json.dumps(session_data)
        )
        
        return session_id
    
    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session data"""
        session_data = await self.redis.get(f"session:{session_id}")
        
        if not session_data:
            return None
        
        data = json.loads(session_data)
        
        # Update last accessed time
        data['last_accessed'] = time.time()
        await self.redis.setex(
            f"session:{session_id}",
            self.session_timeout,
            json.dumps(data)
        )
        
        return data
    
    async def invalidate_session(self, session_id: str):
        """Invalidate session"""
        await self.redis.delete(f"session:{session_id}")
```

## API Authentication Middleware

### FastAPI Middleware
```python
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token from Authorization header"""
    
    try:
        token = credentials.credentials
        payload = jwt_manager.verify_token(token)
        
        # Check if user/agent is active
        if payload.get('user_id'):
            user = await user_service.get_user(payload['user_id'])
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is disabled"
                )
        
        elif payload.get('agent_id'):
            agent = await agent_service.get_agent(payload['agent_id'])
            if not agent or not agent.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Agent is disabled"
                )
        
        return payload
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

def require_permission(permission: str):
    """Decorator to require specific permission"""
    
    def decorator(func):
        async def wrapper(*args, token: dict = Depends(verify_token), **kwargs):
            if not auth_checker.check_permission(token, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission}"
                )
            return await func(*args, token=token, **kwargs)
        return wrapper
    return decorator

# Usage example
@app.post("/tasks")
@require_permission("task:write")
async def create_task(task_data: TaskCreate, token: dict = Depends(verify_token)):
    # Task creation logic
    pass
```

## Audit & Compliance

### Audit Logging
```python
class AuditLogger:
    def __init__(self, log_store):
        self.log_store = log_store
    
    async def log_authentication(self, user_id: str, success: bool,
                               method: str, ip_address: str):
        """Log authentication attempt"""
        
        event = {
            'event_type': 'authentication',
            'user_id': user_id,
            'success': success,
            'method': method,
            'ip_address': ip_address,
            'timestamp': datetime.utcnow(),
            'user_agent': request.headers.get('User-Agent')
        }
        
        await self.log_store.store_event(event)
    
    async def log_authorization(self, user_id: str, action: str,
                              resource: str, granted: bool):
        """Log authorization decision"""
        
        event = {
            'event_type': 'authorization',
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'granted': granted,
            'timestamp': datetime.utcnow()
        }
        
        await self.log_store.store_event(event)
```

## Related Documentation
- [RBAC Specification](rbac_spec.md)
- [Token Management](token_management.md)
- [Security Considerations](security_considerations.md)
- [OAuth Integration Guide](oauth_integration.md)