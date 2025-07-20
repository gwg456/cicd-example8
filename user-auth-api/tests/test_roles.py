import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_roles.db"
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


class TestRoles:
    """Test role management endpoints"""

    def setup_method(self):
        """Setup for each test method"""
        # Clear database
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # Create test user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        self.user_id = response.json()["id"]
        self.token = self._get_token("testuser", "testpass123")

    def _get_token(self, username: str, password: str) -> str:
        """Helper to get access token"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": username, "password": password}
        )
        return response.json()["access_token"]

    def _get_auth_headers(self, token: str) -> dict:
        """Helper to get authorization headers"""
        return {"Authorization": f"Bearer {token}"}

    def test_get_roles_unauthorized(self):
        """Test getting roles without authentication"""
        response = client.get("/api/v1/roles/")
        assert response.status_code == 401

    def test_get_roles_forbidden(self):
        """Test getting roles without admin/manager permissions"""
        headers = self._get_auth_headers(self.token)
        response = client.get("/api/v1/roles/", headers=headers)
        assert response.status_code == 403

    def test_create_role_unauthorized(self):
        """Test creating role without authentication"""
        role_data = {
            "name": "test_role",
            "description": "Test Role"
        }
        response = client.post("/api/v1/roles/", json=role_data)
        assert response.status_code == 401

    def test_create_role_forbidden(self):
        """Test creating role without superuser permissions"""
        headers = self._get_auth_headers(self.token)
        role_data = {
            "name": "test_role",
            "description": "Test Role"
        }
        response = client.post("/api/v1/roles/", json=role_data, headers=headers)
        assert response.status_code in [401, 403]

    def test_create_role_invalid_data(self):
        """Test creating role with invalid data"""
        headers = self._get_auth_headers(self.token)
        role_data = {
            "description": "Test Role without name"
        }
        response = client.post("/api/v1/roles/", json=role_data, headers=headers)
        assert response.status_code == 422  # Validation error

    def test_get_role_by_id_unauthorized(self):
        """Test getting role by ID without authentication"""
        response = client.get("/api/v1/roles/1")
        assert response.status_code == 401

    def test_get_role_by_id_forbidden(self):
        """Test getting role by ID without proper permissions"""
        headers = self._get_auth_headers(self.token)
        response = client.get("/api/v1/roles/1", headers=headers)
        assert response.status_code == 403

    def test_get_nonexistent_role(self):
        """Test getting nonexistent role"""
        headers = self._get_auth_headers(self.token)
        response = client.get("/api/v1/roles/9999", headers=headers)
        assert response.status_code in [403, 404]  # Forbidden or Not Found

    def test_role_data_validation(self):
        """Test role data validation"""
        headers = self._get_auth_headers(self.token)
        
        # Test empty name
        role_data = {"name": ""}
        response = client.post("/api/v1/roles/", json=role_data, headers=headers)
        assert response.status_code == 422

        # Test missing name
        role_data = {"description": "Role without name"}
        response = client.post("/api/v1/roles/", json=role_data, headers=headers)
        assert response.status_code == 422

    def test_role_response_structure(self):
        """Test that role responses have correct structure"""
        # This test would work if we had proper admin permissions
        # For now, it tests the expected error structure
        headers = self._get_auth_headers(self.token)
        response = client.get("/api/v1/roles/", headers=headers)
        
        # Even for forbidden access, response should be JSON
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert "detail" in data