"""Steganografi LSB pada gambar PNG. Pesan sebaiknya dienkripsi dahulu."""
from io import BytesIO
from PIL import Image
import numpy as np


def embed_msg(image_bytes: bytes, message: str) -> bytes:
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    pixels = np.array(image, dtype=np.uint8)
    flat = pixels.reshape(-1)
    message_bytes = message.encode("utf-8")
    if len(message_bytes) >= 2**32:
        raise ValueError("Pesan terlalu besar.")
    payload = len(message_bytes).to_bytes(4, "big") + message_bytes
    bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
    if bits.size > flat.size:
        capacity = max(0, (flat.size // 8) - 4)
        raise ValueError(f"Gambar terlalu kecil. Kapasitas pesan sekitar {capacity} byte.")
    flat[:bits.size] = (flat[:bits.size] & 0xFE) | bits
    output = BytesIO()
    Image.fromarray(pixels, mode="RGB").save(output, format="PNG")
    return output.getvalue()


def extract_msg(image_bytes: bytes) -> str:
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    flat = np.array(image, dtype=np.uint8).reshape(-1)
    if flat.size < 32:
        raise ValueError("Gambar tidak memuat data yang cukup.")
    length_bits = flat[:32] & 1
    length = int.from_bytes(np.packbits(length_bits).tobytes(), "big")
    total_bits = 32 + length * 8
    if length <= 0 or total_bits > flat.size:
        raise ValueError("Pesan tersembunyi tidak ditemukan atau gambar tidak valid.")
    data_bits = flat[32:total_bits] & 1
    data = np.packbits(data_bits).tobytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Pesan tersembunyi rusak atau bukan format DIARYLOCK.") from exc
