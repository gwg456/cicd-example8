import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.config import settings

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_conftest.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """Create a test client"""
    Base.metadata.create_all(bind=engine)
    try:
        yield TestClient(app)
    finally:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }


@pytest.fixture
def sample_admin_data():
    """Sample admin user data for testing"""
    return {
        "username": "adminuser",
        "email": "admin@example.com",
        "password": "adminpass123",
        "full_name": "Admin User"
    }


@pytest.fixture
def sample_role_data():
    """Sample role data for testing"""
    return {
        "name": "test_role",
        "description": "Test Role for Testing"
    }


@pytest.fixture
def authenticated_user(client, sample_user_data):
    """Create and authenticate a test user"""
    # Register user
    response = client.post("/api/v1/auth/register", json=sample_user_data)
    assert response.status_code == 200
    user_data = response.json()
    
    # Login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    
    return {
        "user": user_data,
        "token": token_data["access_token"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"}
    }


@pytest.fixture
def authenticated_admin(client, sample_admin_data):
    """Create and authenticate an admin user"""
    # Register admin user
    response = client.post("/api/v1/auth/register", json=sample_admin_data)
    assert response.status_code == 200
    user_data = response.json()
    
    # Login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": sample_admin_data["username"],
            "password": sample_admin_data["password"]
        }
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    
    return {
        "user": user_data,
        "token": token_data["access_token"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"}
    }


@pytest.fixture
def multiple_users(client):
    """Create multiple test users"""
    users = []
    for i in range(3):
        user_data = {
            "username": f"user{i}",
            "email": f"user{i}@example.com",
            "password": f"password{i}123",
            "full_name": f"User {i}"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        users.append(response.json())
    
    return users


def get_auth_headers(token: str) -> dict:
    """Helper function to create authorization headers"""
    return {"Authorization": f"Bearer {token}"}


def get_user_token(client, username: str, password: str) -> str:
    """Helper function to get user token"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    return {
        "app_name": "Test User Auth API",
        "secret_key": "test-secret-key-for-testing-only",
        "algorithm": "HS256",
        "access_token_expire_minutes": 30,
        "database_url": SQLALCHEMY_DATABASE_URL
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Custom assertions
def assert_user_response(response_data, expected_data):
    """Assert user response data matches expected format"""
    assert "id" in response_data
    assert response_data["username"] == expected_data["username"]
    assert response_data["email"] == expected_data["email"]
    assert response_data["is_active"] is True
    assert response_data["is_superuser"] is False
    assert "created_at" in response_data
    assert "roles" in response_data
    assert isinstance(response_data["roles"], list)


def assert_error_response(response, expected_status_code, expected_detail=None):
    """Assert error response format"""
    assert response.status_code == expected_status_code
    data = response.json()
    assert "detail" in data
    if expected_detail:
        assert expected_detail in data["detail"]


def assert_validation_error(response, field_name=None):
    """Assert validation error response format"""
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)
    if field_name:
        field_errors = [
            error for error in data["detail"]
            if field_name in error.get("loc", [])
        ]
        assert len(field_errors) > 0, f"No validation error found for field {field_name}"


# Test data generators
def generate_user_data(username_suffix="", email_suffix=""):
    """Generate test user data"""
    return {
        "username": f"testuser{username_suffix}",
        "email": f"test{email_suffix}@example.com",
        "password": "testpass123",
        "full_name": f"Test User{username_suffix}"
    }


def generate_role_data(name_suffix=""):
    """Generate test role data"""
    return {
        "name": f"testrole{name_suffix}",
        "description": f"Test Role {name_suffix}"
    }


# Database utilities
def create_test_user(db, username="testuser", email="test@example.com"):
    """Create a test user in the database"""
    from app import crud, schemas
    
    user_data = schemas.UserCreate(
        username=username,
        email=email,
        password="testpass123",
        full_name="Test User"
    )
    return crud.create_user(db, user_data)


def create_test_role(db, name="testrole", description="Test Role"):
    """Create a test role in the database"""
    from app import crud, schemas
    
    role_data = schemas.RoleCreate(
        name=name,
        description=description
    )
    return crud.create_role(db, role_data)