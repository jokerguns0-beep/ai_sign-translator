"""
Application configuration.

All runtime configuration is loaded from environment variables / .env via
pydantic-settings. Nothing sensitive (API keys, etc.) is ever hard-coded.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Centralized, validated application settings.

    Every other module should import `get_config()` rather than reading
    os.environ directly, so that configuration stays in one place and is
    type-checked at startup.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Gemini ---
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # --- App ---
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    # --- Gesture sequence buffer ---
    sequence_window_min: int = 40
    sequence_window_max: int = 90
    frame_sample_rate: int = 2  # process every Nth frame to save CPU

    # --- MediaPipe ---
    mp_hands_max_num_hands: int = 2
    mp_hands_min_detection_confidence: float = 0.6
    mp_hands_min_tracking_confidence: float = 0.5
    mp_pose_min_detection_confidence: float = 0.6
    # 0 = "lite" model (~10x lighter than complexity=1) - critical on
    # memory-constrained hosting like Render's free tier (512MB).
    mp_pose_model_complexity: int = 0
    # Frame width MediaPipe actually processes - frames are downscaled to
    # this before detection, independent of the camera's native resolution.
    frame_target_width: int = 480

    # --- History ---
    history_db_path: str = "./data/history.db"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_config() -> Config:
    """Return a cached singleton Config instance."""
    return Config()
