from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from . import models, schemas
from .auth import get_password_hash, verify_password
from .client_auth import client_auth_service


# User CRUD operations
def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Get user by username"""
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get user by email"""
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Get list of users"""
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate, is_oidc_user: bool = False) -> models.User:
    """Create new user"""
    hashed_password = None
    if not is_oidc_user and user.password:
        hashed_password = get_password_hash(user.password)
    
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=user.is_active,
        is_oidc_user=is_oidc_user
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> Optional[models.User]:
    """Update user"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Handle password update
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data["password"])
        del update_data["password"]
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    """Delete user"""
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True


def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    """Authenticate user with username and password"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    
    # OIDC users cannot authenticate with password
    if user.is_oidc_user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


# OIDC-specific CRUD operations
def get_user_by_provider_id(db: Session, provider: str, provider_user_id: str) -> Optional[models.User]:
    """Get user by OIDC provider and provider user ID"""
    oidc_link = db.query(models.UserOIDCLink).filter(
        models.UserOIDCLink.provider == provider,
        models.UserOIDCLink.provider_user_id == provider_user_id
    ).first()
    
    if oidc_link:
        return oidc_link.user
    return None


def create_user_provider_link(
    db: Session, 
    user_id: int, 
    provider: str, 
    provider_user_id: str,
    provider_data: Optional[Dict[str, Any]] = None
) -> models.UserOIDCLink:
    """Create a link between user and OIDC provider"""
    # Check if link already exists
    existing_link = db.query(models.UserOIDCLink).filter(
        models.UserOIDCLink.user_id == user_id,
        models.UserOIDCLink.provider == provider
    ).first()
    
    if existing_link:
        # Update existing link
        existing_link.provider_user_id = provider_user_id
        if provider_data:
            existing_link.provider_data = provider_data
        db.commit()
        db.refresh(existing_link)
        return existing_link
    
    # Create new link
    oidc_link = models.UserOIDCLink(
        user_id=user_id,
        provider=provider,
        provider_user_id=provider_user_id,
        provider_data=provider_data
    )
    db.add(oidc_link)
    db.commit()
    db.refresh(oidc_link)
    return oidc_link


def get_user_provider_links(db: Session, user_id: int) -> List[models.UserOIDCLink]:
    """Get all OIDC provider links for a user"""
    return db.query(models.UserOIDCLink).filter(
        models.UserOIDCLink.user_id == user_id
    ).all()


def remove_user_provider_link(db: Session, user_id: int, provider: str) -> bool:
    """Remove OIDC provider link for a user"""
    oidc_link = db.query(models.UserOIDCLink).filter(
        models.UserOIDCLink.user_id == user_id,
        models.UserOIDCLink.provider == provider
    ).first()
    
    if oidc_link:
        db.delete(oidc_link)
        db.commit()
        return True
    return False


# API Client CRUD operations
def create_api_client(
    db: Session, 
    client: schemas.APIClientCreate, 
    owner_id: int
) -> models.APIClient:
    """Create new API client"""
    credentials = client_auth_service.generate_client_credentials()
    client_secret_hash = get_password_hash(credentials["client_secret"])
    
    db_client = models.APIClient(
        client_id=credentials["client_id"],
        client_secret_hash=client_secret_hash,
        name=client.name,
        description=client.description,
        owner_id=owner_id,
        scopes=client.scopes,
        is_trusted=client.is_trusted
    )
    
    # Set expiration if provided
    if client.expires_days:
        db_client.expires_at = datetime.utcnow() + timedelta(days=client.expires_days)
    
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    
    # Return client with plain text secret (only time it's available)
    db_client.client_secret = credentials["client_secret"]
    return db_client


def get_api_client_by_id(db: Session, client_id: str) -> Optional[models.APIClient]:
    """Get API client by client_id"""
    return db.query(models.APIClient).filter(
        models.APIClient.client_id == client_id
    ).first()


def get_user_api_clients(db: Session, user_id: int) -> List[models.APIClient]:
    """Get all API clients for a user"""
    return db.query(models.APIClient).filter(
        models.APIClient.owner_id == user_id
    ).all()


def update_api_client(
    db: Session, 
    client_id: str, 
    client_update: schemas.APIClientUpdate
) -> Optional[models.APIClient]:
    """Update API client"""
    db_client = get_api_client_by_id(db, client_id)
    if not db_client:
        return None
    
    update_data = client_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_client, field, value)
    
    db.commit()
    db.refresh(db_client)
    return db_client


def delete_api_client(db: Session, client_id: str) -> bool:
    """Delete API client"""
    db_client = get_api_client_by_id(db, client_id)
    if not db_client:
        return False
    
    db.delete(db_client)
    db.commit()
    return True


def authenticate_client(db: Session, client_id: str, client_secret: str) -> Optional[models.APIClient]:
    """Authenticate API client"""
    client = get_api_client_by_id(db, client_id)
    if not client or not client.is_active:
        return None
    
    # Check expiration
    if client.expires_at and client.expires_at < datetime.utcnow():
        return None
    
    # Verify client secret
    if not verify_password(client_secret, client.client_secret_hash):
        return None
    
    # Update last used time and request count
    client.last_used_at = datetime.utcnow()
    client.request_count += 1
    db.commit()
    
    return client


def create_api_key(
    db: Session, 
    api_key: schemas.APIKeyCreate, 
    client_id: int
) -> models.APIKey:
    """Create new API key"""
    key_value = client_auth_service.generate_api_key(f"client_{client_id}")
    key_hash = get_password_hash(key_value)
    
    db_key = models.APIKey(
        key_id=f"ak_{client_id}_{len(key_value)}",
        key_hash=key_hash,
        name=api_key.name,
        client_id=client_id,
        scopes=api_key.scopes
    )
    
    # Set expiration if provided
    if api_key.expires_days:
        db_key.expires_at = datetime.utcnow() + timedelta(days=api_key.expires_days)
    
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    
    # Return key with plain text value (only time it's available)
    db_key.key_value = key_value
    return db_key


def get_api_key_by_id(db: Session, key_id: str) -> Optional[models.APIKey]:
    """Get API key by key_id"""
    return db.query(models.APIKey).filter(
        models.APIKey.key_id == key_id
    ).first()


def get_client_api_keys(db: Session, client_id: int) -> List[models.APIKey]:
    """Get all API keys for a client"""
    return db.query(models.APIKey).filter(
        models.APIKey.client_id == client_id
    ).all()


def authenticate_api_key(db: Session, key_id: str, key_value: str) -> Optional[models.APIKey]:
    """Authenticate API key"""
    api_key = get_api_key_by_id(db, key_id)
    if not api_key or not api_key.is_active:
        return None
    
    # Check expiration
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        return None
    
    # Verify key value
    if not verify_password(key_value, api_key.key_hash):
        return None
    
    # Update last used time and request count
    api_key.last_used_at = datetime.utcnow()
    api_key.request_count += 1
    db.commit()
    
    return api_key


def revoke_api_key(db: Session, key_id: str) -> bool:
    """Revoke API key"""
    api_key = get_api_key_by_id(db, key_id)
    if not api_key:
        return False
    
    api_key.is_active = False
    db.commit()
    return True


# Role CRUD operations
def get_role(db: Session, role_id: int) -> Optional[models.Role]:
    """Get role by ID"""
    return db.query(models.Role).filter(models.Role.id == role_id).first()


def get_role_by_name(db: Session, name: str) -> Optional[models.Role]:
    """Get role by name"""
    return db.query(models.Role).filter(models.Role.name == name).first()


def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[models.Role]:
    """Get list of roles"""
    return db.query(models.Role).offset(skip).limit(limit).all()


def create_role(db: Session, role: schemas.RoleCreate) -> models.Role:
    """Create new role"""
    db_role = models.Role(
        name=role.name,
        description=role.description
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


def update_role(db: Session, role_id: int, role_update: schemas.RoleUpdate) -> Optional[models.Role]:
    """Update role"""
    db_role = get_role(db, role_id)
    if not db_role:
        return None
    
    update_data = role_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_role, field, value)
    
    db.commit()
    db.refresh(db_role)
    return db_role


def delete_role(db: Session, role_id: int) -> bool:
    """Delete role"""
    db_role = get_role(db, role_id)
    if not db_role:
        return False
    
    db.delete(db_role)
    db.commit()
    return True


def assign_role_to_user(db: Session, user_id: int, role_id: int) -> bool:
    """Assign role to user"""
    user = get_user(db, user_id)
    role = get_role(db, role_id)
    
    if not user or not role:
        return False
    
    if role not in user.roles:
        user.roles.append(role)
        db.commit()
    
    return True


def remove_role_from_user(db: Session, user_id: int, role_id: int) -> bool:
    """Remove role from user"""
    user = get_user(db, user_id)
    role = get_role(db, role_id)
    
    if not user or not role:
        return False
    
    if role in user.roles:
        user.roles.remove(role)
        db.commit()
    
    return True


# Permission CRUD operations
def create_permission(db: Session, permission: schemas.PermissionCreate) -> models.Permission:
    """Create new permission"""
    db_permission = models.Permission(
        name=permission.name,
        description=permission.description,
        resource=permission.resource,
        action=permission.action
    )
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission


def get_permissions(db: Session, skip: int = 0, limit: int = 100) -> List[models.Permission]:
    """Get list of permissions"""
    return db.query(models.Permission).offset(skip).limit(limit).all()