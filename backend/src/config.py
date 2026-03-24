from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Ambiente ─────────────────────────────────────
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "info"

    # ─── SQL Server ───────────────────────────────────
    SQL_SERVER_HOST: str
    SQL_SERVER_PORT: int = 1433
    SQL_SERVER_DB: str
    SQL_SERVER_USER: str
    SQL_SERVER_PASSWORD: str

    @property
    def SQL_CONNECTION_STRING(self) -> str:
        return (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={self.SQL_SERVER_HOST},{self.SQL_SERVER_PORT};"
            f"DATABASE={self.SQL_SERVER_DB};"
            f"UID={self.SQL_SERVER_USER};"
            f"PWD={self.SQL_SERVER_PASSWORD};"
            f"TrustServerCertificate=yes;"
        )

    # ─── LDAP / AD ────────────────────────────────────
    LDAP_SERVER: str
    LDAP_DOMAIN: str
    LDAP_BASE_DN: str
    LDAP_BIND_USER: str
    LDAP_BIND_PASSWORD: str

    # ─── JWT ──────────────────────────────────────────
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8
    REFRESH_TOKEN_EXPIRE_HOURS: int = 24

    # ─── Criptografia ─────────────────────────────────
    ENCRYPTION_KEY: str

    # ─── Qdrant ───────────────────────────────────────
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333

    # ─── Redis ────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ─── MinIO ────────────────────────────────────────
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "tania-documents"
    MINIO_SECURE: bool = False

    # ─── LiteLLM ──────────────────────────────────────
    LITELLM_PROXY_URL: str = "http://litellm:4000"
    LITELLM_MASTER_KEY: str

    # ─── n8n ──────────────────────────────────────────
    N8N_BASE_URL: str = ""
    N8N_WEBHOOK_SECRET: str = ""
    N8N_API_KEY: str = ""

    # ─── Teams ────────────────────────────────────────
    TEAMS_TENANT_ID: str = ""
    TEAMS_CLIENT_ID: str = ""
    TEAMS_CLIENT_SECRET: str = ""

    # ─── SMTP ─────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "TanIA <tania@tanac.com.br>"

    # ─── CORS ─────────────────────────────────────────
    @property
    def CORS_ORIGINS(self) -> List[str]:
        return ["https://tania.tanac.com.br"] if self.ENVIRONMENT == "production" \
            else ["http://localhost:3000", "http://localhost"]


settings = Settings()
