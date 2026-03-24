"""
Criptografia AES-256-GCM para armazenar API keys e credenciais no banco.
"""
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from src.config import settings


def _get_key() -> bytes:
    key = base64.b64decode(settings.ENCRYPTION_KEY)
    if len(key) not in (16, 24, 32):
        raise ValueError("ENCRYPTION_KEY deve ser uma chave AES de 128, 192 ou 256 bits em base64.")
    return key


def encrypt(plaintext: str) -> str:
    """Criptografa string e retorna base64(nonce + ciphertext)."""
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()


def decrypt(ciphertext_b64: str) -> str:
    """Descriptografa string criptografada pelo encrypt()."""
    key = _get_key()
    aesgcm = AESGCM(key)
    data = base64.b64decode(ciphertext_b64)
    nonce, ct = data[:12], data[12:]
    return aesgcm.decrypt(nonce, ct, None).decode()
