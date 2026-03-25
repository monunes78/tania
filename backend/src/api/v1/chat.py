"""
Chat com RAG — busca semântica no Qdrant antes de chamar o LLM.
"""
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.db.session import get_db
from src.api.dependencies import get_current_user
from src.models.user import User
from src.models.agent import Agent
from src.models.document import Document
from src.models.conversation import Conversation, Message
from src.core.llm import litellm_client

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    agent_id: str
    message: str
    conversation_id: Optional[str] = None


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


def _retrieve_context(agent: Agent, query: str, user_id: str, db: Session) -> tuple[str, List[str]]:
    """
    Busca chunks relevantes via pgvector.
    Retorna (context_block, list_of_doc_ids_used).
    """
    try:
        from src.core.rag import embedder
        from src.core.rag.vector_store import search as vector_search

        accessible_docs = (
            db.query(Document)
            .filter(
                Document.agent_id == agent.id,
                Document.status == "indexed",
                Document.classification == "public",
            )
            .all()
        )
        # TODO Phase 5: incluir docs confidenciais com acesso individual

        if not accessible_docs:
            return "", []

        allowed_ids = [str(d.id) for d in accessible_docs]
        query_vector = embedder.embed_one(query)

        results = vector_search(
            db=db,
            agent_id=str(agent.id),
            query_vector=query_vector,
            top_k=agent.max_context_chunks,
            score_threshold=0.35,
            allowed_document_ids=allowed_ids,
        )

        if not results:
            return "", []

        lines = ["## Contexto relevante da base de conhecimento:\n"]
        used_ids: List[str] = []
        doc_names: dict[str, str] = {str(d.id): d.original_name for d in accessible_docs}

        for i, hit in enumerate(results, 1):
            doc_id = hit["document_id"]
            doc_name = doc_names.get(doc_id, "Documento")
            lines.append(f"[{i}] **{doc_name}** (relevância: {hit['score']:.0%})\n{hit['content']}\n")
            if doc_id not in used_ids:
                used_ids.append(doc_id)

        return "\n".join(lines), used_ids

    except Exception:
        return "", []


def _build_messages(agent: Agent, conversation: Conversation, user_message: str, context: str, db: Session) -> list[dict]:
    messages = []

    system = agent.system_prompt or ""
    if context:
        system = f"{system}\n\n{context}" if system else context

    if system:
        messages.append({"role": "system", "content": system})

    # Histórico recente (últimas 20 mensagens = 10 trocas)
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
    """Chat síncrono com RAG."""
    agent = _get_agent_or_404(payload.agent_id, db)
    conv = _get_or_create_conversation(payload.conversation_id, agent.id, current_user.id, db)

    context, rag_doc_ids = _retrieve_context(agent, payload.message, str(current_user.id), db)
    messages = _build_messages(agent, conv, payload.message, context, db)

    user_msg = Message(conversation_id=conv.id, role="user", content=payload.message)
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

    import json as _json
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=response_text,
        rag_chunks_used=_json.dumps(rag_doc_ids) if rag_doc_ids else None,
    )
    db.add(assistant_msg)
    db.commit()

    return {
        "conversation_id": conv.id,
        "message_id": assistant_msg.id,
        "content": response_text,
        "rag_sources": rag_doc_ids,
    }


@router.post("/stream")
def stream_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chat com streaming SSE + RAG."""
    agent = _get_agent_or_404(payload.agent_id, db)
    conv = _get_or_create_conversation(payload.conversation_id, agent.id, current_user.id, db)

    context, rag_doc_ids = _retrieve_context(agent, payload.message, str(current_user.id), db)
    messages = _build_messages(agent, conv, payload.message, context, db)

    user_msg = Message(conversation_id=conv.id, role="user", content=payload.message)
    db.add(user_msg)
    db.commit()

    conversation_id = conv.id

    def generate():
        full_response = []
        try:
            # Envia fontes RAG antes de começar o streaming
            if rag_doc_ids:
                yield f"data: {json.dumps({'rag_sources': rag_doc_ids})}\n\n"

            for token in litellm_client.stream(
                messages=messages,
                db=db,
                llm_config_id=agent.llm_config_id,
                temperature=float(agent.temperature or 0.1),
                max_tokens=2048,
            ):
                full_response.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"

            full_text = "".join(full_response)
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_text,
                rag_chunks_used=json.dumps(rag_doc_ids) if rag_doc_ids else None,
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
        {"id": c.id, "created_at": c.created_at, "updated_at": c.updated_at}
        for c in convs
    ]


@router.get("/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
        {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at}
        for m in msgs
    ]
