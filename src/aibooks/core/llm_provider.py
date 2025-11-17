"""LLM provider abstraction layer supporting multiple providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from loguru import logger


@dataclass
class LLMResponse:
    """Standardized LLM response."""

    content: str
    model: str
    tokens_in: int
    tokens_out: int
    finish_reason: str
    cost: float = 0.0


class LLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, model: str, **kwargs):
        """Initialize LLM provider.

        Args:
            model: Model name/identifier
            **kwargs: Provider-specific configuration
        """
        self.model = model
        self.config = kwargs

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs,
    ) -> LLMResponse:
        """Generate completion.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse object
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available.

        Returns:
            True if provider can be used
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider (GPT models)."""

    def __init__(self, model: str, api_key: str, **kwargs):
        """Initialize OpenAI provider."""
        super().__init__(model, **kwargs)
        self.api_key = api_key

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self._available = True
        except ImportError:
            logger.warning("OpenAI library not available")
            self._available = False
        except Exception as e:
            logger.warning(f"OpenAI initialization failed: {e}")
            self._available = False

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs,
    ) -> LLMResponse:
        """Generate completion using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        # Calculate cost
        from ..core.cost_tracker import MODEL_PRICING

        pricing = MODEL_PRICING.get(self.model, MODEL_PRICING["default"])
        cost_in = (response.usage.prompt_tokens / 1000.0) * pricing["input"]
        cost_out = (response.usage.completion_tokens / 1000.0) * pricing["output"]

        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            tokens_in=response.usage.prompt_tokens,
            tokens_out=response.usage.completion_tokens,
            finish_reason=response.choices[0].finish_reason,
            cost=cost_in + cost_out,
        )

    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return self._available and bool(self.api_key)


class AnthropicProvider(LLMProvider):
    """Anthropic provider (Claude models)."""

    def __init__(self, model: str, api_key: str, **kwargs):
        """Initialize Anthropic provider."""
        super().__init__(model, **kwargs)
        self.api_key = api_key

        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
            self._available = True
        except ImportError:
            logger.warning("Anthropic library not available")
            self._available = False
        except Exception as e:
            logger.warning(f"Anthropic initialization failed: {e}")
            self._available = False

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs,
    ) -> LLMResponse:
        """Generate completion using Anthropic."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )

        # Calculate cost
        from ..core.cost_tracker import MODEL_PRICING

        pricing = MODEL_PRICING.get(self.model, MODEL_PRICING["default"])
        cost_in = (response.usage.input_tokens / 1000.0) * pricing["input"]
        cost_out = (response.usage.output_tokens / 1000.0) * pricing["output"]

        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            finish_reason=response.stop_reason,
            cost=cost_in + cost_out,
        )

    def is_available(self) -> bool:
        """Check if Anthropic is available."""
        return self._available and bool(self.api_key)


class OllamaProvider(LLMProvider):
    """Ollama provider (local models) - FREE!"""

    def __init__(self, model: str, base_url: str = "http://localhost:11434", **kwargs):
        """Initialize Ollama provider.

        Args:
            model: Model name (e.g., 'llama3.1', 'mistral', 'phi3')
            base_url: Ollama server URL
        """
        super().__init__(model, **kwargs)
        self.base_url = base_url
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if Ollama is available."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs,
    ) -> LLMResponse:
        """Generate completion using Ollama."""
        import requests

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        data = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        response = requests.post(
            f"{self.base_url}/api/generate",
            json=data,
            timeout=120,
        )
        response.raise_for_status()

        result = response.json()

        # Estimate tokens (Ollama doesn't always provide exact counts)
        tokens_in = len(full_prompt.split()) * 1.3  # Rough estimate
        tokens_out = len(result["response"].split()) * 1.3

        return LLMResponse(
            content=result["response"],
            model=self.model,
            tokens_in=int(tokens_in),
            tokens_out=int(tokens_out),
            finish_reason=result.get("done_reason", "stop"),
            cost=0.0,  # Ollama is free!
        )

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        return self._available


class GroqProvider(LLMProvider):
    """Groq provider (fast inference, free tier available)."""

    def __init__(self, model: str, api_key: str, **kwargs):
        """Initialize Groq provider."""
        super().__init__(model, **kwargs)
        self.api_key = api_key

        try:
            from groq import Groq
            self.client = Groq(api_key=api_key)
            self._available = True
        except ImportError:
            logger.warning("Groq library not available")
            self._available = False
        except Exception as e:
            logger.warning(f"Groq initialization failed: {e}")
            self._available = False

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs,
    ) -> LLMResponse:
        """Generate completion using Groq."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        # Groq has very low costs
        cost = (response.usage.total_tokens / 1000000.0) * 0.27  # ~$0.27 per 1M tokens

        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            tokens_in=response.usage.prompt_tokens,
            tokens_out=response.usage.completion_tokens,
            finish_reason=response.choices[0].finish_reason,
            cost=cost,
        )

    def is_available(self) -> bool:
        """Check if Groq is available."""
        return self._available and bool(self.api_key)


class LLMFactory:
    """Factory for creating LLM providers."""

    @staticmethod
    def create_provider(
        provider: str,
        model: str,
        api_key: Optional[str] = None,
        **kwargs,
    ) -> LLMProvider:
        """Create an LLM provider.

        Args:
            provider: Provider name (openai, anthropic, ollama, groq)
            model: Model name
            api_key: API key (not needed for Ollama)
            **kwargs: Additional provider configuration

        Returns:
            LLMProvider instance

        Raises:
            ValueError: If provider is unknown
        """
        provider = provider.lower()

        if provider == "openai":
            return OpenAIProvider(model, api_key, **kwargs)
        elif provider == "anthropic":
            return AnthropicProvider(model, api_key, **kwargs)
        elif provider == "ollama":
            return OllamaProvider(model, **kwargs)
        elif provider == "groq":
            return GroqProvider(model, api_key, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    @staticmethod
    def get_available_providers() -> List[str]:
        """Get list of available providers.

        Returns:
            List of provider names
        """
        providers = []

        # Check OpenAI
        try:
            import openai
            providers.append("openai")
        except ImportError:
            pass

        # Check Anthropic
        try:
            import anthropic
            providers.append("anthropic")
        except ImportError:
            pass

        # Check Ollama
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=1)
            if response.status_code == 200:
                providers.append("ollama")
        except Exception:
            pass

        # Check Groq
        try:
            import groq
            providers.append("groq")
        except ImportError:
            pass

        return providers
