from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    """Centralized configuration for the Gujarat CCTV Intelligence Platform."""

    DATABASE_URL: str = "postgresql+asyncpg://cctv_user:cctv_pass_2026@localhost:5432/cctv_platform"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    JWT_SECRET: str = "REDACTED_INSECURE_JWT_SECRET"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 480

    # AI Pipeline
    DETECTION_CONFIDENCE_THRESHOLD: float = 0.5
    ANPR_CONFIDENCE_THRESHOLD: float = 0.6
    FRAME_SAMPLE_RATE: int = 2
    TRACKING_IOU_THRESHOLD: float = 0.3
    REID_SIMILARITY_THRESHOLD: float = 0.75

    # Paths
    RECORDINGS_PATH: str = "./data/recordings"
    MODELS_PATH: str = "./data/models"
    FRAMES_OUTPUT_PATH: str = "./data/frames"

    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

