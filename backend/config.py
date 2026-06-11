import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # App Settings
    SECRET_KEY: str = Field(default="changeme-use-strong-key-in-prod-1234567890abcdef")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # LOCAL_MODE=true uses SQLite + in-memory Qdrant (no external services needed)
    # Changed default to True since you are running locally without Docker
    LOCAL_MODE: bool = Field(default=True)

    # Databases
    # Use sqlite+aiosqlite:///./sentinel_local.db for local no-docker mode
    POSTGRES_URL: str = Field(default="postgresql+asyncpg://sentinel:sentinelpass@localhost:5432/sentinel_db")
    
    # ─── UPDATED NEO4J DEFAULTS FOR CLOUD INFRASTRUCTURE ───────────────────
    NEO4J_URI: str = Field(default="bolt://localhost:7687")
    NEO4J_USER: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="sentinelneo4j")
    
    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: int = Field(default=6333)
    REDIS_URL: str = Field(default="redis://:sentinelredis@localhost:6379/0")

    # LLM & Embeddings
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    # Swapped default from qwen3:4b to your active pre-staged model weights
    OLLAMA_MODEL: str = Field(default="mistral")
    EMBEDDING_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    FORCE_MOCK_LLM: bool = Field(default=False)

    # Search API Keys
    SERPER_API_KEY: str = Field(default="")
    OPENSANCTIONS_API_KEY: str = Field(default="")

    def get_db_url(self) -> str:
        """Return the correct DB URL based on LOCAL_MODE."""
        if self.LOCAL_MODE:
            return "sqlite+aiosqlite:///./sentinel_local.db"
        return self.POSTGRES_URL

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow" # Changed from 'ignore' to prevent Pydantic parsing drops

settings = Settings()
