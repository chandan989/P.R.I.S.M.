"""
P.R.I.S.M. Backend Configuration

Loads configuration from environment variables and .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import validator, field_validator
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""

    # Model Settings
    model_name: str = "gemma-4-26B-A4B-it-MXFP4_MOE"
    model_host: str = "localhost"
    model_port: int = 11434
    model_url: Optional[str] = None
    model_backend: str = "ollama"  # "ollama" or "llama_cpp"
    model_path: Optional[str] = None  # Path to GGUF file for llama_cpp

    # llama.cpp Settings
    n_ctx: int = 4096
    n_gpu_layers: int = 28
    n_threads: int = 4
    verbose: bool = False

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # Knowledge Base Settings
    kb_root: str = "./knowledge_base"
    kb_index_type: str = "faiss"
    kb_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    kb_embedding_device: str = "cpu"

    # Verification Settings
    verification_threshold: float = 0.75
    verification_top_k: int = 5

    # Confidence Calibration
    confidence_method: str = "conformal"
    confidence_alpha: float = 0.1

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/backend.log"

    # CORS Settings
    cors_origins: str = "*"
    cors_allow_credentials: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @field_validator('model_backend')
    @classmethod
    def validate_model_backend(cls, v):
        """Validate model backend type."""
        valid_backends = ['ollama', 'llama_cpp']
        if v not in valid_backends:
            raise ValueError(
                f"Invalid model_backend '{v}'. Must be one of: {valid_backends}"
            )
        return v

    @field_validator('model_path')
    @classmethod
    def validate_model_path(cls, v, info):
        """Validate model path when using llama_cpp backend."""
        if info.data.get('model_backend') == 'llama_cpp' and not v:
            raise ValueError(
                "model_path is required when using llama_cpp backend"
            )
        if v:
            path = Path(v)
            if not path.exists():
                raise ValueError(
                    f"model_path does not exist: {v}"
                )
        return v

    @field_validator('kb_root')
    @classmethod
    def validate_kb_root(cls, v):
        """Validate knowledge base root path."""
        path = Path(v)
        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator('verification_threshold')
    @classmethod
    def validate_verification_threshold(cls, v):
        """Validate verification threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError(
                f"verification_threshold must be between 0 and 1, got {v}"
            )
        return v

    @field_validator('confidence_alpha')
    @classmethod
    def validate_confidence_alpha(cls, v):
        """Validate confidence alpha is between 0 and 1."""
        if not 0 < v < 1:
            raise ValueError(
                f"confidence_alpha must be between 0 and 1, got {v}"
            )
        return v

    @field_validator('n_ctx', 'n_gpu_layers', 'n_threads')
    @classmethod
    def validate_positive_int(cls, v):
        """Validate integer settings are positive."""
        if v <= 0:
            raise ValueError(f"Value must be positive, got {v}")
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log_level '{v}'. Must be one of: {valid_levels}"
            )
        return v.upper()

    @field_validator('api_port', 'model_port')
    @classmethod
    def validate_port(cls, v):
        """Validate port numbers are in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError(
                f"Port must be between 1 and 65535, got {v}"
            )
        return v

    @property
    def model_endpoint(self) -> str:
        """Get the full model endpoint URL."""
        if self.model_url:
            return self.model_url
        return f"http://{self.model_host}:{self.model_port}"

    @property
    def cors_origins_list(self) -> list:
        """Parse CORS origins from string to list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
