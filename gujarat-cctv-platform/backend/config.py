from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cctv_intel"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    JWT_SECRET: str = "super_secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 1440
    
    DETECTION_CONFIDENCE_THRESHOLD: float = 0.6
    ANPR_CONFIDENCE_THRESHOLD: float = 0.8
    FRAME_SAMPLE_RATE: int = 5
    
    RECORDINGS_PATH: str = "../data/recordings"
    MODELS_PATH: str = "ai/weights"
    
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = ["*"]
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
