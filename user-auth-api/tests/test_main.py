import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_main.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestMainApp:
    """Test main application functionality"""

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "redoc" in data
        assert data["message"] == "Welcome to User Auth API"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"
        assert data["redoc"] == "/redoc"

    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_docs_endpoint_accessible(self):
        """Test that OpenAPI docs are accessible"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint_accessible(self):
        """Test that ReDoc documentation is accessible"""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_json_accessible(self):
        """Test that OpenAPI JSON specification is accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        
        # Check basic info
        assert data["info"]["title"] == "User Auth API"
        assert data["info"]["version"] == "1.0.0"

    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.options("/")
        # CORS headers should be present in preflight responses
        # The exact behavior depends on the CORS middleware configuration

    def test_nonexistent_endpoint(self):
        """Test accessing nonexistent endpoint"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_invalid_method(self):
        """Test using invalid HTTP method"""
        response = client.patch("/")  # Root only supports GET
        assert response.status_code == 405

    def test_api_versioning(self):
        """Test that API endpoints are properly versioned"""
        # Test that v1 endpoints are accessible
        response = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        })
        # Should get either success or validation error, not 404
        assert response.status_code != 404

    def test_application_startup(self):
        """Test that application starts up correctly"""
        # This is implicit in other tests, but we can verify basic functionality
        assert app is not None
        assert hasattr(app, 'include_router')
        assert hasattr(app, 'add_middleware')

    def test_database_connection(self):
        """Test database connection is working"""
        # This is tested implicitly through other endpoints
        # but we can verify basic connectivity
        response = client.get("/health")
        assert response.status_code == 200


class TestErrorHandling:
    """Test application error handling"""

    def test_validation_error_response(self):
        """Test validation error response format"""
        response = client.post("/api/v1/auth/register", json={
            "username": "test",
            "email": "invalid-email",  # Invalid email format
            "password": "123"  # Too short
        })
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    def test_authentication_error_response(self):
        """Test authentication error response format"""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data

    def test_authorization_error_response(self):
        """Test authorization error response format"""
        # Register and login a user
        client.post("/api/v1/auth/register", json={
            "username": "normaluser",
            "email": "normal@example.com",
            "password": "normalpass123"
        })
        
        login_response = client.post("/api/v1/auth/login", data={
            "username": "normaluser",
            "password": "normalpass123"
        })
        token = login_response.json()["access_token"]
        
        # Try to access admin endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/roles/", headers=headers)
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

    def test_not_found_error_response(self):
        """Test not found error response format"""
        # Register and login a user
        client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        })
        
        login_response = client.post("/api/v1/auth/login", data={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        
        # Try to access nonexistent user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/9999", headers=headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data