"""USB dongle prototipe berbasis file token pada flash drive.

Ini simulasi dongle untuk tugas: token file masih dapat disalin, sehingga
bukan pengganti hardware security key yang memiliki secure element.
"""
from pathlib import Path
import hashlib
import os
import string
import secrets

DONGLE_RELATIVE_PATH = Path("DIARYLOCK") / "diarylock.key"


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_dongle(drive_root: str) -> tuple[str, str]:
    root = Path(drive_root).expanduser()
    if not root.exists() or not root.is_dir():
        raise ValueError("Lokasi USB tidak ditemukan atau bukan folder/drive.")
    folder = root / "DIARYLOCK"
    folder.mkdir(parents=True, exist_ok=True)
    token_path = folder / "diarylock.key"
    if token_path.exists():
        raise FileExistsError("Token sudah ada. Gunakan flashdisk kosong atau hapus token lama terlebih dahulu.")
    token = secrets.token_urlsafe(48)
    with token_path.open("x", encoding="utf-8") as file:
        file.write(token)
    try:
        os.chmod(token_path, 0o600)
    except OSError:
        pass
    return str(token_path), _token_hash(token)


def verify_dongle_file(token_path: str, expected_hash: str) -> bool:
    try:
        token = Path(token_path).expanduser().read_text(encoding="utf-8").strip()
        return bool(token) and secrets.compare_digest(_token_hash(token), expected_hash)
    except (OSError, UnicodeError, TypeError):
        return False


def _candidate_paths() -> list[Path]:
    candidates: list[Path] = []
    if os.name == "nt":
        try:
            import ctypes
            mask = ctypes.windll.kernel32.GetLogicalDrives()
            for index, letter in enumerate(string.ascii_uppercase):
                if mask & (1 << index):
                    root = f"{letter}:\\"
                    drive_type = ctypes.windll.kernel32.GetDriveTypeW(root)
                    # 2=removable, 3=fixed. Periksa keduanya agar flash drive
                    # yang dilaporkan Windows sebagai fixed tetap terdeteksi.
                    if drive_type in (2, 3):
                        candidates.append(Path(root) / DONGLE_RELATIVE_PATH)
        except Exception:
            pass
    else:
        bases = [Path("/media") / str(os.getenv("USER", "")), Path("/run/media") / str(os.getenv("USER", "")), Path("/Volumes")]
        for base in bases:
            if base.exists():
                try:
                    for mount in base.iterdir():
                        candidates.append(mount / DONGLE_RELATIVE_PATH)
                except OSError:
                    continue
    return candidates


def detect_dongle(expected_hash: str) -> str | None:
    for candidate in _candidate_paths():
        if verify_dongle_file(str(candidate), expected_hash):
            return str(candidate)
    return None
