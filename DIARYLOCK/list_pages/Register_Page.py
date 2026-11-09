import re
import streamlit as st
import connection as cn
from functions.security import hash_password
from functions.biometric import save_face_samples


def register():
    st.title("📝 Registrasi DIARYLOCK")
    st.caption("Buat akun dan daftarkan biometrik wajah. Pastikan USB dongle sudah terhubung.")

    with st.form("register_form"):
        username = st.text_input("Username", max_chars=30)
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Konfirmasi password", type="password")
        st.markdown("**Pendaftaran biometrik wajah**")
        st.caption("Ambil tiga foto wajah dengan posisi sedikit berbeda. Wajah harus terlihat jelas.")
        c1, c2, c3 = st.columns(3)
        with c1:
            face1 = st.camera_input("Sampel wajah 1", key="register_face_1")
        with c2:
            face2 = st.camera_input("Sampel wajah 2", key="register_face_2")
        with c3:
            face3 = st.camera_input("Sampel wajah 3", key="register_face_3")
        submitted = st.form_submit_button("Daftar Akun", type="primary", use_container_width=True)

    if submitted:
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", username):
            st.error("Username harus 3–30 karakter dan hanya boleh berisi huruf, angka, titik, _ atau -.")
            return
        if len(password) < 8:
            st.error("Password minimal 8 karakter.")
            return
        if password != confirm_password:
            st.error("Konfirmasi password tidak sama.")
            return
        if any(sample is None for sample in (face1, face2, face3)):
            st.error("Ambil ketiga sampel wajah sebelum mendaftar.")
            return
        if cn.get_user(username):
            st.error("Username sudah digunakan.")
            return
        try:
            password_hash = hash_password(password)
            save_face_samples(username, [face1.getvalue(), face2.getvalue(), face3.getvalue()])
            cn.create_user(username, password_hash)
            st.success("Registrasi berhasil. Silakan buka menu Login.")
        except Exception as exc:
            st.error(f"Registrasi gagal: {exc}")
            st.info("Pastikan kamera diizinkan oleh browser dan opencv-contrib-python sudah terpasang.")
