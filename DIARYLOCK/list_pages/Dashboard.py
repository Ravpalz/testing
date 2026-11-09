import json
import os
from pathlib import Path

import streamlit as st
import connection as cn
from functions.text_encrypt_decrypt import super_encrypt, super_decrypt
from functions.file_encrypt import encrypt_file, decrypt_file
from functions.steganography_encryption import embed_msg, extract_msg
from functions.blockchain import add_asset_record, verify_chain, verify_uploaded_asset


def _diary_page():
    st.title("📔 Jurnal Saya")
    st.write("Setiap catatan disuper-enkripsi sebelum disimpan ke SQLite. Hash ciphertext dicatat ke blockchain lokal.")
    tab_new, tab_open = st.tabs(["Buat Catatan", "Buka Catatan"])

    with tab_new:
        title = st.text_input("Judul catatan", key="diary_title")
        body = st.text_area("Isi catatan", height=180, key="diary_body")
        col1, col2 = st.columns(2)
        with col1:
            vigenere_key = st.text_input("Kunci Vigenere", type="password", key="diary_vigenere")
        with col2:
            aes_password = st.text_input("Passphrase AES", type="password", key="diary_aes")
        if st.button("🔒 Enkripsi dan Simpan Catatan", type="primary"):
            if not title.strip() or not body.strip() or not vigenere_key or not aes_password:
                st.error("Semua kolom harus diisi.")
            else:
                try:
                    plaintext = json.dumps({"title": title.strip(), "body": body}, ensure_ascii=False)
                    encrypted_payload = super_encrypt(plaintext, vigenere_key, aes_password)
                    entry_id = cn.insert_diary_entry(st.session_state.username, encrypted_payload)
                    add_asset_record(
                        st.session_state.username,
                        "diary",
                        entry_id,
                        f"Catatan #{entry_id}",
                        encrypted_payload.encode("utf-8"),
                    )
                    st.success(f"Catatan #{entry_id} berhasil dienkripsi dan disimpan. Hash aset dicatat pada blockchain.")
                    st.info("Simpan kedua kunci. Kunci tidak disimpan oleh aplikasi, sehingga catatan tidak dapat dibuka jika kunci hilang.")
                except Exception as exc:
                    st.error(f"Catatan gagal disimpan: {exc}")

    with tab_open:
        entries = cn.get_diary_entries(st.session_state.username)
        if not entries:
            st.info("Belum ada catatan tersimpan.")
        else:
            options = [row["id"] for row in entries]
            labels = {row["id"]: f"Catatan #{row['id']} — {row['created_at'][:19].replace('T', ' ')} UTC" for row in entries}
            selected_id = st.selectbox("Pilih catatan", options, format_func=lambda value: labels[value])
            c1, c2 = st.columns(2)
            with c1:
                open_vig = st.text_input("Kunci Vigenere", type="password", key="open_vig")
            with c2:
                open_aes = st.text_input("Passphrase AES", type="password", key="open_aes")
            if st.button("Buka dan Dekripsi Catatan"):
                entry = cn.get_diary_entry(selected_id, st.session_state.username)
                try:
                    decoded = super_decrypt(entry["encrypted_payload"], open_vig, open_aes)
                    data = json.loads(decoded)
                    st.session_state.opened_diary = data
                    st.success("Catatan berhasil didekripsi.")
                except Exception as exc:
                    st.session_state.pop("opened_diary", None)
                    st.error(f"Tidak dapat membuka catatan: {exc}")
            if st.session_state.get("opened_diary"):
                st.divider()
                st.subheader(st.session_state.opened_diary.get("title", "Catatan"))
                st.write(st.session_state.opened_diary.get("body", ""))
                if st.button("Tutup Catatan"):
                    st.session_state.pop("opened_diary", None)
                    st.rerun()


