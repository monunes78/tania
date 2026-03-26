"""
Cria usuário admin local para primeiro acesso.
Executar via: docker compose exec backend python scripts/seed_admin.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from passlib.hash import bcrypt
from src.db.session import SessionLocal
from src.models.user import User


ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "TanIA@2026"  # Trocar após primeiro login
ADMIN_EMAIL = "admin@tanac.com.br"
ADMIN_DISPLAY_NAME = "Administrador TanIA"


def main():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if existing:
            print(f"[!] Usuário '{ADMIN_USERNAME}' já existe (id={existing.id}).")
            if not existing.password_hash:
                existing.password_hash = bcrypt.hash(ADMIN_PASSWORD)
                existing.is_admin = True
                db.commit()
                print(f"[✓] password_hash atualizado para login local.")
            return

        user = User(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            display_name=ADMIN_DISPLAY_NAME,
            password_hash=bcrypt.hash(ADMIN_PASSWORD),
            is_admin=True,
            ad_object_id=None,
        )
        db.add(user)
        db.commit()
        print(f"[✓] Usuário admin criado com sucesso.")
        print(f"    Login: {ADMIN_USERNAME}")
        print(f"    Senha: {ADMIN_PASSWORD}")
        print(f"    ⚠  Troque a senha após o primeiro acesso!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
