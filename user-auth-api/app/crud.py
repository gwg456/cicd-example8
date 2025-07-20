from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from . import models, schemas
from .auth import get_password_hash, verify_password


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