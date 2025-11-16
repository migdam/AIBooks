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

    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    default_model: str = Field(default="gpt-4o-mini")
    metadata_model: str = Field(default="gpt-4o-mini")
    cleanup_model: str = Field(default="gpt-4o-mini")
    agent_model: str = Field(default="gpt-4o")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, ge=1)


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
                openai_api_key=os.getenv("OPENAI_API_KEY", ""),
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                default_model=os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini"),
                metadata_model=os.getenv("METADATA_LLM_MODEL", "gpt-4o-mini"),
                cleanup_model=os.getenv("CLEANUP_LLM_MODEL", "gpt-4o-mini"),
                agent_model=os.getenv("AGENT_LLM_MODEL", "gpt-4o"),
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
