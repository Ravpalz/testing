"""Super enkripsi: Vigenere (klasik) lalu AES-256-GCM (modern)."""
import base64
import json
import os
import string

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

MAGIC = b"DIARYLOCK-TEXT-v1"
PBKDF2_ROUNDS = 250_000
ALPHABET = string.ascii_uppercase


def _clean_key(key: str) -> str:
    cleaned = "".join(ch for ch in key.upper() if ch in ALPHABET)
    if not cleaned:
        raise ValueError("Kunci Vigenere harus memiliki minimal satu huruf A-Z.")
    return cleaned


def vigenere_encrypt(text: str, key: str) -> str:
    key = _clean_key(key)
    result = []
    key_index = 0
    for char in text:
        if char.isascii() and char.isalpha():
            base = ord("A") if char.isupper() else ord("a")
            shift = ord(key[key_index % len(key)]) - ord("A")
            result.append(chr((ord(char) - base + shift) % 26 + base))
            key_index += 1
        else:
            result.append(char)
    return "".join(result)


def vigenere_decrypt(text: str, key: str) -> str:
    key = _clean_key(key)
    result = []
    key_index = 0
    for char in text:
        if char.isascii() and char.isalpha():
            base = ord("A") if char.isupper() else ord("a")
            shift = ord(key[key_index % len(key)]) - ord("A")
            result.append(chr((ord(char) - base - shift) % 26 + base))
            key_index += 1
        else:
            result.append(char)
    return "".join(result)


def _derive_aes_key(passphrase: str, salt: bytes) -> bytes:
    if len(passphrase) < 8:
        raise ValueError("Kunci AES minimal 8 karakter.")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ROUNDS,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def super_encrypt(plaintext: str, vigenere_key: str, aes_passphrase: str) -> str:
    """Enkripsi Vigenere -> AES-GCM; hasil berupa token Base64 URL-safe."""
    if not isinstance(plaintext, str):
        raise TypeError("Plaintext harus berupa teks.")
    after_vigenere = vigenere_encrypt(plaintext, vigenere_key).encode("utf-8")
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _derive_aes_key(aes_passphrase, salt)
    # AESGCM menghasilkan ciphertext yang sudah menyertakan authentication tag.
    ciphertext_and_tag = AESGCM(key).encrypt(nonce, after_vigenere, MAGIC)
    payload = {
        "version": 1,
        "salt": base64.b64encode(salt).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext_and_tag).decode("ascii"),
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def super_decrypt(encrypted_payload: str, vigenere_key: str, aes_passphrase: str) -> str:
    """Dekripsi AES-GCM -> Vigenere; kunci yang salah akan ditolak."""
    try:
        raw = base64.urlsafe_b64decode(encrypted_payload.encode("ascii"))
        payload = json.loads(raw.decode("utf-8"))
        if payload.get("version") != 1:
            raise ValueError("Versi ciphertext tidak dikenali.")
        salt = base64.b64decode(payload["salt"])
        nonce = base64.b64decode(payload["nonce"])
        ciphertext_and_tag = base64.b64decode(payload["ciphertext"])
        key = _derive_aes_key(aes_passphrase, salt)
        after_aes = AESGCM(key).decrypt(nonce, ciphertext_and_tag, MAGIC)
        return vigenere_decrypt(after_aes.decode("utf-8"), vigenere_key)
    except Exception as exc:
        if isinstance(exc, ValueError) and str(exc).startswith("Kunci AES"):
            raise
        raise ValueError("Dekripsi gagal. Periksa ciphertext dan kedua kunci.") from exc
