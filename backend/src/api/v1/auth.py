from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import structlog

from src.db.session import get_db
from src.core.auth import ldap_client, jwt_service
from src.models.user import User
from src.models.audit_log import AuditLog
from src.api.dependencies import get_current_user

log = structlog.get_logger()
router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    display_name: str
    is_admin: bool

    class Config:
        from_attributes = True


@router.post("/login")
def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    # 1. Autenticar no AD
    ldap_user = ldap_client.authenticate(body.username, body.password)
    if not ldap_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
        )

    # 2. Upsert do usuário no banco
    user = db.query(User).filter(User.ad_object_id == ldap_user.object_id).first()
    if not user:
        user = User(
            ad_object_id=ldap_user.object_id,
            username=ldap_user.username,
            email=ldap_user.email,
            display_name=ldap_user.display_name,
        )
        db.add(user)
    else:
        user.username = ldap_user.username
        user.email = ldap_user.email
        user.display_name = ldap_user.display_name

    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)

    # 3. Emitir tokens
    access_token = jwt_service.create_access_token(str(user.id), user.is_admin)
    refresh_token = jwt_service.create_refresh_token(str(user.id))

    # 4. Definir cookies HttpOnly
    cookie_opts = dict(httponly=True, secure=True, samesite="lax")
    response.set_cookie("access_token", access_token, max_age=28800, **cookie_opts)
    response.set_cookie("refresh_token", refresh_token, max_age=86400, **cookie_opts)

    # 5. Registrar auditoria
    db.add(AuditLog(user_id=str(user.id), action="auth.login"))
    db.commit()

    log.info("auth.login.success", user_id=str(user.id), username=user.username)

    return {
        "user": UserResponse.model_validate(user),
        "access_token": access_token,
    }


@router.post("/logout")
def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    db.add(AuditLog(user_id=str(current_user.id), action="auth.logout"))
    db.commit()
    return {"message": "Logout realizado com sucesso"}


@router.post("/refresh")
def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token ausente")

    payload = jwt_service.verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo")

    new_access = jwt_service.create_access_token(str(user.id), user.is_admin)
    response.set_cookie("access_token", new_access, max_age=28800, httponly=True, secure=True, samesite="lax")

    return {"message": "Token renovado"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
