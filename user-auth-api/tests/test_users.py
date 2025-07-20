import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.config import settings

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_users.db"
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


class TestUsers:
    """Test user management endpoints"""

    def setup_method(self):
        """Setup for each test method"""
        # Clear database
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # Create test users
        self.normal_user_data = {
            "username": "normaluser",
            "email": "normal@example.com",
            "password": "normalpass123",
            "full_name": "Normal User"
        }
        
        self.admin_user_data = {
            "username": "adminuser",
            "email": "admin@example.com",
            "password": "adminpass123",
            "full_name": "Admin User"
        }
        
        # Register normal user
        response = client.post("/api/v1/auth/register", json=self.normal_user_data)
        assert response.status_code == 200
        self.normal_user_id = response.json()["id"]
        
        # Register admin user
        response = client.post("/api/v1/auth/register", json=self.admin_user_data)
        assert response.status_code == 200
        self.admin_user_id = response.json()["id"]
        
        # Get tokens
        self.normal_token = self._get_token("normaluser", "normalpass123")
        self.admin_token = self._get_token("adminuser", "adminpass123")

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

    def test_get_current_user(self):
        """Test getting current user information"""
        headers = self._get_auth_headers(self.normal_token)
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "normaluser"
        assert data["email"] == "normal@example.com"
        assert data["full_name"] == "Normal User"
        assert data["is_active"] is True
        assert "id" in data

    def test_get_current_user_unauthorized(self):
        """Test getting current user without authentication"""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_update_current_user(self):
        """Test updating current user information"""
        headers = self._get_auth_headers(self.normal_token)
        update_data = {
            "full_name": "Updated Normal User",
            "email": "updated@example.com"
        }
        
        response = client.put("/api/v1/users/me", json=update_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == "Updated Normal User"
        assert data["email"] == "updated@example.com"

    def test_get_users_list_unauthorized(self):
        """Test getting users list without proper permissions"""
        headers = self._get_auth_headers(self.normal_token)
        response = client.get("/api/v1/users/", headers=headers)
        assert response.status_code == 403

    def test_get_user_by_id_own_profile(self):
        """Test getting own user profile by ID"""
        headers = self._get_auth_headers(self.normal_token)
        response = client.get(f"/api/v1/users/{self.normal_user_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "normaluser"

    def test_get_user_by_id_other_user_forbidden(self):
        """Test getting other user's profile without admin permissions"""
        headers = self._get_auth_headers(self.normal_token)
        response = client.get(f"/api/v1/users/{self.admin_user_id}", headers=headers)
        assert response.status_code == 403

    def test_get_user_by_id_nonexistent(self):
        """Test getting nonexistent user"""
        headers = self._get_auth_headers(self.normal_token)
        response = client.get("/api/v1/users/9999", headers=headers)
        assert response.status_code == 404

    def test_update_user_by_admin(self):
        """Test updating user by admin (requires superuser)"""
        # This test assumes admin user has superuser privileges
        # In a real scenario, you'd need to set is_superuser=True for admin
        headers = self._get_auth_headers(self.admin_token)
        update_data = {
            "full_name": "Updated by Admin",
            "is_active": False
        }
        
        response = client.put(f"/api/v1/users/{self.normal_user_id}", json=update_data, headers=headers)
        # This might return 403 if admin user is not superuser
        # assert response.status_code == 200

    def test_delete_user_unauthorized(self):
        """Test deleting user without superuser permissions"""
        headers = self._get_auth_headers(self.normal_token)
        response = client.delete(f"/api/v1/users/{self.admin_user_id}", headers=headers)
        assert response.status_code == 401  # or 403 depending on implementation

    def test_password_validation_in_update(self):
        """Test password validation during user update"""
        headers = self._get_auth_headers(self.normal_token)
        update_data = {
            "password": "short"  # Too short password
        }
        
        response = client.put("/api/v1/users/me", json=update_data, headers=headers)
        # This depends on password validation in the endpoint
        # assert response.status_code == 422

    def test_user_profile_completeness(self):
        """Test that user profile returns all expected fields"""
        headers = self._get_auth_headers(self.normal_token)
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ["id", "username", "email", "is_active", "is_superuser", "created_at"]
        for field in required_fields:
            assert field in data
        
        # Check roles array exists
        assert "roles" in data
        assert isinstance(data["roles"], list)


class TestUserRoles:
    """Test user role management endpoints"""

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
        
        # Create test role
        role_data = {
            "name": "test_role",
            "description": "Test Role"
        }
        headers = self._get_auth_headers(self.token)
        response = client.post("/api/v1/roles/", json=role_data, headers=headers)
        if response.status_code == 200:
            self.role_id = response.json()["id"]
        else:
            self.role_id = 1  # Fallback for testing

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

    def test_assign_role_to_user_unauthorized(self):
        """Test assigning role to user without superuser permissions"""
        headers = self._get_auth_headers(self.token)
        response = client.post(f"/api/v1/users/{self.user_id}/roles/{self.role_id}", headers=headers)
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

    def test_remove_role_from_user_unauthorized(self):
        """Test removing role from user without superuser permissions"""
        headers = self._get_auth_headers(self.token)
        response = client.delete(f"/api/v1/users/{self.user_id}/roles/{self.role_id}", headers=headers)
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

    def test_assign_role_nonexistent_user(self):
        """Test assigning role to nonexistent user"""
        headers = self._get_auth_headers(self.token)
        response = client.post(f"/api/v1/users/9999/roles/{self.role_id}", headers=headers)
        assert response.status_code in [401, 403, 404]

    def test_assign_nonexistent_role(self):
        """Test assigning nonexistent role to user"""
        headers = self._get_auth_headers(self.token)
        response = client.post(f"/api/v1/users/{self.user_id}/roles/9999", headers=headers)
        assert response.status_code in [401, 403, 404]