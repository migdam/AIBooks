"""Configuration management for AIBooks."""

import os
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMConfig(BaseModel):
    """LLM configuration settings."""

    # API Keys
    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    groq_api_key: str = Field(default="")

    # Provider selection (openai, anthropic, ollama, groq)
    default_provider: str = Field(default="openai")
    advanced_provider: str = Field(default="openai")  # For complex tasks
    free_provider: str = Field(default="ollama")  # For simple tasks

    # Model selection by task type
    default_model: str = Field(default="gpt-4o-mini")
    metadata_model: str = Field(default="gpt-4o-mini")
    cleanup_model: str = Field(default="gpt-4o-mini")
    agent_model: str = Field(default="gpt-4o")

    # Free models (Ollama local models)
    free_model: str = Field(default="llama3.1:8b")  # Local Ollama model
    simple_task_model: str = Field(default="llama3.1:8b")  # For simple tasks

    # Advanced models for complex tasks
    advanced_model: str = Field(default="gpt-4o")  # Or claude-3-5-sonnet

    # Ollama configuration
    ollama_base_url: str = Field(default="http://localhost:11434")

    # Model parameters
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, ge=1)

    # Strategy: when to use free vs paid
    use_free_for_simple: bool = Field(default=True)  # Use free models for simple tasks
    cost_threshold: float = Field(default=0.01)  # Switch to free if cost > threshold


class CostConfig(BaseModel):
    """Cost control configuration."""

    daily_cost_cap: float = Field(default=10.0, ge=0.0)
    cost_warning_threshold: float = Field(default=5.0, ge=0.0)
    enable_cost_tracking: bool = Field(default=True)


class ProcessingConfig(BaseModel):
    """Processing configuration."""

    max_workers: int = Field(default=4, ge=1, le=32)
    batch_size: int = Field(default=10, ge=1)
    enable_ocr: bool = Field(default=True)
    enable_docling_vision: bool = Field(default=True)


class PathConfig(BaseModel):
    """Path configuration."""

    database_path: Path = Field(default=Path("./aibooks.db"))
    output_dir: Path = Field(default=Path("./output"))
    temp_dir: Path = Field(default=Path("./data/temp"))
    log_dir: Path = Field(default=Path("./logs"))
    calibre_path: Path = Field(default=Path("/usr/bin/ebook-meta"))

    @field_validator("database_path", "output_dir", "temp_dir", "log_dir", mode="before")
    def resolve_path(cls, v):
        """Resolve path to absolute."""
        if isinstance(v, str):
            return Path(v).resolve()
        return v.resolve() if isinstance(v, Path) else v


class LoggingConfig(BaseModel):
    """Logging configuration."""

    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/aibooks.log")
    enable_console_log: bool = Field(default=True)
    enable_file_log: bool = Field(default=True)


class Config(BaseModel):
    """Main configuration for AIBooks."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    cost: CostConfig = Field(default_factory=CostConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    paths: PathConfig = Field(default_factory=PathConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            llm=LLMConfig(
                # API Keys
                openai_api_key=os.getenv("OPENAI_API_KEY", ""),
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                groq_api_key=os.getenv("GROQ_API_KEY", ""),

                # Providers
                default_provider=os.getenv("DEFAULT_PROVIDER", "openai"),
                advanced_provider=os.getenv("ADVANCED_PROVIDER", "openai"),
                free_provider=os.getenv("FREE_PROVIDER", "ollama"),

                # Models
                default_model=os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini"),
                metadata_model=os.getenv("METADATA_LLM_MODEL", "gpt-4o-mini"),
                cleanup_model=os.getenv("CLEANUP_LLM_MODEL", "gpt-4o-mini"),
                agent_model=os.getenv("AGENT_LLM_MODEL", "gpt-4o"),
                free_model=os.getenv("FREE_LLM_MODEL", "llama3.1:8b"),
                simple_task_model=os.getenv("SIMPLE_TASK_MODEL", "llama3.1:8b"),
                advanced_model=os.getenv("ADVANCED_LLM_MODEL", "gpt-4o"),

                # Ollama config
                ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),

                # Strategy
                use_free_for_simple=os.getenv("USE_FREE_FOR_SIMPLE", "true").lower() == "true",
                cost_threshold=float(os.getenv("COST_THRESHOLD", "0.01")),
            ),
            cost=CostConfig(
                daily_cost_cap=float(os.getenv("DAILY_COST_CAP", "10.0")),
                cost_warning_threshold=float(os.getenv("COST_WARNING_THRESHOLD", "5.0")),
            ),
            processing=ProcessingConfig(
                max_workers=int(os.getenv("MAX_WORKERS", "4")),
                batch_size=int(os.getenv("BATCH_SIZE", "10")),
                enable_ocr=os.getenv("DOCLING_OCR_ENABLED", "true").lower() == "true",
                enable_docling_vision=os.getenv("DOCLING_VISION_ENABLED", "true").lower() == "true",
            ),
            paths=PathConfig(
                database_path=Path(os.getenv("DATABASE_PATH", "./aibooks.db")),
                output_dir=Path(os.getenv("OUTPUT_DIR", "./output")),
                temp_dir=Path(os.getenv("TEMP_DIR", "./data/temp")),
                calibre_path=Path(os.getenv("CALIBRE_PATH", "/usr/bin/ebook-meta")),
            ),
            logging=LoggingConfig(
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                log_file=os.getenv("LOG_FILE", "logs/aibooks.log"),
            ),
        )

    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        self.paths.output_dir.mkdir(parents=True, exist_ok=True)
        self.paths.temp_dir.mkdir(parents=True, exist_ok=True)
        self.paths.log_dir.mkdir(parents=True, exist_ok=True)

        # Create output subdirectories
        (self.paths.output_dir / "txt").mkdir(exist_ok=True)
        (self.paths.output_dir / "md").mkdir(exist_ok=True)
        (self.paths.output_dir / "json").mkdir(exist_ok=True)


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
        _config.ensure_directories()
    return _config
