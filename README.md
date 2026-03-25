# TanIA — Plataforma Empresarial de Agentes IA

Plataforma on-premise de agentes de inteligência artificial por departamento para a TANAC.
Cada departamento possui seu próprio agente com base de conhecimento (RAG), acesso ao histórico de conversas e integração com os sistemas da empresa.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | Next.js 14+ · TailwindCSS 4 · NextAuth 5 |
| Backend | Python 3.12 · FastAPI · Celery · Redis |
| Banco de dados | PostgreSQL 15 via Supabase self-hosted · pgvector (HNSW) |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` (local, sentence-transformers) |
| LLM | LiteLLM Proxy (Claude · OpenAI · Ollama) |
| Storage | MinIO |
| Proxy | Nginx + SSL |
| Containers | Docker · docker compose v2 |
| SO | Ubuntu 24.04 LTS |

---

## Funcionalidades

- **Agentes por departamento** — cada depto tem seu agente com prompt e base de conhecimento próprios
- **RAG (Retrieval-Augmented Generation)** — documentos PDF/DOCX indexados com pgvector HNSW
- **Autenticação LDAP/AD** — login com conta corporativa, sem senhas no TanIA
- **Admin Panel** — gestão de usuários, agentes, documentos, LLMs e configurações
- **Histórico de conversas** — persistido por usuário e agente
- **Integrações** — n8n para agendamentos, Microsoft Teams, e-mail
- **Multi-LLM** — troca de modelo pelo Admin Panel sem deploy

---

## Instalação

### Pré-requisitos

- Ubuntu 22.04+ (recomendado: 24.04 LTS)
- 8 GB RAM mínimo (recomendado: 32 GB)
- 20 GB livres em disco
- Acesso root (`sudo`)

### Deploy em uma linha

```bash
git clone https://github.com/monunes78/tania.git /opt/tania
cd /opt/tania
sudo ./deploy.sh
```

O script `deploy.sh` instala Docker, configura o `.env` com geração automática de segredos, converte o certificado SSL, faz o build de todos os containers, executa as migrations e sobe o sistema completo.

Você só precisará informar:
- URL pública do sistema (ex: `https://tania.tanac.com.br`)
- Senha do serviço LDAP (`svc_tania@tanac.com.br`)
- OpenRouter API Key (opcional — pode configurar depois pelo Admin Panel)

### Certificado SSL

Coloque o arquivo `.pfx` na pasta `cert/` antes de executar o deploy:

```bash
# Do Windows, via scp:
scp "D:\Certificados\TanacWildcard2025.pfx" usuario@ip-vm:/opt/tania/cert/
```

Se nenhum `.pfx` for encontrado, o script gera um certificado auto-assinado temporário.

---

## Atualização

```bash
cd /opt/tania

# Atualização inteligente (rebuild seletivo — só o que mudou)
./update.sh

# Forçar rebuild completo
./update.sh --force-rebuild
```

---

## Estrutura do Projeto

```
backend/          FastAPI · Celery · Alembic
  src/
    api/v1/       Endpoints: auth, agents, chat, departments, documents, admin
    models/       SQLAlchemy models
    core/         Lógica de negócio, RAG, embeddings
    workers/      Celery tasks (ingestão de documentos)
frontend/         Next.js 14+ · TailwindCSS 4
  src/app/
    (auth)/       Login
    (dashboard)/  Chat · Admin Panel
nginx/            Reverse proxy · SSL
litellm-proxy/    Configuração do LiteLLM
supabase/
  migrations/     SQL migrations (pgvector HNSW, schema tania)
scripts/          Utilitários (seed, etc.)
deploy.sh         Deploy completo automatizado
update.sh         Atualização incremental inteligente
```

---

## Acesso após o Deploy

| URL | Descrição |
|---|---|
| `https://tania.tanac.com.br` | Aplicação principal |
| `http://<vm-ip>:8082` | Supabase Studio (rede interna) |
| `http://<vm-ip>:9001` | MinIO Console (rede interna) |
| `http://<vm-ip>:8000/api/docs` | API Docs FastAPI (rede interna) |

> Supabase Studio e MinIO Console ficam acessíveis apenas na rede interna ou via SSH tunnel.

---

## Comandos Úteis

```bash
# Status dos containers
docker compose ps

# Logs em tempo real
docker compose logs -f

# Migrations manuais
docker compose exec backend alembic upgrade head

# Log do último deploy
cat logs/deploy.log
```

---

## Documentação

Documentação completa no vault Obsidian do projeto:
- Arquitetura, stack, decisões técnicas
- Guia de instalação passo a passo
- Funcionalidades e roadmap
