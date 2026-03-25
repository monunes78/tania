"""
CRUD de Agentes — apenas admins.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.api.dependencies import get_admin_user
from src.models.user import User
from src.models.agent import Agent
from src.models.department import Department
from src.models.llm_config import LLMConfiguration
from src.models.agent_prompt_history import AgentPromptHistory
from src.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentPromptUpdate,
    AgentPromptHistoryResponse,
)

router = APIRouter(prefix="/agents", tags=["agents"])


def _to_response(agent: Agent, db: Session) -> AgentResponse:
    dept = db.query(Department).filter(Department.id == agent.department_id).first()
    llm = None
    if agent.llm_config_id:
        llm = db.query(LLMConfiguration).filter(LLMConfiguration.id == agent.llm_config_id).first()

    from src.models.document import Document
    doc_count = db.query(Document).filter(Document.agent_id == agent.id).count()

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        system_prompt=agent.system_prompt,
        temperature=agent.temperature,
        max_context_chunks=agent.max_context_chunks,
        enable_sql_access=agent.enable_sql_access,
        is_active=agent.is_active,
        department_id=agent.department_id,
        department_name=dept.name if dept else None,
        llm_config_id=agent.llm_config_id,
        llm_config_name=llm.name if llm else None,
        qdrant_collection=None,
        document_count=doc_count,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.get("", response_model=List[AgentResponse])
def list_agents(
    department_id: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    q = db.query(Agent)
    if department_id:
        q = q.filter(Agent.department_id == department_id)
    agents = q.order_by(Agent.name).all()
    return [_to_response(a, db) for a in agents]


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    payload: AgentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    dept = db.query(Department).filter(Department.id == payload.department_id).first()
    if not dept:
        raise HTTPException(status_code=400, detail="Departamento não encontrado.")

    agent = Agent(**payload.model_dump())
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return _to_response(agent, db)


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado.")
    return _to_response(agent, db)


@router.patch("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: str,
    payload: AgentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)

    db.commit()
    db.refresh(agent)
    return _to_response(agent, db)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado.")
    db.delete(agent)
    db.commit()


# --- Prompt Editor ---

@router.put("/{agent_id}/prompt", response_model=AgentResponse)
def update_prompt(
    agent_id: str,
    payload: AgentPromptUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado.")

    # Salva histórico antes de alterar
    history = AgentPromptHistory(
        agent_id=agent_id,
        updated_by=admin.id,
        system_prompt=agent.system_prompt,
    )
    db.add(history)

    agent.system_prompt = payload.system_prompt
    db.commit()
    db.refresh(agent)
    return _to_response(agent, db)


@router.get("/{agent_id}/prompt/history", response_model=List[AgentPromptHistoryResponse])
def get_prompt_history(
    agent_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    history = (
        db.query(AgentPromptHistory)
        .filter(AgentPromptHistory.agent_id == agent_id)
        .order_by(AgentPromptHistory.created_at.desc())
        .limit(20)
        .all()
    )

    result = []
    for h in history:
        user = db.query(User).filter(User.id == h.updated_by).first()
        result.append(AgentPromptHistoryResponse(
            id=h.id,
            system_prompt=h.system_prompt,
            updated_by_name=user.display_name if user else None,
            created_at=h.created_at,
        ))
    return result
