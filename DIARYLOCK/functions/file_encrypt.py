"""Enkripsi file dengan ChaCha20-Poly1305 (berbeda dari algoritma teks)."""
import os
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

MAGIC = b"DLF1"
AAD = b"DIARYLOCK-FILE-v1"
SALT_SIZE = 16
NONCE_SIZE = 12
PBKDF2_ROUNDS = 300_000


def _derive_key(password: str, salt: bytes) -> bytes:
    if len(password) < 8:
        raise ValueError("Password file minimal 8 karakter.")
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS, dklen=32
    )


def encrypt_file(file_bytes: bytes, password: str) -> bytes:
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = _derive_key(password, salt)
    ciphertext = ChaCha20Poly1305(key).encrypt(nonce, file_bytes, AAD)
    return MAGIC + salt + nonce + ciphertext


def decrypt_file(encrypted_bytes: bytes, password: str) -> bytes:
    minimum = len(MAGIC) + SALT_SIZE + NONCE_SIZE + 16
    if len(encrypted_bytes) < minimum or not encrypted_bytes.startswith(MAGIC):
        raise ValueError("Format file DIARYLOCK tidak valid atau file rusak.")
    offset = len(MAGIC)
    salt = encrypted_bytes[offset:offset + SALT_SIZE]
    offset += SALT_SIZE
    nonce = encrypted_bytes[offset:offset + NONCE_SIZE]
    ciphertext = encrypted_bytes[offset + NONCE_SIZE:]
    key = _derive_key(password, salt)
    try:
        return ChaCha20Poly1305(key).decrypt(nonce, ciphertext, AAD)
    except Exception as exc:
        raise ValueError("Dekripsi gagal. Password salah atau file telah diubah.") from exc
