from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .database import engine, get_db
from .models import Base
from .routers import auth, users, roles
from . import crud, schemas

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A REST API with user registration, login, and role-based access control",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")


@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Welcome to User Auth API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    db = next(get_db())
    
    # Create default roles if they don't exist
    default_roles = [
        {"name": "admin", "description": "Administrator role with full permissions"},
        {"name": "manager", "description": "Manager role with limited admin permissions"},
        {"name": "user", "description": "Regular user role with basic permissions"}
    ]
    
    for role_data in default_roles:
        existing_role = crud.get_role_by_name(db, role_data["name"])
        if not existing_role:
            role_create = schemas.RoleCreate(**role_data)
            crud.create_role(db, role_create)
    
    # Create default superuser if it doesn't exist
    superuser_username = "admin"
    superuser = crud.get_user_by_username(db, superuser_username)
    
    if not superuser:
        superuser_data = schemas.UserCreate(
            username=superuser_username,
            email="admin@example.com",
            password="admin123",
            full_name="System Administrator",
            is_active=True
        )
        superuser = crud.create_user(db, superuser_data)
        
        # Make the user a superuser
        superuser.is_superuser = True
        db.commit()
        
        # Assign admin role
        admin_role = crud.get_role_by_name(db, "admin")
        if admin_role:
            crud.assign_role_to_user(db, superuser.id, admin_role.id)
    
    db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)