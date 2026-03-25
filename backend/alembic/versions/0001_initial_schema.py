"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-03-25

Cria todas as tabelas do schema tania com pgvector.
As extensões (vector, uuid-ossp) e o schema são criados no env.py antes desta migration.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("ad_object_id", sa.String(256), nullable=False, unique=True),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("email", sa.String(256), nullable=False),
        sa.Column("display_name", sa.String(256)),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_login", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        schema="tania",
    )

    # ── departments ───────────────────────────────────────────────────────────
    op.create_table(
        "departments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("slug", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.String(500)),
        sa.Column("icon", sa.String(50)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        schema="tania",
    )

    # ── department_access ─────────────────────────────────────────────────────
    op.create_table(
        "department_access",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("tania.departments.id"), nullable=False),
        sa.Column("ad_group_dn", sa.String(500), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        schema="tania",
    )

    # ── llm_configurations ────────────────────────────────────────────────────
    op.create_table(
        "llm_configurations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("tania.users.id"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("api_key_enc", sa.Text()),
        sa.Column("api_base_url", sa.String(500)),
        sa.Column("extra_params", sa.Text()),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        schema="tania",
    )

    # ── agents ────────────────────────────────────────────────────────────────
    op.create_table(
        "agents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("tania.departments.id"), nullable=False),
        sa.Column("llm_config_id", UUID(as_uuid=True), sa.ForeignKey("tania.llm_configurations.id"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500)),
        sa.Column("system_prompt", sa.Text()),
        sa.Column("temperature", sa.Numeric(3, 2), server_default="0.1"),
        sa.Column("max_context_chunks", sa.Integer(), server_default="5"),
        sa.Column("enable_sql_access", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()")),
        schema="tania",
    )

    # ── agent_prompt_history ──────────────────────────────────────────────────
    op.create_table(
        "agent_prompt_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("tania.agents.id"), nullable=False),
        sa.Column("updated_by", UUID(as_uuid=True), sa.ForeignKey("tania.users.id"), nullable=True),
        sa.Column("system_prompt", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        schema="tania",
    )

    # ── documents ─────────────────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("tania.agents.id"), nullable=False),
        sa.Column("uploaded_by", UUID(as_uuid=True), sa.ForeignKey("tania.users.id"), nullable=True),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("original_name", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column("classification", sa.String(20), nullable=False, server_default="public"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text()),
        sa.Column("minio_path", sa.String(1000), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger()),
        sa.Column("chunk_count", sa.Integer(), server_default="0"),
        sa.Column("expires_at", sa.DateTime()),
        sa.Column("indexed_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        schema="tania",
    )

    # ── document_access ───────────────────────────────────────────────────────
    op.create_table(
        "document_access",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("tania.documents.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("tania.users.id"), nullable=False),
        sa.Column("granted_by", UUID(as_uuid=True), sa.ForeignKey("tania.users.id"), nullable=True),
        sa.Column("granted_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        schema="tania",
    )

    # ── document_chunks (pgvector) ────────────────────────────────────────────
    op.create_table(
        "document_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("tania.documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("tania.agents.id"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text()),  # placeholder — alterado abaixo via SQL
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        schema="tania",
    )

    # Alterar coluna embedding para tipo vector(384) do pgvector
    op.execute("ALTER TABLE tania.document_chunks ALTER COLUMN embedding TYPE vector(384) USING NULL::vector(384)")

    # Índice HNSW para busca ANN por similaridade coseno
    op.execute(
        """
        CREATE INDEX ix_document_chunks_embedding_hnsw
        ON tania.document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )

    # ── conversations ─────────────────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("tania.users.id"), nullable=False),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("tania.agents.id"), nullable=False),
        sa.Column("title", sa.String(200)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()")),
        schema="tania",
    )

    # ── messages ──────────────────────────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("tania.conversations.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("rag_chunks_used", sa.Text()),
        sa.Column("model_used", sa.String(100)),
        sa.Column("tokens_input", sa.Integer()),
        sa.Column("tokens_output", sa.Integer()),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        schema="tania",
    )

    # ── schedules ─────────────────────────────────────────────────────────────
    op.create_table(
        "schedules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("tania.users.id"), nullable=False),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("tania.agents.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("task_payload", sa.Text(), nullable=False),
        sa.Column("cron_expression", sa.String(50), nullable=False),
        sa.Column("channels", sa.String(500), nullable=False, server_default='["chat"]'),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_run", sa.DateTime()),
        sa.Column("next_run", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        schema="tania",
    )

    # ── db_connections ────────────────────────────────────────────────────────
    op.create_table(
        "db_connections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("tania.agents.id"), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("db_type", sa.String(20), nullable=False, server_default="sqlserver"),
        sa.Column("server_host", sa.String(200), nullable=False),
        sa.Column("server_port", sa.String(10), server_default="1433"),
        sa.Column("database_name", sa.String(100), nullable=False),
        sa.Column("allowed_schemas", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("credentials_enc", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        schema="tania",
    )

    # ── audit_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("tania.users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50)),
        sa.Column("entity_id", sa.String(100)),
        sa.Column("details", sa.Text()),
        sa.Column("ip_address", sa.String(50)),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        schema="tania",
    )


def downgrade() -> None:
    op.drop_table("audit_logs", schema="tania")
    op.drop_table("db_connections", schema="tania")
    op.drop_table("schedules", schema="tania")
    op.drop_table("messages", schema="tania")
    op.drop_table("conversations", schema="tania")
    op.execute("DROP INDEX IF EXISTS tania.ix_document_chunks_embedding_hnsw")
    op.drop_table("document_chunks", schema="tania")
    op.drop_table("document_access", schema="tania")
    op.drop_table("documents", schema="tania")
    op.drop_table("agent_prompt_history", schema="tania")
    op.drop_table("agents", schema="tania")
    op.drop_table("llm_configurations", schema="tania")
    op.drop_table("department_access", schema="tania")
    op.drop_table("departments", schema="tania")
    op.drop_table("users", schema="tania")
