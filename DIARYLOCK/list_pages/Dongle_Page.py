import streamlit as st
import connection as cn
from functions.dongle import create_dongle, verify_dongle_file


def setup_dongle():
    st.title("🔑 Setup USB Dongle DIARYLOCK")
    st.write("Sebelum registrasi dan login, buat token akses pada flashdisk yang akan digunakan sebagai dongle.")
    st.warning(
        "Masukkan lokasi/root flashdisk, misalnya `E:\\` pada Windows. "
        "Program akan membuat folder `DIARYLOCK` dan file `diarylock.key` di dalamnya. "
        "Jangan menghapus atau membagikan file token tersebut."
    )
    drive_root = st.text_input("Lokasi USB flash drive", placeholder="E:\\")
    if st.button("Buat USB Dongle", type="primary"):
        if not drive_root.strip():
            st.error("Masukkan lokasi flashdisk terlebih dahulu.")
        else:
            try:
                token_path, token_hash = create_dongle(drive_root.strip())
                cn.set_setting("dongle_token_hash", token_hash)
                st.session_state.verified_dongle_path = token_path
                st.success("Dongle berhasil dibuat dan didaftarkan pada aplikasi.")
                st.info(f"Lokasi token: {token_path}")
                st.rerun()
            except FileExistsError as exc:
                st.error(str(exc))
            except (OSError, ValueError) as exc:
                st.error(f"Setup dongle gagal: {exc}")


def dongle_required():
    st.title("🔒 DIARYLOCK Terkunci")
    st.error("USB dongle belum terdeteksi atau token tidak valid. Aplikasi belum dapat digunakan.")
    st.write("Hubungkan flashdisk yang telah didaftarkan. Jika drive tidak terdeteksi otomatis, masukkan path file token secara manual.")
    token_path = st.text_input(
        "Path file dongle",
        placeholder=r"E:\DIARYLOCK\diarylock.key",
    )
    if st.button("Verifikasi Dongle", type="primary"):
        expected_hash = cn.get_setting("dongle_token_hash")
        if token_path.strip() and verify_dongle_file(token_path.strip(), expected_hash):
            st.session_state.verified_dongle_path = token_path.strip()
            st.success("Dongle valid. Membuka halaman login...")
            st.rerun()
        else:
            st.error("Token tidak ditemukan atau tidak sesuai.")
