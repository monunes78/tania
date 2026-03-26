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

    # ─── PostgreSQL / Supabase ────────────────────────
    POSTGRES_HOST: str = "supabase-db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ─── LDAP / AD (opcional — vazio = login só local) ─
    LDAP_SERVER: str = ""
    LDAP_DOMAIN: str = ""
    LDAP_BASE_DN: str = ""
    LDAP_BIND_USER: str = ""
    LDAP_BIND_PASSWORD: str = ""

    # ─── JWT ──────────────────────────────────────────
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8
    REFRESH_TOKEN_EXPIRE_HOURS: int = 24

    # ─── Criptografia ─────────────────────────────────
    ENCRYPTION_KEY: str

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