def _text_encryption_page():
    st.title("🔐 Super Enkripsi Teks")
    st.caption("Urutan enkripsi: Vigenere Cipher → AES-256-GCM. Dekripsi dilakukan dengan urutan terbalik.")
    encrypt_tab, decrypt_tab = st.tabs(["Enkripsi", "Dekripsi"])
    with encrypt_tab:
        message = st.text_area("Masukkan pesan asli", height=150, key="text_plain")
        c1, c2 = st.columns(2)
        with c1:
            vig = st.text_input("Kunci Vigenere", type="password", key="text_vig_enc")
        with c2:
            aes = st.text_input("Passphrase AES (minimal 8 karakter)", type="password", key="text_aes_enc")
        if st.button("Enkripsi Pesan", type="primary"):
            try:
                if not message:
                    raise ValueError("Pesan tidak boleh kosong.")
                result = super_encrypt(message, vig, aes)
                st.session_state.text_encrypted_result = result
            except Exception as exc:
                st.error(str(exc))
        if st.session_state.get("text_encrypted_result"):
            st.text_area("Ciphertext", st.session_state.text_encrypted_result, height=130)
            st.download_button(
                "Unduh ciphertext",
                st.session_state.text_encrypted_result.encode("utf-8"),
                file_name="diarylock_ciphertext.txt",
                mime="text/plain",
            )

    with decrypt_tab:
        encrypted_text = st.text_area("Tempel ciphertext", height=130, key="text_cipher")
        c1, c2 = st.columns(2)
        with c1:
            vig_dec = st.text_input("Kunci Vigenere", type="password", key="text_vig_dec")
        with c2:
            aes_dec = st.text_input("Passphrase AES", type="password", key="text_aes_dec")
        if st.button("Dekripsi Pesan"):
            try:
                result = super_decrypt(encrypted_text.strip(), vig_dec, aes_dec)
                st.success("Dekripsi berhasil.")
                st.text_area("Plaintext", result, height=150)
            except Exception as exc:
                st.error(str(exc))


def _file_encryption_page():
    st.title("📁 Enkripsi dan Dekripsi File")
    st.caption("File memakai ChaCha20-Poly1305, berbeda dari super enkripsi teks.")
    encrypt_tab, decrypt_tab = st.tabs(["Enkripsi File", "Dekripsi File"])
    with encrypt_tab:
        uploaded = st.file_uploader("Pilih file", key="file_to_encrypt")
        password = st.text_input("Password enkripsi file (minimal 8 karakter)", type="password", key="file_enc_password")
        if st.button("Enkripsi File", type="primary"):
            if uploaded is None:
                st.error("Pilih file terlebih dahulu.")
            else:
                try:
                    encrypted = encrypt_file(uploaded.getvalue(), password)
                    st.success("File berhasil dienkripsi.")
                    st.download_button(
                        "Unduh file terenkripsi",
                        encrypted,
                        file_name=f"{uploaded.name}.dlf",
                        mime="application/octet-stream",
                    )
                except Exception as exc:
                    st.error(str(exc))
    with decrypt_tab:
        encrypted_upload = st.file_uploader("Pilih file .dlf", type=["dlf"], key="file_to_decrypt")
        decrypt_password = st.text_input("Password dekripsi", type="password", key="file_dec_password")
        if st.button("Dekripsi File"):
            if encrypted_upload is None:
                st.error("Pilih file terenkripsi terlebih dahulu.")
            else:
                try:
                    decrypted = decrypt_file(encrypted_upload.getvalue(), decrypt_password)
                    original_name = encrypted_upload.name[:-4] if encrypted_upload.name.lower().endswith(".dlf") else "file_pulih"
                    st.success("File berhasil didekripsi.")
                    st.download_button(
                        "Unduh file hasil dekripsi",
                        decrypted,
                        file_name=original_name,
                        mime="application/octet-stream",
                    )
                except Exception as exc:
                    st.error(str(exc))


