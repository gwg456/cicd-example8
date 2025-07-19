from sqlalchemy.orm import Session
from typing import Optional, List
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


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Create new user"""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=user.is_active
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
    
    # Hash password if provided
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
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
    """Authenticate user"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


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
    db_role = models.Role(name=role.name, description=role.description)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


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