from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas, models
from ..database import get_db
from ..dependencies import get_current_superuser, require_roles

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=List[schemas.Role])
def read_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["admin", "manager"]))
):
    """Get list of roles (admin/manager only)"""
    roles = crud.get_roles(db, skip=skip, limit=limit)
    return roles


@router.post("/", response_model=schemas.Role)
def create_role(
    role: schemas.RoleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superuser)
):
    """Create new role (superuser only)"""
    # Check if role already exists
    db_role = crud.get_role_by_name(db, name=role.name)
    if db_role:
        raise HTTPException(
            status_code=400,
            detail="Role already exists"
        )
    
    return crud.create_role(db=db, role=role)


@router.get("/{role_id}", response_model=schemas.Role)
def read_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["admin", "manager"]))
):
    """Get role by ID (admin/manager only)"""
    db_role = crud.get_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role