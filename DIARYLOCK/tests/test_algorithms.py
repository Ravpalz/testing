import sys
import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path
from io import BytesIO

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from functions.text_encrypt_decrypt import super_encrypt, super_decrypt, vigenere_encrypt, vigenere_decrypt
from functions.file_encrypt import encrypt_file, decrypt_file
from functions.security import hash_password, verify_password
import connection as cn
from functions.blockchain import add_asset_record, verify_chain
from functions.steganography_encryption import embed_msg, extract_msg
from PIL import Image


class TestDiarylockAlgorithms(unittest.TestCase):
    def test_vigenere_round_trip(self):
        message = "Halo Aya! Ini Catatan 123."
        encrypted = vigenere_encrypt(message, "KUNCI")
        self.assertEqual(vigenere_decrypt(encrypted, "KUNCI"), message)

    def test_super_encryption_round_trip(self):
        message = "Catatan rahasia DIARYLOCK 🌷"
        encrypted = super_encrypt(message, "KUNCI", "passphrase-aes-aman")
        self.assertNotEqual(encrypted, message)
        self.assertEqual(super_decrypt(encrypted, "KUNCI", "passphrase-aes-aman"), message)

    def test_super_encryption_rejects_wrong_key(self):
        encrypted = super_encrypt("pesan rahasia", "KUNCI", "passphrase-aes-aman")
        with self.assertRaises(ValueError):
            super_decrypt(encrypted, "KUNCI", "passphrase-salah")

    def test_file_encryption_round_trip(self):
        original = b"dokumen diarylock\x00\x01"
        encrypted = encrypt_file(original, "password-file-aman")
        self.assertEqual(decrypt_file(encrypted, "password-file-aman"), original)

    def test_password_hash_round_trip(self):
        stored = hash_password("password-ku-aman")
        self.assertNotEqual(stored, "password-ku-aman")
        self.assertTrue(verify_password("password-ku-aman", stored))
        self.assertFalse(verify_password("password-salah", stored))

    def test_blockchain_detects_changed_diary_ciphertext(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_db = Path(temp_dir) / "diarylock_test.db"
            with patch.object(cn, "DB_PATH", temporary_db):
                cn.initialize_database()
                cn.create_user("aya_test", hash_password("password-ku-aman"))
                payload = "encrypted-payload-demo"
                entry_id = cn.insert_diary_entry("aya_test", payload)
                add_asset_record("aya_test", "diary", entry_id, f"Catatan #{entry_id}", payload.encode())
                valid_before, _ = verify_chain()
                self.assertTrue(valid_before)
                cn.run_query(
                    "UPDATE diary_entries SET encrypted_payload = ? WHERE id = ?",
                    ("tampered-payload", entry_id),
                    fetch=False,
                )
                valid_after, _ = verify_chain()
                self.assertFalse(valid_after)

    def test_steganography_round_trip(self):
        image = Image.new("RGB", (300, 300), color=(140, 180, 220))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        output = embed_msg(buffer.getvalue(), "pesan rahasia")
        self.assertEqual(extract_msg(output), "pesan rahasia")


if __name__ == "__main__":
    unittest.main()
