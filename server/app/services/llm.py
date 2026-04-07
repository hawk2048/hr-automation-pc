"""HR Automation - LLM Service (Local + Remote)"""
from typing import Optional
import httpx
from app.config import settings


class LLMService:
    """Unified LLM service supporting local Ollama and remote APIs"""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model
        self.base_url = base_url or (
            settings.llm_base_url if self.provider == "ollama"
            else settings.remote_api_base
        )
        self.api_key = api_key or settings.remote_api_key

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate text from LLM"""
        if self.provider == "ollama":
            return await self._generate_ollama(prompt, system, temperature, max_tokens)
        else:
            return await self._generate_remote(prompt, system, temperature, max_tokens)

    async def _generate_ollama(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate using local Ollama"""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
            except httpx.ConnectError:
                raise RuntimeError(
                    f"Cannot connect to Ollama at {self.base_url}. "
                    "Please ensure Ollama is running: `ollama serve`"
                )
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Ollama API error: {e.response.status_code}")

    async def _generate_remote(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate using remote API (OpenAI-compatible)"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.ConnectError:
                raise RuntimeError(
                    f"Cannot connect to remote API at {self.base_url}. "
                    "Check your network and API key."
                )
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Remote API error: {e.response.status_code}")

    async def check_health(self) -> dict:
        """Check LLM service health"""
        if self.provider == "ollama":
            url = f"{self.base_url}/api/tags"
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        models = response.json().get("models", [])
                        return {
                            "status": "ok",
                            "provider": "ollama",
                            "available_models": [m["name"] for m in models],
                            "current_model": self.model,
                        }
            except Exception:
                return {"status": "error", "provider": "ollama", "message": "Cannot connect"}
        else:
            # Remote: just check if API key is set
            if self.api_key:
                return {
                    "status": "ok",
                    "provider": "remote",
                    "model": self.model,
                    "base_url": self.base_url,
                }
            return {"status": "error", "provider": "remote", "message": "No API key configured"}


# Global instance
llm_service = LLMService()


def get_llm_service(
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMService:
    """Factory function for LLM service with optional overrides"""
    if provider or model:
        return LLMService(provider=provider, model=model)
    return llm_service