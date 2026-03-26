#!/bin/bash
# Inicialização do banco TanIA
# Cria apenas os roles necessários para PostgREST e o schema tania.
# NÃO criar extensões aqui — a imagem supabase/postgres já faz isso internamente.
set -e

psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL

-- Schema principal da plataforma
CREATE SCHEMA IF NOT EXISTS tania;

-- Roles necessárias para o PostgREST
DO \$\$
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
    EXECUTE format('CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD %L', '$POSTGRES_PASSWORD');
  END IF;
END
\$\$;

ALTER ROLE authenticator WITH PASSWORD '$POSTGRES_PASSWORD';

GRANT anon TO authenticator;
GRANT authenticated TO authenticator;
GRANT service_role TO authenticator;

GRANT USAGE ON SCHEMA tania TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA tania GRANT ALL ON TABLES TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA tania GRANT SELECT ON TABLES TO anon, authenticated;

EOSQL
