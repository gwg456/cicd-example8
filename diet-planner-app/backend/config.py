import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///diet_planner.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Azure OIDC Configuration
    AZURE_CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')
    AZURE_CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET')
    AZURE_TENANT_ID = os.environ.get('AZURE_TENANT_ID')
    AZURE_AUTHORITY = os.environ.get('AZURE_AUTHORITY')
    AZURE_REDIRECT_URI = os.environ.get('AZURE_REDIRECT_URI')
    AZURE_SCOPE = os.environ.get('AZURE_SCOPE', 'openid profile email').split(' ')
    
    # Frontend Configuration
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'