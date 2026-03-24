"""
Wrapper LiteLLM — ponto único de chamada a qualquer LLM.
Lê a configuração ativa do banco e descriptografa a API key em memória.
"""
import time
from typing import Optional, Generator
import litellm
import structlog
from sqlalchemy.orm import Session

from src.models.llm_config import LLMConfiguration
from src.core.auth.crypto import decrypt

log = structlog.get_logger()

litellm.drop_params = True
litellm.set_verbose = False


def _build_params(config: LLMConfiguration) -> dict:
    """Monta os parâmetros do LiteLLM a partir da configuração do banco."""
    provider = config.provider.lower()
    model = config.model_name

    # Para OpenRouter, o formato é "openrouter/<model>"
    if provider == "openrouter" and not model.startswith("openrouter/"):
        model = f"openrouter/{model}"
    elif provider not in ("openrouter",) and "/" not in model:
        model = f"{provider}/{model}"

    params: dict = {"model": model}

    if config.api_key_enc:
        params["api_key"] = decrypt(config.api_key_enc)

    if config.api_base_url:
        params["api_base"] = config.api_base_url
    elif provider == "openrouter":
        params["api_base"] = "https://openrouter.ai/api/v1"

    return params


def get_active_config(
    db: Session,
    llm_config_id: Optional[str] = None,
) -> LLMConfiguration:
    """Retorna a configuração LLM ativa (por ID ou padrão)."""
    if llm_config_id:
        config = db.query(LLMConfiguration).filter(
            LLMConfiguration.id == llm_config_id,
            LLMConfiguration.is_active == True,
        ).first()
        if config:
            return config

    config = db.query(LLMConfiguration).filter(
        LLMConfiguration.is_default == True,
        LLMConfiguration.is_active == True,
    ).first()

    if not config:
        raise ValueError("Nenhuma configuração LLM ativa encontrada. Configure um LLM no Admin Panel.")

    return config


def chat(
    messages: list[dict],
    db: Session,
    llm_config_id: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> str:
    """Chamada síncrona ao LLM. Retorna o texto completo da resposta."""
    config = get_active_config(db, llm_config_id)
    params = _build_params(config)

    start = time.time()
    response = litellm.completion(
        **params,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
    )
    latency = int((time.time() - start) * 1000)

    content = response.choices[0].message.content
    log.info(
        "llm.call",
        model=params["model"],
        latency_ms=latency,
        tokens_in=response.usage.prompt_tokens,
        tokens_out=response.usage.completion_tokens,
    )
    return content


def stream(
    messages: list[dict],
    db: Session,
    llm_config_id: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> Generator[str, None, None]:
    """Streaming do LLM — gera tokens conforme chegam."""
    config = get_active_config(db, llm_config_id)
    params = _build_params(config)

    response = litellm.completion(
        **params,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )

    for chunk in response:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


def test_connection(config: LLMConfiguration) -> dict:
    """Testa a conexão com o LLM. Retorna {success, latency_ms, response, error}."""
    params = _build_params(config)
    start = time.time()
    try:
        response = litellm.completion(
            **params,
            messages=[{"role": "user", "content": "Responda apenas: OK"}],
            max_tokens=10,
            stream=False,
        )
        latency = int((time.time() - start) * 1000)
        return {
            "success": True,
            "latency_ms": latency,
            "response": response.choices[0].message.content,
            "error": None,
        }
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return {
            "success": False,
            "latency_ms": latency,
            "response": None,
            "error": str(e),
        }
