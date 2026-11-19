from functools import lru_cache
from pydantic import computed_field
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
    # Slowapi storage. Leave unset for per-process memory; set to e.g.
    # "redis://localhost:6379/2" so rate limits are shared across workers.
    rate_limit_storage_uri: str | None = None
    
    #smtp 
    mail_username: str 
    mail_password: str
    mail_from: str 
    mail_from_name: str = "YourShop"
    mail_server: str
    mail_port: int = 587
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    
    #elastic search 
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_products_index: str = "products"

    #minio object storage
    minio_endpoint: str = "http://localhost:9000"
    minio_public_url: str = "http://localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "product-images"
    minio_region: str = "us-east-1"
    
    #opentelemetry
    otel_exporter_endpoint: str = "localhost:4317"
    
    #llm providers (priority: 1. Gemini Free -> 2. Grok/Groq Free -> 3. OpenAI)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"

    grok_api_key: str | None = None
    groq_api_key: str | None = None
    grok_model: str = "llama-3.3-70b-versatile"
    grok_base_url: str | None = None

    #openai (tertiary fallback)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 800
    chat_max_history_messages: int = 20
    chat_max_tool_iterations: int = 5
    
    
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
         
    
