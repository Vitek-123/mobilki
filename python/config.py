"""
Конфигурация приложения
"""
import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Настройки приложения"""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:root@localhost:3306/project_mobilki_aviasales"
    )
    
    # Redis
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "true").lower() in ("true", "1", "yes")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "10800"))  # 3 часа
    
    # JWT
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "your-secret-key-change-this-in-production-min-32-chars"
    )
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # CORS
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:8000,http://127.0.0.1:8000"
        ).split(",")
    ]
    
    # API
    API_TITLE: str = "Mobil Api"
    API_VERSION: str = "0.10.4"
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100
    
    # External Services
    YANDEX_MARKET_TIMEOUT: int = 60  # секунд
    YANDEX_MARKET_HEADLESS: bool = True
    
    # Yandex Market OAuth API
    YANDEX_OAUTH_TOKEN: Optional[str] = os.getenv("YANDEX_OAUTH_TOKEN")
    YANDEX_MARKET_CAMPAIGN_ID: Optional[str] = os.getenv("YANDEX_MARKET_CAMPAIGN_ID")


settings = Settings()

