"""
Seed inicial dos departamentos TanIA.
Uso: docker-compose exec backend python scripts/seed_departments.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.db.session import SessionLocal
from src.models.department import Department

DEPARTMENTS = [
    {"name": "DHO — Desenvolvimento Humano e Organizacional", "slug": "dho", "icon": "users"},
    {"name": "DP — Departamento Pessoal", "slug": "dp", "icon": "briefcase"},
    {"name": "TI — Tecnologia da Informação", "slug": "ti", "icon": "monitor"},
    {"name": "Produção", "slug": "producao", "icon": "factory"},
    {"name": "Logística", "slug": "logistica", "icon": "truck"},
    {"name": "Suprimentos", "slug": "suprimentos", "icon": "package"},
    {"name": "Controladoria", "slug": "controladoria", "icon": "bar-chart"},
    {"name": "Fiscal", "slug": "fiscal", "icon": "file-text"},
    {"name": "Diretoria", "slug": "diretoria", "icon": "building"},
    {"name": "Comercial", "slug": "comercial", "icon": "handshake"},
    {"name": "Marketing", "slug": "marketing", "icon": "megaphone"},
    {"name": "Endomarketing", "slug": "endomarketing", "icon": "heart"},
    {"name": "Manutenção", "slug": "manutencao", "icon": "wrench"},
    {"name": "Negócios Florestais", "slug": "negocios-florestais", "icon": "tree-pine"},
    {"name": "Financeiro", "slug": "financeiro", "icon": "dollar-sign"},
    {"name": "P&D — Pesquisa e Desenvolvimento", "slug": "pd", "icon": "flask"},
    {"name": "SGI — Sistema de Gestão Integrada", "slug": "sgi", "icon": "settings"},
    {"name": "SSO — Saúde e Segurança Ocupacional", "slug": "sso", "icon": "shield"},
    {"name": "Tanagro Silvicultura", "slug": "tanagro-silvicultura", "icon": "sprout"},
    {"name": "Tanagro Colheita", "slug": "tanagro-colheita", "icon": "scissors"},
    {"name": "Jurídico", "slug": "juridico", "icon": "scale"},
    {"name": "PMO", "slug": "pmo", "icon": "layout"},
]


def seed():
    db = SessionLocal()
    try:
        inserted = 0
        skipped = 0
        for d in DEPARTMENTS:
            exists = db.query(Department).filter(Department.slug == d["slug"]).first()
            if exists:
                skipped += 1
                continue
            dept = Department(**d)
            db.add(dept)
            inserted += 1

        db.commit()
        print(f"✅ Seed concluído: {inserted} inseridos, {skipped} já existiam.")
    except Exception as e:
        db.rollback()
        print(f"❌ Erro no seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
