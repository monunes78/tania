"""
Endpoints do usuário atual — departamentos acessíveis, agentes, etc.
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.db.session import get_db
from src.api.dependencies import get_current_user
from src.models.user import User
from src.models.department import Department
from src.models.agent import Agent

router = APIRouter(prefix="/me", tags=["me"])


class AgentSummary(BaseModel):
    id: str
    name: str


class DepartmentSummary(BaseModel):
    id: str
    name: str
    slug: str
    icon: str
    agents: List[AgentSummary]


@router.get("/departments", response_model=List[DepartmentSummary])
def get_my_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna departamentos e agentes acessíveis ao usuário.
    Admins veem tudo. Usuários regulares veem todos os ativos (Phase 2).
    Controle granular por grupo AD será implementado na Phase 3.
    """
    departments = (
        db.query(Department)
        .filter(Department.is_active == True)
        .order_by(Department.name)
        .all()
    )

    result = []
    for dept in departments:
        agents = (
            db.query(Agent)
            .filter(
                Agent.department_id == dept.id,
                Agent.is_active == True,
            )
            .order_by(Agent.name)
            .all()
        )
        if agents:
            result.append(DepartmentSummary(
                id=dept.id,
                name=dept.name,
                slug=dept.slug,
                icon=dept.icon or "users",
                agents=[AgentSummary(id=a.id, name=a.name) for a in agents],
            ))

    return result
