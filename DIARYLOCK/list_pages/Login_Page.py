import streamlit as st
import connection as cn
from functions.security import verify_password
from functions.biometric import verify_face


def login():
    left, right = st.columns([1.25, 1])
    with left:
        st.title("🔐 Selamat Datang di DIARYLOCK")
        st.markdown("### Login dengan tiga lapisan keamanan")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        face = st.camera_input("Verifikasi wajah melalui webcam", key="login_face")
        if st.button("Login", type="primary", use_container_width=True):
            if not username or not password or face is None:
                st.error("Lengkapi username, password, dan pemindaian wajah.")
                return
            user = cn.get_user(username)
            if not user or not verify_password(password, user["password_hash"]):
                st.error("Username atau password tidak sesuai.")
                return
            passed, detail = verify_face(username, face.getvalue())
            if not passed:
                st.error("Verifikasi biometrik gagal.")
                st.caption(detail)
                return
            st.session_state.is_logged_in = True
            st.session_state.username = username
            st.success("Autentikasi berhasil. Selamat menggunakan DIARYLOCK.")
            st.caption(detail)
            st.rerun()
    with right:
        st.markdown("## 📔 Jurnal Pribadi")
        st.write("Simpan cerita, pemikiran, dan catatan pribadi dalam bentuk terenkripsi.")
        st.info("Akses login hanya tersedia setelah USB dongle yang terdaftar berhasil diverifikasi.")
        st.caption("Data biometrik disimpan secara lokal pada folder data/faces.")
