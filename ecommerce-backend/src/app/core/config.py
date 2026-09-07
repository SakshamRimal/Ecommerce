from functools import lru_cache
from pydantic import PostgresDsn , computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    #app 
    app_name: str = "ecommerce-backend"
    app_env: str = "local" #local|stagin|Production
    debug: bool = False
    log_level: str =  "INFO"   
    
    #server 
    host: str = "0.0.0.0"
    port: int = 8000
    
    #postgres 
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ecommerce"
    
    database_pool_size: int = 10 
    database_max_overflow: int = 20
    
    #jwt 
    jwt_secret_key: str  
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    #cors
    cors_allowed_origins: list[str] = ["http://localhost:3000"]
    
    #redis 
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300
    arq_redis_url: str = "redis://localhost:6379/1"
    
    #smtp 
    mail_username: str 
    mail_password: str
    mail_from: str 
    mail_from_name: str = "YourShop"
    mail_server: str
    mail_port: int = 2525
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    
    #elastic search 
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_products_index: str = "products"
    
    
    
    @computed_field
    @property
    def database_url(self) -> str:
        return(
             f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        
    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"
    
    
@lru_cache()
def get_settings() -> Settings:
    """Cached singleton settings instance."""
    return Settings()
         
    