def _steganography_page():
    st.title("🖼️ Steganografi Gambar")
    st.write("Pesan dienkripsi terlebih dahulu menggunakan Vigenere + AES, kemudian ciphertext disisipkan ke gambar dengan metode LSB.")
    hide_tab, extract_tab = st.tabs(["Sisipkan Pesan", "Ekstrak Pesan"])
    with hide_tab:
        cover = st.file_uploader("Unggah gambar cover", type=["png", "jpg", "jpeg"], key="steg_cover")
        secret = st.text_area("Pesan rahasia", key="steg_secret")
        c1, c2 = st.columns(2)
        with c1:
            vig = st.text_input("Kunci Vigenere", type="password", key="steg_vig")
        with c2:
            aes = st.text_input("Passphrase AES", type="password", key="steg_aes")
        if st.button("Enkripsi dan Sisipkan Pesan", type="primary"):
            if cover is None or not secret:
                st.error("Unggah gambar dan isi pesan terlebih dahulu.")
            else:
                try:
                    encrypted_message = super_encrypt(secret, vig, aes)
                    output_png = embed_msg(cover.getvalue(), encrypted_message)
                    st.success("Pesan terenkripsi berhasil disisipkan ke gambar.")
                    st.image(output_png, caption="Gambar steganografi", use_container_width=True)
                    st.download_button("Unduh gambar PNG", output_png, file_name="diarylock_stego.png", mime="image/png")
                except Exception as exc:
                    st.error(f"Gagal menyisipkan pesan: {exc}")

    with extract_tab:
        stego_image = st.file_uploader("Unggah gambar yang berisi pesan", type=["png"], key="steg_extract")
        c1, c2 = st.columns(2)
        with c1:
            vig_dec = st.text_input("Kunci Vigenere", type="password", key="steg_vig_dec")
        with c2:
            aes_dec = st.text_input("Passphrase AES", type="password", key="steg_aes_dec")
        if st.button("Ekstrak dan Dekripsi Pesan"):
            if stego_image is None:
                st.error("Unggah gambar terlebih dahulu.")
            else:
                try:
                    encrypted_message = extract_msg(stego_image.getvalue())
                    plaintext = super_decrypt(encrypted_message, vig_dec, aes_dec)
                    st.success("Pesan berhasil diekstrak dan didekripsi.")
                    st.text_area("Pesan rahasia", plaintext, height=130)
                except Exception as exc:
                    st.error(f"Ekstraksi/dekripsi gagal: {exc}")


def _blockchain_page():
    st.title("⛓️ Blockchain Integritas Catatan")
    st.write("Setiap catatan baru otomatis dicatat sebagai aset. Blockchain menyimpan hash ciphertext, timestamp, dan hash blok sebelumnya.")
    valid, messages = verify_chain()
    if valid:
        st.success("Rantai blockchain valid.")
    else:
        st.error("Ditemukan masalah pada blockchain.")
    for message in messages:
        st.write(f"- {message}")

    blocks = cn.get_all_blocks()
    if blocks:
        rows = []
        for block in blocks:
            rows.append({
                "Index": block["block_index"],
                "Pemilik": block["username"],
                "Aset": block["asset_name"],
                "Jenis": block["asset_type"],
                "Waktu (UTC)": block["timestamp"][:19].replace("T", " "),
                "Hash aset": block["asset_hash"][:18] + "...",
                "Hash blok": block["block_hash"][:18] + "...",
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada blok. Simpan catatan pertama pada menu Jurnal Saya.")

    st.divider()
    st.subheader("Catat file penting (opsional)")
    asset = st.file_uploader("Pilih file yang hash-nya ingin dicatat", key="asset_to_chain")
    if st.button("Catat Hash File ke Blockchain"):
        if asset is None:
            st.error("Pilih file terlebih dahulu.")
        else:
            try:
                block = add_asset_record(
                    st.session_state.username,
                    "file",
                    None,
                    asset.name,
                    asset.getvalue(),
                )
                st.success(f"Hash file berhasil dicatat pada blok #{block['block_index']}.")
            except Exception as exc:
                st.error(f"Gagal mencatat file: {exc}")

    file_blocks = [block for block in blocks if block["asset_type"] == "file"]
    if file_blocks:
        st.subheader("Verifikasi file terhadap catatan blockchain")
        block_ids = [block["id"] for block in file_blocks]
        selected_block = st.selectbox("Pilih catatan file", block_ids, format_func=lambda value: next(f"Blok #{b['block_index']} — {b['asset_name']}" for b in file_blocks if b["id"] == value))
        verify_file = st.file_uploader("Unggah kembali file yang ingin diverifikasi", key="asset_verify_file")
        if st.button("Verifikasi Hash File"):
            if verify_file is None:
                st.error("Unggah file terlebih dahulu.")
            elif verify_uploaded_asset(selected_block, verify_file.getvalue()):
                st.success("Hash cocok. File sama dengan aset yang dicatat.")
            else:
                st.error("Hash berbeda. File tidak sama dengan aset yang dicatat.")


def dashboard(page: str):
    st.markdown("<div class='diary-subtitle'>PRIVATE JOURNAL • ENCRYPTED BY DESIGN</div>", unsafe_allow_html=True)
    if page == "Jurnal Saya":
        _diary_page()
    elif page == "Enkripsi Teks":
        _text_encryption_page()
    elif page == "Enkripsi File":
        _file_encryption_page()
    elif page == "Steganografi Gambar":
        _steganography_page()
    elif page == "Blockchain":
        _blockchain_page()
