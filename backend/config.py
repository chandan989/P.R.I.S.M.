"""
P.R.I.S.M. Backend Configuration

Loads configuration from environment variables and .env file.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


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
