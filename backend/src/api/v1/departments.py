"""
CRUD de Departamentos — apenas admins.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.api.dependencies import get_admin_user
from src.models.user import User
from src.models.department import Department, DepartmentAccess
from src.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentAccessCreate,
    DepartmentAccessSchema,
)

router = APIRouter(prefix="/departments", tags=["departments"])


def _to_response(dept: Department, db: Session) -> DepartmentResponse:
    from src.models.agent import Agent
    agent_count = db.query(Agent).filter(Agent.department_id == dept.id).count()
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        slug=dept.slug,
        description=dept.description,
        icon=dept.icon,
        is_active=dept.is_active,
        created_at=dept.created_at,
        agent_count=agent_count,
    )


@router.get("", response_model=List[DepartmentResponse])
def list_departments(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    depts = db.query(Department).order_by(Department.name).all()
    return [_to_response(d, db) for d in depts]


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    existing = db.query(Department).filter(Department.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug já existe.")

    dept = Department(**payload.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return _to_response(dept, db)


@router.get("/{dept_id}", response_model=DepartmentResponse)
def get_department(
    dept_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Departamento não encontrado.")
    return _to_response(dept, db)


@router.patch("/{dept_id}", response_model=DepartmentResponse)
def update_department(
    dept_id: str,
    payload: DepartmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Departamento não encontrado.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(dept, field, value)

    db.commit()
    db.refresh(dept)
    return _to_response(dept, db)


@router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    dept_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Departamento não encontrado.")
    db.delete(dept)
    db.commit()


# --- Acesso por grupo AD ---

@router.get("/{dept_id}/access", response_model=List[DepartmentAccessSchema])
def list_access(
    dept_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    return db.query(DepartmentAccess).filter(DepartmentAccess.department_id == dept_id).all()


@router.post("/{dept_id}/access", response_model=DepartmentAccessSchema, status_code=status.HTTP_201_CREATED)
def add_access(
    dept_id: str,
    payload: DepartmentAccessCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Departamento não encontrado.")

    access = DepartmentAccess(
        department_id=dept_id,
        ad_group_dn=payload.ad_group_dn,
        role=payload.role,
    )
    db.add(access)
    db.commit()
    db.refresh(access)
    return access


@router.delete("/{dept_id}/access/{access_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_access(
    dept_id: str,
    access_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    access = db.query(DepartmentAccess).filter(
        DepartmentAccess.id == access_id,
        DepartmentAccess.department_id == dept_id,
    ).first()
    if not access:
        raise HTTPException(status_code=404, detail="Registro de acesso não encontrado.")
    db.delete(access)
    db.commit()
