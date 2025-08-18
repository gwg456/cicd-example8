# 🔌 API Documentation

## Overview

The Prefect CI/CD application provides RESTful APIs for workflow management, health monitoring, and metrics collection.

## Base URL

```
Production: https://api.example.com
Staging: https://staging-api.example.com
Development: http://localhost:8000
```

## Authentication

### JWT Authentication

All API endpoints (except health checks) require JWT authentication.

#### Get Token
```http
POST /auth/token
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Use Token
```http
GET /api/flows
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Endpoints

### Health Checks

#### GET /health
Comprehensive health check of all system components.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "components": [
    {
      "name": "system",
      "status": "healthy",
      "message": "System resources OK",
      "details": {
        "cpu_percent": 45.2,
        "memory_percent": 62.5,
        "disk_percent": 35.8
      }
    },
    {
      "name": "prefect_api",
      "status": "healthy",
      "message": "Prefect API is reachable"
    },
    {
      "name": "database",
      "status": "healthy",
      "message": "Database connection OK"
    }
  ],
  "metrics": {
    "uptime_seconds": 86400,
    "process_uptime_seconds": 3600
  }
}
```

#### GET /health/live
Kubernetes liveness probe endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

#### GET /health/ready
Kubernetes readiness probe endpoint.

**Response:**
```json
{
  "status": "ready"
}
```

### Metrics

#### GET /metrics
Prometheus-formatted metrics endpoint.

**Response:**
```text
# HELP app_requests_total Total number of requests
# TYPE app_requests_total counter
app_requests_total{method="GET",endpoint="/api/flows",status="200"} 1234

# HELP app_request_duration_seconds Request duration in seconds
# TYPE app_request_duration_seconds histogram
app_request_duration_seconds_bucket{method="GET",endpoint="/api/flows",le="0.1"} 100
```

### Workflow Management

#### GET /api/flows
List all registered flows.

**Query Parameters:**
- `limit` (int): Maximum number of results (default: 100)
- `offset` (int): Pagination offset (default: 0)
- `status` (string): Filter by status (active/inactive)

**Response:**
```json
{
  "flows": [
    {
      "id": "flow-123",
      "name": "hello-flow",
      "description": "Production hello workflow",
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "tags": ["production", "automated"]
    }
  ],
  "total": 10,
  "limit": 100,
  "offset": 0
}
```

#### GET /api/flows/{flow_id}
Get details of a specific flow.

**Response:**
```json
{
  "id": "flow-123",
  "name": "hello-flow",
  "description": "Production hello workflow",
  "status": "active",
  "schedule": {
    "type": "interval",
    "interval": 3600
  },
  "parameters": {
    "name": {
      "type": "string",
      "default": "World",
      "required": false
    }
  },
  "tags": ["production", "automated"],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### POST /api/flows/{flow_id}/run
Trigger a flow run.

**Request Body:**
```json
{
  "parameters": {
    "name": "Alice",
    "include_processing": true
  },
  "tags": ["manual", "api-triggered"]
}
```

**Response:**
```json
{
  "run_id": "run-456",
  "flow_id": "flow-123",
  "status": "scheduled",
  "parameters": {
    "name": "Alice",
    "include_processing": true
  },
  "scheduled_at": "2024-01-01T00:00:00Z"
}
```

#### GET /api/runs/{run_id}
Get flow run status.

**Response:**
```json
{
  "run_id": "run-456",
  "flow_id": "flow-123",
  "status": "completed",
  "started_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:05:00Z",
  "duration": 300,
  "result": {
    "status": "success",
    "greeting": "Hello Alice!",
    "processed_data": {...}
  },
  "logs_url": "/api/runs/run-456/logs"
}
```

#### GET /api/runs/{run_id}/logs
Get flow run logs.

**Query Parameters:**
- `level` (string): Filter by log level (DEBUG/INFO/WARNING/ERROR)
- `limit` (int): Maximum number of log lines
- `follow` (bool): Stream logs in real-time

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "level": "INFO",
      "message": "Flow started",
      "correlation_id": "abc-123",
      "task": "hello_flow"
    }
  ]
}
```

### Deployment Management

#### POST /api/deployments
Create a new deployment.

**Request Body:**
```json
{
  "flow_name": "hello-flow",
  "deployment_name": "hello-production",
  "schedule": {
    "type": "cron",
    "cron": "0 9 * * *"
  },
  "tags": ["production"],
  "parameters": {
    "name": "Scheduled"
  }
}
```

**Response:**
```json
{
  "deployment_id": "deploy-789",
  "flow_name": "hello-flow",
  "deployment_name": "hello-production",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### PUT /api/deployments/{deployment_id}
Update deployment configuration.

**Request Body:**
```json
{
  "schedule": {
    "type": "interval",
    "interval": 7200
  },
  "parameters": {
    "name": "Updated"
  }
}
```

#### DELETE /api/deployments/{deployment_id}
Delete a deployment.

**Response:**
```json
{
  "message": "Deployment deleted successfully",
  "deployment_id": "deploy-789"
}
```

### Circuit Breaker Status

#### GET /api/circuit-breakers
Get status of all circuit breakers.

**Response:**
```json
{
  "circuit_breakers": [
    {
      "name": "prefect_api",
      "state": "closed",
      "total_calls": 1000,
      "total_successes": 995,
      "total_failures": 5,
      "success_rate": 99.5,
      "failure_count": 0,
      "circuit_open_count": 1,
      "last_failure_time": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /api/circuit-breakers/{name}/reset
Reset a circuit breaker.

**Response:**
```json
{
  "message": "Circuit breaker reset successfully",
  "name": "prefect_api",
  "state": "closed"
}
```

## Error Responses

### Error Format
```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional error context"
  },
  "correlation_id": "abc-123",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `CONFIGURATION_ERROR` | 500 | Server configuration issue |
