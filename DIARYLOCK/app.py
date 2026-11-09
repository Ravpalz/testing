import streamlit as st

import connection as cn
from functions.dongle import detect_dongle, verify_dongle_file
from list_pages import Dongle_Page, Login_Page, Register_Page, Dashboard

st.set_page_config(
    page_title="DIARYLOCK | Private Digital Diary",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

cn.initialize_database()

st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px;}
      [data-testid="stSidebar"] {border-right: 1px solid rgba(128,128,128,.2);}
      .diary-subtitle {color: #8b8b98; font-size: .92rem; letter-spacing: .08em;}
    </style>
    """,
    unsafe_allow_html=True,
)

if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

st.sidebar.title("🔐 DIARYLOCK")
st.sidebar.caption("Private Digital Diary")

# Tahap pertama hanya dilakukan saat aplikasi pertama kali disiapkan.
dongle_hash = cn.get_setting("dongle_token_hash")
if not dongle_hash:
    Dongle_Page.setup_dongle()
    st.stop()

# Dongle harus ditemukan dan tokennya harus cocok sebelum halaman login dibuka.
manual_path = st.session_state.get("verified_dongle_path", "")
valid_path = None
if manual_path and verify_dongle_file(manual_path, dongle_hash):
    valid_path = manual_path
else:
    valid_path = detect_dongle(dongle_hash)

if not valid_path:
    st.session_state.is_logged_in = False
    st.session_state.username = ""
    Dongle_Page.dongle_required()
    st.stop()

st.session_state.verified_dongle_path = valid_path
st.sidebar.success("USB dongle terverifikasi")

if st.session_state.is_logged_in:
    st.sidebar.success(f"Login sebagai {st.session_state.username}")
    page = st.sidebar.radio(
        "Navigasi",
        ["Jurnal Saya", "Enkripsi Teks", "Enkripsi File", "Steganografi Gambar", "Blockchain"],
    )
    Dashboard.dashboard(page)
    st.sidebar.divider()
    if st.sidebar.button("Keluar", use_container_width=True):
        st.session_state.is_logged_in = False
        st.session_state.username = ""
        st.session_state.pop("opened_diary", None)
        st.rerun()
else:
    st.sidebar.info("Dongle aktif — silakan autentikasi")
    page = st.sidebar.radio("Navigasi", ["Login", "Register"])
    if page == "Login":
        Login_Page.login()
    else:
        Register_Page.register()
