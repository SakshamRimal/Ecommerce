from functools import lru_cache
from pydantic import PostgresDsn , computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    #app 
    app_name: str = "ecommerce-backend"
    app_env: str = "local" #local|stagin|Production
    debug: bool = False
    log_lovel: str =  "INFO"   
    
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
         
    
