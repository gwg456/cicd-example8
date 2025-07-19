import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.config import settings

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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


class TestAuth:
    """Test authentication endpoints"""

    def test_register_user(self):
        """Test user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data

    def test_register_duplicate_username(self):
        """Test registration with duplicate username"""
        # First registration
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate",
                "email": "first@example.com",
                "password": "testpass123"
            }
        )
        
        # Second registration with same username
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate",
                "email": "second@example.com",
                "password": "testpass123"
            }
        )
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    def test_login_success(self):
        """Test successful login"""
        # Register user first
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "logintest",
                "email": "login@example.com",
                "password": "loginpass123"
            }
        )
        
        # Login
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "logintest", "password": "loginpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_json_success(self):
        """Test successful login with JSON"""
        # Register user first
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "jsonlogin",
                "email": "jsonlogin@example.com",
                "password": "jsonpass123"
            }
        )
        
        # Login with JSON
        response = client.post(
            "/api/v1/auth/login/json",
            json={"username": "jsonlogin", "password": "jsonpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self):
        """Test login with wrong password"""
        # Register user first
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "wrongpass",
                "email": "wrongpass@example.com",
                "password": "correctpass123"
            }
        )
        
        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "wrongpass", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent", "password": "password123"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]