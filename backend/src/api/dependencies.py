from fastapi import Depends, HTTPException, Cookie, status
from sqlalchemy.orm import Session
from typing import Optional

from src.db.session import get_db
from src.core.auth import jwt_service
from src.models.user import User


def get_current_user(
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado",
    )
    if not access_token:
        raise credentials_exception

    payload = jwt_service.verify_access_token(access_token)
    if not payload:
        raise credentials_exception

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise credentials_exception

    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return current_user
