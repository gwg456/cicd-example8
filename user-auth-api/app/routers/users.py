from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas, models
from ..database import get_db
from ..dependencies import get_current_active_user, get_current_superuser, require_roles

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=schemas.User)
def read_current_user(
    current_user: models.User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=schemas.User)
def update_current_user(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    return crud.update_user(db, current_user.id, user_update)


@router.get("/", response_model=List[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["admin", "manager"]))
):
    """Get list of users (admin/manager only)"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=schemas.User)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get user by ID"""
    # Users can only see their own profile unless they're admin/superuser
    if user_id != current_user.id and not current_user.is_superuser:
        user_roles = [role.name for role in current_user.roles]
        if "admin" not in user_roles and "manager" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superuser)
):
    """Update user (superuser only)"""
    db_user = crud.update_user(db, user_id, user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superuser)
):
    """Delete user (superuser only)"""
    success = crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/roles/{role_id}")
def assign_role_to_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superuser)
):
    """Assign role to user (superuser only)"""
    success = crud.assign_role_to_user(db, user_id, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="User or role not found")
    return {"message": "Role assigned successfully"}


@router.delete("/{user_id}/roles/{role_id}")
def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superuser)
):
    """Remove role from user (superuser only)"""
    success = crud.remove_role_from_user(db, user_id, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="User or role not found")
    return {"message": "Role removed successfully"}