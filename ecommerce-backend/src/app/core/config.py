from functools import lru_cache
from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings , SettingsConfigDict
from pathlib import Path

# project root = two levels up from this file (src/app/core/config.py -> project root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    app_name: str = "Ecommerce Backend"
    app_env: str = "local"
    debug: bool = False
    log_level: str = "info"
    
    #server
    host: str = "0.0.0.0"
    port: int = 8000
    
    #postgres
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int = 5432
    postgres_db: str
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        
    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Cache settings to avoid reloading them multiple times."""
    return Settings()