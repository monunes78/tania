-- Inicialização do banco TanIA
-- Executado automaticamente pelo supabase/postgres na primeira inicialização

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";           -- pgvector (embeddings)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";          -- busca textual fuzzy

-- Schema principal da plataforma
CREATE SCHEMA IF NOT EXISTS tania;

-- Roles necessárias para o PostgREST (Supabase Studio)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role NOLOGIN NOINHERIT BYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticator') THEN
    CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD 'placeholder';
  END IF;
END
$$;

ALTER ROLE authenticator WITH PASSWORD :'POSTGRES_PASSWORD';

GRANT anon TO authenticator;
GRANT authenticated TO authenticator;
GRANT service_role TO authenticator;

-- Permissões no schema tania
GRANT USAGE ON SCHEMA tania TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA tania
  GRANT ALL ON TABLES TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA tania
  GRANT SELECT ON TABLES TO anon, authenticated;
