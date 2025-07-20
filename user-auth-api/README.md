# User Auth API

A comprehensive FastAPI-based user authentication and authorization service with JWT tokens, role-based access control, and extensive API documentation.

## Features

- 🚀 **FastAPI Framework**: Modern, fast web framework for building APIs
- 🔐 **JWT Authentication**: Secure token-based authentication
- 👥 **Role-Based Access Control**: Fine-grained permission management
- 📚 **OpenAPI Documentation**: Auto-generated API docs with Swagger UI
- 🗄️ **SQLAlchemy ORM**: Database modeling and management
- 🔒 **Password Security**: Bcrypt hashing with salt
- ✅ **Comprehensive Testing**: Unit tests with pytest
- 🐳 **Docker Support**: Containerized deployment
- 📊 **Database Migrations**: Alembic for schema management

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL (for production) or SQLite (for development)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd user-auth-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python scripts/init_db.py
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

### Core Endpoints

#### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login user (form data) |
| POST | `/api/v1/auth/login/json` | Login user (JSON) |

#### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/me` | Get current user |
| PUT | `/api/v1/users/me` | Update current user |
| GET | `/api/v1/users/` | List users (admin/manager) |
| GET | `/api/v1/users/{id}` | Get user by ID |
| PUT | `/api/v1/users/{id}` | Update user (superuser) |
| DELETE | `/api/v1/users/{id}` | Delete user (superuser) |

#### Roles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/roles/` | List roles (admin/manager) |
| POST | `/api/v1/roles/` | Create role (superuser) |
| GET | `/api/v1/roles/{id}` | Get role by ID |

#### User-Role Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users/{user_id}/roles/{role_id}` | Assign role to user |
| DELETE | `/api/v1/users/{user_id}/roles/{role_id}` | Remove role from user |

## Usage Examples

### 1. Register a New User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123",
    "full_name": "John Doe"
  }'
```

### 2. Login and Get Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=johndoe&password=securepassword123"
```

### 3. Access Protected Endpoint

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 4. Update User Profile

```bash
curl -X PUT "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Updated Doe",
    "email": "john.updated@example.com"
  }'
```

## Database Schema

### Tables

- **users**: User accounts and profiles
- **roles**: Role definitions
- **permissions**: Permission definitions (future)
- **user_roles**: Many-to-many user-role relationships

### Entity Relationship

```
Users ←→ UserRoles ←→ Roles
                      ↓
                  RolePermissions ←→ Permissions
```

For detailed schema documentation, see [docs/database_schema.md](docs/database_schema.md).

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Test with coverage
pytest --cov=app --cov-report=html
```

### Test Files

- `tests/test_auth.py`: Authentication endpoints
- `tests/test_users.py`: User management endpoints
- `tests/test_roles.py`: Role management endpoints
- `tests/test_main.py`: Application and error handling tests
- `tests/conftest.py`: Test configuration and fixtures

## Development

### Environment Setup

1. **Development Environment**
   ```bash
   export DATABASE_URL="sqlite:///./dev.db"
   export SECRET_KEY="your-secret-key"
   export ENVIRONMENT="development"
   ```

2. **Run with Hot Reload**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Downgrade migrations
alembic downgrade -1
```

### Code Quality

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

## Deployment

### Docker Deployment

1. **Build Image**
   ```bash
   docker build -t user-auth-api .
   ```

2. **Run Container**
   ```bash
   docker run -p 8000:8000 -e DATABASE_URL="your-db-url" user-auth-api
   ```

3. **Docker Compose**
   ```bash
   docker-compose up -d
   ```

### Production Environment

1. **Environment Variables**
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost/dbname"
   export SECRET_KEY="your-secure-secret-key"
   export ENVIRONMENT="production"
   export ACCESS_TOKEN_EXPIRE_MINUTES=60
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./app.db` |
| `SECRET_KEY` | JWT secret key | Required |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `60` |
| `APP_NAME` | Application name | `User Auth API` |
| `ENVIRONMENT` | Environment (dev/prod) | `development` |

### Database Configuration

#### Development (SQLite)
```python
DATABASE_URL = "sqlite:///./dev.db"
```

#### Production (PostgreSQL)
```python
DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

## Security Features

### Password Security
- Bcrypt hashing with automatic salt generation
- Minimum password length validation
- Password complexity can be extended

### JWT Tokens
- Configurable expiration time
- Secure secret key requirement
- Bearer token authentication

### Role-Based Access Control
- Multiple roles per user
- Hierarchical permission system
- Protected endpoints with role validation

### Data Protection
- SQL injection prevention through ORM
- Input validation with Pydantic
- Proper error handling without data leakage

## API Reference

### Authentication Flow

1. **Register**: Create new user account
2. **Login**: Authenticate and receive JWT token
3. **Access**: Use token in Authorization header
4. **Refresh**: Re-login when token expires

### Response Formats

#### Success Response
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2023-01-01T00:00:00Z",
  "roles": []
}
```

#### Error Response
```json
{
  "detail": "Error message description"
}
```

#### Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Use type hints for better code clarity
- Add proper error handling

## Architecture

### Project Structure

```
user-auth-api/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection and session
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── crud.py              # Database operations
│   ├── auth.py              # Authentication utilities
│   ├── dependencies.py      # FastAPI dependencies
│   └── routers/
│       ├── auth.py          # Authentication endpoints
│       ├── users.py         # User management endpoints
│       └── roles.py         # Role management endpoints
├── tests/                   # Test files
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── alembic/                 # Database migrations
└── requirements.txt         # Python dependencies
```

### Technology Stack

- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Python SQL toolkit and ORM
- **Alembic**: Database migration tool
- **Pydantic**: Data validation using Python type hints
- **Passlib**: Password hashing library
- **PyJWT**: JSON Web Token implementation
- **Pytest**: Testing framework
- **Uvicorn**: ASGI server

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check DATABASE_URL environment variable
   - Ensure database server is running
   - Verify database credentials

2. **Token Validation Error**
   - Check SECRET_KEY configuration
   - Ensure token hasn't expired
   - Verify Authorization header format

3. **Permission Denied**
   - Check user roles and permissions
   - Ensure user is active
   - Verify endpoint authorization requirements

### Debug Mode

```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload --log-level debug
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Documentation: Check the `/docs` endpoint
- Issues: Open an issue on GitHub
- Email: support@example.com

## Changelog

### v1.0.0
- Initial release
- User registration and authentication
- Role-based access control
- Comprehensive API documentation
- Full test coverage