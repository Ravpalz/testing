"""Face verification prototipe menggunakan OpenCV LBPH.

Memerlukan opencv-contrib-python karena modul cv2.face tidak ada pada paket
opencv-python standar. Gambar wajah disimpan lokal di data/faces/<username>.
"""
from pathlib import Path
import re
import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
FACES_DIR = BASE_DIR / "data" / "faces"
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


def _face_crop(image_bytes: bytes) -> np.ndarray:
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Gambar tidak dapat dibaca.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    detector = cv2.CascadeClassifier(CASCADE_PATH)
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(70, 70))
    if len(faces) == 0:
        raise ValueError("Wajah tidak terdeteksi. Ambil foto dengan wajah menghadap kamera dan pencahayaan cukup.")
    x, y, width, height = max(faces, key=lambda item: item[2] * item[3])
    crop = gray[y:y + height, x:x + width]
    crop = cv2.equalizeHist(crop)
    return cv2.resize(crop, (200, 200), interpolation=cv2.INTER_AREA)


def save_face_samples(username: str, image_samples: list[bytes]) -> int:
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", username):
        raise ValueError("Username hanya boleh berisi huruf, angka, titik, garis bawah, atau minus (3–30 karakter).")
    if len(image_samples) < 3:
        raise ValueError("Daftarkan minimal 3 sampel foto wajah.")
    if not hasattr(cv2, "face") or not hasattr(cv2.face, "LBPHFaceRecognizer_create"):
        raise RuntimeError("OpenCV contrib belum terpasang. Jalankan pip install opencv-contrib-python.")
    user_dir = FACES_DIR / username
    user_dir.mkdir(parents=True, exist_ok=True)
    # Simpan crop grayscale agar data yang dipakai saat login konsisten.
    saved = 0
    for index, image_bytes in enumerate(image_samples, start=1):
        face = _face_crop(image_bytes)
        target = user_dir / f"sample_{index}.png"
        if not cv2.imwrite(str(target), face):
            raise OSError("Gagal menyimpan sampel wajah.")
        saved += 1
    return saved


def verify_face(username: str, image_bytes: bytes, threshold: float = 85.0) -> tuple[bool, str]:
    if not hasattr(cv2, "face") or not hasattr(cv2.face, "LBPHFaceRecognizer_create"):
        return False, "OpenCV contrib belum terpasang. Jalankan pip install -r requirements.txt."
    user_dir = FACES_DIR / username
    sample_paths = sorted(user_dir.glob("sample_*.png")) if user_dir.exists() else []
    if len(sample_paths) < 3:
        return False, "Data biometrik belum lengkap. Daftarkan ulang minimal 3 sampel wajah."
    try:
        training_faces = [cv2.imread(str(path), cv2.IMREAD_GRAYSCALE) for path in sample_paths]
        training_faces = [face for face in training_faces if face is not None]
        if len(training_faces) < 3:
            return False, "Sampel wajah tidak dapat dibaca."
        labels = np.array([1] * len(training_faces), dtype=np.int32)
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(training_faces, labels)
        query_face = _face_crop(image_bytes)
        predicted_label, confidence = recognizer.predict(query_face)
        passed = predicted_label == 1 and confidence <= threshold
        return passed, f"Nilai kecocokan LBPH: {confidence:.2f} (ambang {threshold:.0f})."
    except (ValueError, cv2.error) as exc:
        return False, str(exc)
