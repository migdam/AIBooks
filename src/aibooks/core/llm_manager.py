"""LLM Manager for intelligent provider and model selection."""

from typing import Optional, Dict, Any
from loguru import logger

from .llm_provider import LLMFactory, LLMProvider, LLMResponse
from .config import get_config
from .cost_tracker import CostTracker


class LLMManager:
    """Manages LLM provider selection and usage."""

    # Task complexity classification
    SIMPLE_TASKS = {
        "format_detection",
        "simple_metadata",
        "quick_validation",
    }

    MODERATE_TASKS = {
        "metadata_enhancement",
        "text_cleanup",
        "chapter_detection",
    }

    COMPLEX_TASKS = {
        "metadata_inference",
        "quality_analysis",
        "failure_recovery",
        "ocr_correction",
    }

    def __init__(self, cost_tracker: Optional[CostTracker] = None):
        """Initialize LLM Manager.

        Args:
            cost_tracker: Optional cost tracker for logging
        """
        self.config = get_config()
        self.cost_tracker = cost_tracker

        # Cache providers
        self._providers: Dict[str, LLMProvider] = {}

        logger.info("LLM Manager initialized")
        self._log_available_providers()

    def _log_available_providers(self):
        """Log available LLM providers."""
        available = LLMFactory.get_available_providers()
        if available:
            logger.info(f"Available LLM providers: {', '.join(available)}")
        else:
            logger.warning("No LLM providers available")

    def _get_provider(self, provider_name: str, model: str) -> LLMProvider:
        """Get or create a provider instance.

        Args:
            provider_name: Provider name
            model: Model name

        Returns:
            LLMProvider instance
        """
        cache_key = f"{provider_name}:{model}"

        if cache_key not in self._providers:
            # Get API key based on provider
            api_key = None
            if provider_name == "openai":
                api_key = self.config.llm.openai_api_key
            elif provider_name == "anthropic":
                api_key = self.config.llm.anthropic_api_key
            elif provider_name == "groq":
                api_key = self.config.llm.groq_api_key

            # Create provider
            self._providers[cache_key] = LLMFactory.create_provider(
                provider_name,
                model,
                api_key=api_key,
                base_url=self.config.llm.ollama_base_url if provider_name == "ollama" else None,
            )

        return self._providers[cache_key]

    def select_provider_for_task(self, task: str) -> tuple[str, str]:
        """Select best provider and model for a task.

        Args:
            task: Task name/type

        Returns:
            Tuple of (provider_name, model_name)
        """
        # Check if we should use free models for simple tasks
        if self.config.llm.use_free_for_simple and task in self.SIMPLE_TASKS:
            # Try to use Ollama for free
            provider = self._get_provider(
                self.config.llm.free_provider,
                self.config.llm.free_model,
            )

            if provider.is_available():
                logger.info(f"Using FREE provider for simple task: {task}")
                return self.config.llm.free_provider, self.config.llm.free_model

        # Check daily budget
        if self.cost_tracker:
            daily_cost = self.cost_tracker.get_daily_cost()
            daily_cap = self.config.cost.daily_cost_cap

            if daily_cost >= daily_cap * 0.9:  # 90% of budget used
                logger.warning(f"Budget nearly exhausted ({daily_cost:.2f}/{daily_cap:.2f}), using free provider")

                # Force free provider
                provider = self._get_provider(
                    self.config.llm.free_provider,
                    self.config.llm.free_model,
                )

                if provider.is_available():
                    return self.config.llm.free_provider, self.config.llm.free_model

        # Select based on task complexity
        if task in self.COMPLEX_TASKS:
            # Use advanced provider/model
            return self.config.llm.advanced_provider, self.config.llm.advanced_model
        elif task in self.MODERATE_TASKS:
            # Use default provider/model
            return self.config.llm.default_provider, self.config.llm.default_model
        else:
            # Simple task - use default or free
            if self.config.llm.use_free_for_simple:
                provider = self._get_provider(
                    self.config.llm.free_provider,
                    self.config.llm.simple_task_model,
                )
                if provider.is_available():
                    return self.config.llm.free_provider, self.config.llm.simple_task_model

            return self.config.llm.default_provider, self.config.llm.default_model

    def complete(
        self,
        prompt: str,
        task: str = "general",
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        force_provider: Optional[str] = None,
        force_model: Optional[str] = None,
        document_id: Optional[int] = None,
    ) -> LLMResponse:
        """Generate LLM completion with intelligent provider selection.

        Args:
            prompt: User prompt
            task: Task type for provider selection
            system_prompt: Optional system prompt
            temperature: Sampling temperature (uses config default if None)
            max_tokens: Max tokens (uses config default if None)
            force_provider: Force specific provider
            force_model: Force specific model
            document_id: Optional document ID for logging

        Returns:
            LLMResponse object
        """
        # Select provider and model
        if force_provider and force_model:
            provider_name, model = force_provider, force_model
        else:
            provider_name, model = self.select_provider_for_task(task)

        # Get provider
        provider = self._get_provider(provider_name, model)

        if not provider.is_available():
            logger.warning(f"Provider {provider_name} not available, falling back to default")
            provider_name = self.config.llm.default_provider
            model = self.config.llm.default_model
            provider = self._get_provider(provider_name, model)

        # Use config defaults if not specified
        temperature = temperature if temperature is not None else self.config.llm.temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.llm.max_tokens

        # Generate completion
        logger.info(f"Generating completion: provider={provider_name}, model={model}, task={task}")

        import time
        start_time = time.time()

        try:
            response = provider.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Log to cost tracker
            if self.cost_tracker:
                self.cost_tracker.log_usage(
                    document_id=document_id,
                    step=task,
                    model=f"{provider_name}:{model}",
                    tokens_in=response.tokens_in,
                    tokens_out=response.tokens_out,
                    duration_ms=duration_ms,
                    cost=response.cost,
                    payload_preview=prompt[:200],
                    response_status="success",
                )

            logger.info(
                f"Completion generated: {response.tokens_in}+{response.tokens_out} tokens, "
                f"${response.cost:.4f}, {duration_ms}ms"
            )

            return response

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            logger.error(f"LLM completion failed: {e}")

            # Log failure
            if self.cost_tracker:
                self.cost_tracker.log_usage(
                    document_id=document_id,
                    step=task,
                    model=f"{provider_name}:{model}",
                    tokens_in=0,
                    tokens_out=0,
                    duration_ms=duration_ms,
                    cost=0.0,
                    response_status="error",
                )

            raise

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about configured providers.

        Returns:
            Dictionary with provider information
        """
        available_providers = LLMFactory.get_available_providers()

        return {
            "available_providers": available_providers,
            "configured": {
                "default": f"{self.config.llm.default_provider}:{self.config.llm.default_model}",
                "advanced": f"{self.config.llm.advanced_provider}:{self.config.llm.advanced_model}",
                "free": f"{self.config.llm.free_provider}:{self.config.llm.free_model}",
            },
            "strategy": {
                "use_free_for_simple": self.config.llm.use_free_for_simple,
                "cost_threshold": self.config.llm.cost_threshold,
            },
        }
