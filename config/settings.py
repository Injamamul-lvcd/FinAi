"""
Configuration management for the Financial Chatbot RAG System.

This module provides a Pydantic Settings class for loading and validating
configuration from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Required settings must be provided via environment variables or .env file.
    Optional settings have sensible defaults.
    """
    
    # Google Gemini Configuration (Required)
    google_api_key: str = Field(
        ...,
        description="Google API key for Gemini models",
        min_length=1
    )
    
    # Google Gemini Models (Optional with defaults)
    gemini_embedding_model: str = Field(
        default="models/text-embedding-004",
        description="Gemini embedding model name"
    )
    gemini_chat_model: str = Field(
        default="models/gemini-2.0-flash",
        description="Gemini chat model name"
    )
    gemini_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM generation (0.0-2.0)"
    )
    gemini_max_tokens: int = Field(
        default=500,
        ge=1,
        le=8192,
        description="Maximum tokens for LLM response"
    )
    
    # Vector Database Configuration (Optional with defaults)
    chroma_persist_dir: str = Field(
        default="./data/chroma",
        description="Directory for ChromaDB persistent storage"
    )
    chroma_collection_name: str = Field(
        default="financial_docs",
        description="ChromaDB collection name"
    )
    
    # Document Processing Configuration (Optional with defaults)
    chunk_size: int = Field(
        default=800,
        ge=100,
        le=2000,
        description="Size of text chunks in characters"
    )
    chunk_overlap: int = Field(
        default=100,
        ge=0,
        le=500,
        description="Overlap between chunks in characters"
    )
    max_file_size_mb: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum file size for uploads in MB"
    )
    
    # RAG Configuration (Optional with defaults)
    top_k_chunks: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of chunks to retrieve for context"
    )
    max_conversation_turns: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum conversation turns to keep in history"
    )
    
    # Session Storage Configuration (Optional with defaults)
    session_db_path: str = Field(
        default="./data/sessions.db",
        description="Path to SQLite database for session storage"
    )
    
    # API Configuration (Optional with defaults)
    api_host: str = Field(
        default="0.0.0.0",
        description="API host address"
    )
    api_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="API port number"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that log level is one of the standard Python logging levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"log_level must be one of {valid_levels}, got '{v}'"
            )
        return v_upper
    
    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v: int, info) -> int:
        """Validate that chunk overlap is less than chunk size."""
        # Note: chunk_size may not be available yet during validation
        # This will be checked in the post-init validation
        return v
    
    @field_validator("chroma_persist_dir", "session_db_path")
    @classmethod
    def validate_paths(cls, v: str) -> str:
        """Ensure parent directories exist for database paths."""
        # Create parent directory if it doesn't exist
        parent_dir = os.path.dirname(v)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        return v
    
    def model_post_init(self, __context) -> None:
        """Additional validation after model initialization."""
        # Validate chunk_overlap is less than chunk_size
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than "
                f"chunk_size ({self.chunk_size})"
            )
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert max file size from MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.
    
    Creates and caches the settings on first call.
    Subsequent calls return the cached instance.
    
    Returns:
        Settings: The application settings instance
        
    Raises:
        ValidationError: If required configuration is missing or invalid
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment variables.
    
    Useful for testing or when configuration changes at runtime.
    
    Returns:
        Settings: The newly loaded settings instance
    """
    global _settings
    _settings = Settings()
    return _settings
