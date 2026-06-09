from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Food Buddy"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    database_url: str = "sqlite:///./database/restaurant.db"
    data_dir: str = "./data"
    cors_origins: str = ""
    host: str = "0.0.0.0"
    port: int = 8080
    tax_rate: float = 0.05
    order_id_prefix: str = "ORD"

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_currency: str = "INR"
    razorpay_company_name: str = ""
    razorpay_checkout_config_id: str = ""

    geocode_user_agent: str = "FoodBuddy/1.0"
    geocode_fallback_lat: float = 17.435886
    geocode_fallback_lng: float = 78.3618

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in ("production", "staging")

    @property
    def razorpay_enabled(self) -> bool:
        return bool(self.razorpay_key_id and self.razorpay_key_secret)

    @property
    def razorpay_display_name(self) -> str:
        return self.razorpay_company_name.strip() or self.app_name

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent

    @property
    def data_path(self) -> Path:
        path = Path(self.data_dir)
        if not path.is_absolute():
            path = self.base_dir / path
        return path

    @property
    def database_path(self) -> Path:
        if self.database_url.startswith("sqlite:///"):
            rel = self.database_url.replace("sqlite:///", "")
            path = Path(rel)
            if not path.is_absolute():
                path = self.base_dir / path
            return path.parent
        return self.base_dir / "database"

    @property
    def cors_origin_list(self) -> List[str]:
        if self.cors_origins.strip():
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if self.is_production:
            return []
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    @model_validator(mode="after")
    def validate_environment(self) -> "Settings":
        if self.is_production:
            if not self.secret_key or len(self.secret_key) < 32:
                raise ValueError(
                    "SECRET_KEY must be set to a random string of at least 32 characters in production"
                )
            if not self.cors_origins.strip():
                raise ValueError("CORS_ORIGINS must be set in production (comma-separated frontend URLs)")
        elif not self.secret_key:
            object.__setattr__(self, "secret_key", "dev-insecure-key-change-before-production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
