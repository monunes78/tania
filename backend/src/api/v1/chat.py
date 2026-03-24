"""
Chat — endpoint básico sem RAG (Phase 2).
RAG será adicionado na Phase 3.
"""
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.db.session import get_db
from src.api.dependencies import get_current_user
from src.models.user import User
from src.models.agent import Agent
from src.models.conversation import Conversation, Message
from src.core.llm import litellm_client

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    agent_id: str
    message: str
    conversation_id: Optional[str] = None


class ConversationResponse(BaseModel):
    conversation_id: str
    message_id: str


def _get_agent_or_404(agent_id: str, db: Session) -> Agent:
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.is_active == True,
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado.")
    return agent


def _get_or_create_conversation(
    conversation_id: Optional[str],
    agent_id: str,
    user_id: str,
    db: Session,
) -> Conversation:
    if conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        ).first()
        if conv:
            return conv

    conv = Conversation(agent_id=agent_id, user_id=user_id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def _build_messages(agent: Agent, conversation: Conversation, user_message: str, db: Session) -> list[dict]:
    messages = []

    if agent.system_prompt:
        messages.append({"role": "system", "content": agent.system_prompt})

    # Histórico recente (últimas 10 trocas)
    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .limit(20)
        .all()
    )
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": user_message})
    return messages


@router.post("/message")
def send_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chat síncrono — retorna resposta completa."""
    agent = _get_agent_or_404(payload.agent_id, db)
    conv = _get_or_create_conversation(payload.conversation_id, agent.id, current_user.id, db)
    messages = _build_messages(agent, conv, payload.message, db)

    # Salva mensagem do usuário
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=payload.message,
    )
    db.add(user_msg)
    db.flush()

    try:
        response_text = litellm_client.chat(
            messages=messages,
            db=db,
            llm_config_id=agent.llm_config_id,
            temperature=float(agent.temperature or 0.1),
            max_tokens=2048,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Salva resposta do assistente
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=response_text,
    )
    db.add(assistant_msg)
    db.commit()

    return {
        "conversation_id": conv.id,
        "message_id": assistant_msg.id,
        "content": response_text,
    }


@router.post("/stream")
def stream_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chat com streaming SSE."""
    agent = _get_agent_or_404(payload.agent_id, db)
    conv = _get_or_create_conversation(payload.conversation_id, agent.id, current_user.id, db)
    messages = _build_messages(agent, conv, payload.message, db)

    # Salva mensagem do usuário
    user_msg = Message(conversation_id=conv.id, role="user", content=payload.message)
    db.add(user_msg)
    db.commit()

    conversation_id = conv.id

    def generate():
        full_response = []
        try:
            for token in litellm_client.stream(
                messages=messages,
                db=db,
                llm_config_id=agent.llm_config_id,
                temperature=float(agent.temperature or 0.1),
                max_tokens=2048,
            ):
                full_response.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Salva resposta completa
            full_text = "".join(full_response)
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_text,
            )
            db.add(assistant_msg)
            db.commit()

            yield f"data: {json.dumps({'done': True, 'message_id': assistant_msg.id})}\n\n"

        except ValueError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations/{agent_id}")
def list_conversations(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista conversas do usuário com um agente."""
    convs = (
        db.query(Conversation)
        .filter(
            Conversation.agent_id == agent_id,
            Conversation.user_id == current_user.id,
        )
        .order_by(Conversation.updated_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": c.id,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in convs
    ]


@router.get("/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna mensagens de uma conversa."""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")

    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at,
        }
        for m in msgs
    ]
