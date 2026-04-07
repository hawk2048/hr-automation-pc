"""Settings API - LLM Configuration"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.llm import LLMService

router = APIRouter(prefix="/api/settings", tags=["settings"])

# In-memory config (would be persisted to DB in production)
_current_config = {
    "llm_provider": "ollama",
    "llm_model": "qwen2.5:7b",
    "llm_base_url": "http://localhost:11434",
    "remote_api_key": "",
    "remote_api_base": "https://api.openai.com/v1",
    "remote_model": "gpt-4o-mini",
    "embedding_model": "bge-large-zh-v1.5",
}


class LLMConfigUpdate(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    remote_model: Optional[str] = None
    embedding_model: Optional[str] = None


@router.get("/llm")
async def get_llm_config():
    """Get current LLM configuration"""
    return {
        "provider": _current_config["llm_provider"],
        "model": _current_config["llm_model"],
        "base_url": (
            _current_config["llm_base_url"]
            if _current_config["llm_provider"] == "ollama"
            else _current_config["remote_api_base"]
        ),
        "remote_model": _current_config["remote_model"],
        "embedding_model": _current_config["embedding_model"],
    }


@router.post("/llm")
async def update_llm_config(config: LLMConfigUpdate):
    """Update LLM configuration"""
    global _current_config

    if config.provider is not None:
        _current_config["llm_provider"] = config.provider
    if config.model is not None:
        _current_config["llm_model"] = config.model
    if config.base_url is not None:
        _current_config["llm_base_url"] = config.base_url
    if config.api_key is not None:
        _current_config["remote_api_key"] = config.api_key
    if config.api_base is not None:
        _current_config["remote_api_base"] = config.api_base
    if config.remote_model is not None:
        _current_config["remote_model"] = config.remote_model
    if config.embedding_model is not None:
        _current_config["embedding_model"] = config.embedding_model

    # Update active model name based on provider
    if _current_config["llm_provider"] == "ollama":
        active_model = _current_config["llm_model"]
    else:
        active_model = _current_config["remote_model"]

    return {
        "status": "updated",
        "provider": _current_config["llm_provider"],
        "model": active_model,
    }


@router.get("/llm/health")
async def check_llm_health():
    """Check LLM service health"""
    service = LLMService(
        provider=_current_config["llm_provider"],
        model=(
            _current_config["llm_model"]
            if _current_config["llm_provider"] == "ollama"
            else _current_config["remote_model"]
        ),
        base_url=(
            _current_config["llm_base_url"]
            if _current_config["llm_provider"] == "ollama"
            else _current_config["remote_api_base"]
        ),
        api_key=_current_config["remote_api_key"],
    )
    return await service.check_health()


@router.get("/llm/models")
async def list_available_models():
    """List available models based on current provider"""
    service = LLMService(
        provider=_current_config["llm_provider"],
        model="",  # Don't need a specific model for listing
    )
    health = await service.check_health()

    if health.get("status") == "ok" and "available_models" in health:
        return {"models": health["available_models"]}

    # For remote, return predefined options
    if _current_config["llm_provider"] == "remote":
        return {
            "models": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-3.5-turbo",
                "claude-3-sonnet",
                "claude-3-haiku",
            ]
        }

    return {"models": [], "error": "Cannot connect to Ollama"}


# Embedding model options
EMBEDDING_OPTIONS = [
    "bge-large-zh-v1.5",
    "bge-base-zh-v1.5",
    "bge-small-zh-v1.5",
    "text2vec-base-chinese",
    "paraphrase-multilingual-mpnet-base-v2",
]


@router.get("/embedding/models")
async def list_embedding_models():
    """List available embedding models"""
    return {"models": EMBEDDING_OPTIONS, "recommended": "bge-large-zh-v1.5"}