"""
Admin — gestão de configurações LLM.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.api.dependencies import get_admin_user
from src.models.user import User
from src.models.llm_config import LLMConfiguration
from src.core.auth.crypto import encrypt
from src.core.llm.litellm_client import test_connection
from src.schemas.llm_config import (
    LLMConfigCreate,
    LLMConfigUpdate,
    LLMConfigResponse,
    LLMTestResult,
)

router = APIRouter(prefix="/admin/llm", tags=["admin"])


def _to_response(config: LLMConfiguration) -> LLMConfigResponse:
    return LLMConfigResponse(
        id=config.id,
        name=config.name,
        provider=config.provider,
        model_name=config.model_name,
        api_base_url=config.api_base_url,
        extra_params=config.extra_params,
        is_default=config.is_default,
        is_active=config.is_active,
        has_api_key=bool(config.api_key_enc),
        created_at=config.created_at,
    )


@router.get("", response_model=List[LLMConfigResponse])
def list_llm_configs(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    configs = db.query(LLMConfiguration).order_by(LLMConfiguration.name).all()
    return [_to_response(c) for c in configs]


@router.post("", response_model=LLMConfigResponse, status_code=status.HTTP_201_CREATED)
def create_llm_config(
    payload: LLMConfigCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    data = payload.model_dump(exclude={"api_key"})

    # Se é o primeiro config, torna padrão automaticamente
    if payload.is_default:
        db.query(LLMConfiguration).update({"is_default": False})

    config = LLMConfiguration(**data)
    if payload.api_key:
        config.api_key_enc = encrypt(payload.api_key)

    db.add(config)
    db.commit()
    db.refresh(config)
    return _to_response(config)


@router.get("/{config_id}", response_model=LLMConfigResponse)
def get_llm_config(
    config_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    config = db.query(LLMConfiguration).filter(LLMConfiguration.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuração LLM não encontrada.")
    return _to_response(config)


@router.patch("/{config_id}", response_model=LLMConfigResponse)
def update_llm_config(
    config_id: str,
    payload: LLMConfigUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    config = db.query(LLMConfiguration).filter(LLMConfiguration.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuração LLM não encontrada.")

    data = payload.model_dump(exclude_unset=True, exclude={"api_key"})

    if payload.is_default:
        db.query(LLMConfiguration).filter(
            LLMConfiguration.id != config_id
        ).update({"is_default": False})

    for field, value in data.items():
        setattr(config, field, value)

    if payload.api_key is not None:
        config.api_key_enc = encrypt(payload.api_key) if payload.api_key else None

    db.commit()
    db.refresh(config)
    return _to_response(config)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_llm_config(
    config_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    config = db.query(LLMConfiguration).filter(LLMConfiguration.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuração LLM não encontrada.")
    if config.is_default:
        raise HTTPException(status_code=400, detail="Não é possível excluir a configuração padrão.")
    db.delete(config)
    db.commit()


@router.post("/{config_id}/test", response_model=LLMTestResult)
def test_llm_config(
    config_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    config = db.query(LLMConfiguration).filter(LLMConfiguration.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuração LLM não encontrada.")
    return test_connection(config)
