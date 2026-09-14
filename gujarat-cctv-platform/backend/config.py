from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    """Centralized configuration for the Gujarat CCTV Intelligence Platform."""

    DATABASE_URL: str = "postgresql+asyncpg://cctv_user:cctv_pass_2026@localhost:5432/cctv_platform"
    ALLOW_SQLITE_FALLBACK: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    JWT_SECRET: str = "c7d2e8b9a1f43506849e32a10d9487c6b5e4f3a210987654321fedcba0987654"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 480

    # AI Pipeline
    DETECTION_CONFIDENCE_THRESHOLD: float = 0.5
    ANPR_CONFIDENCE_THRESHOLD: float = 0.6
    FRAME_SAMPLE_RATE: int = 2
    TRACKING_IOU_THRESHOLD: float = 0.3
    REID_SIMILARITY_THRESHOLD: float = 0.75
    MAX_ACTIVE_STREAMS: int = 30

    # Speed Limits & Feasibility Gates (km/h)
    STATUTORY_HIGHWAY_SPEED_LIMIT_KMH: float = 120.0  # Gujarat statutory highway limit; triggers speed anomaly
    PHYSICAL_MAX_VEHICLE_SPEED_KMH: float = 150.0      # Hard physical impossibility gate for vehicles; rejects association
    PHYSICAL_MAX_PEDESTRIAN_SPEED_KMH: float = 20.0    # Hard physical impossibility gate for pedestrians (sprint limit); rejects association

    # Paths
    RECORDINGS_PATH: str = "./data/recordings"
    MODELS_PATH: str = "./data/models"
    FRAMES_OUTPUT_PATH: str = "./data/frames"
    
    GATEWAY_URL: str = "http://gateway"

    # Sentinel Camera Grid
    SENTINEL_EMAIL: str = "smitchova@gmail.com"
    SENTINEL_PASSWORD: str = ""
    SENTINEL_CDN_HOST: str = "https://cctv.corp8.cloud"
    SENTINEL_RTSP_IP: str = "103.250.160.189"
    SENTINEL_RTSP_PORT: int = 8554
    SENTINEL_WHEP_PORT: int = 8889

    @property
    def sentinel_encoded_email(self) -> str:
        from urllib.parse import quote
        return quote(self.SENTINEL_EMAIL, safe="")

    def get_rtsp_url(self, cam_id: str) -> str:
        return f"rtsp://{self.sentinel_encoded_email}:{self.SENTINEL_PASSWORD}@{self.SENTINEL_RTSP_IP}:{self.SENTINEL_RTSP_PORT}/stream/{cam_id}"

    def get_hls_url(self, cam_id: str) -> str:
        return f"{self.SENTINEL_CDN_HOST}/{cam_id}/index.m3u8"

    def get_webrtc_url(self, cam_id: str) -> str:
        return f"http://{self.sentinel_encoded_email}:{self.SENTINEL_PASSWORD}@{self.SENTINEL_RTSP_IP}:{self.SENTINEL_WHEP_PORT}/stream/{cam_id}/whep"

    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:3001"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

