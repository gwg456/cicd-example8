from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .database import engine, get_db
from .models import Base
from .routers import auth, users, roles, oidc_auth
from . import crud, schemas

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A REST API with user registration, login, OIDC authentication, and role-based access control",
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
app.include_router(oidc_auth.router, prefix="/api/v1")  # OIDC authentication
app.include_router(users.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")


@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Welcome to User Auth API with OIDC Support", 
        "version": "1.0.0",
        "docs": "/docs",
        "authentication": {
            "traditional": "/api/v1/auth/login",
            "oidc_providers": "/api/v1/auth/oidc/providers"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Error handlers
@app.exception_handler(404)
def not_found_handler(request, exc):
    return {"detail": "Not found"}


@app.exception_handler(500)
def internal_error_handler(request, exc):
    return {"detail": "Internal server error"}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # You can add startup logic here, such as:
    # - Database initialization
    # - Cache warming
    # - Background task setup
    pass


# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    # You can add cleanup logic here
    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)