| `CONNECTION_ERROR` | 503 | External service unavailable |
| `TIMEOUT_ERROR` | 504 | Operation timeout |
| `RATE_LIMIT_ERROR` | 429 | Rate limit exceeded |

## Rate Limiting

API requests are rate-limited to ensure fair usage:

- **Authenticated requests**: 1000 requests per hour
- **Unauthenticated requests**: 100 requests per hour

Rate limit information is included in response headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1704067200
```

## Webhooks

### Webhook Events

The application can send webhooks for the following events:

- `flow.started`: Flow execution started
- `flow.completed`: Flow execution completed
- `flow.failed`: Flow execution failed
- `deployment.created`: New deployment created
- `deployment.updated`: Deployment configuration updated
- `deployment.deleted`: Deployment removed

### Webhook Payload

```json
{
  "event": "flow.completed",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "flow_id": "flow-123",
    "run_id": "run-456",
    "status": "success",
    "duration": 300
  },
  "signature": "sha256=abcdef123456..."
}
```

### Webhook Security

Webhooks are signed using HMAC-SHA256. Verify the signature:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(
        f"sha256={expected}",
        signature
    )
```

## SDK Examples

### Python
```python
import requests

class PrefectCICDClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}"
        }
    
    def list_flows(self):
        response = requests.get(
            f"{self.base_url}/api/flows",
            headers=self.headers
        )
        return response.json()
    
    def run_flow(self, flow_id, parameters=None):
        response = requests.post(
            f"{self.base_url}/api/flows/{flow_id}/run",
            headers=self.headers,
            json={"parameters": parameters or {}}
        )
        return response.json()

# Usage
client = PrefectCICDClient(
    "https://api.example.com",
    "your-api-key"
)
flows = client.list_flows()
run = client.run_flow("flow-123", {"name": "API Test"})
```

### JavaScript
```javascript
class PrefectCICDClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    };
  }
  
  async listFlows() {
    const response = await fetch(
      `${this.baseUrl}/api/flows`,
      { headers: this.headers }
    );
    return response.json();
  }
  
  async runFlow(flowId, parameters = {}) {
    const response = await fetch(
      `${this.baseUrl}/api/flows/${flowId}/run`,
      {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({ parameters })
      }
    );
    return response.json();
  }
}

// Usage
const client = new PrefectCICDClient(
  'https://api.example.com',
  'your-api-key'
);
const flows = await client.listFlows();
const run = await client.runFlow('flow-123', { name: 'API Test' });
```

### cURL
```bash
# List flows
curl -X GET https://api.example.com/api/flows \
  -H "Authorization: Bearer your-api-key"

# Run flow
curl -X POST https://api.example.com/api/flows/flow-123/run \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"name": "API Test"}}'

# Get run status
curl -X GET https://api.example.com/api/runs/run-456 \
  -H "Authorization: Bearer your-api-key"
```