# DIARYLOCK — Private Digital Diary

Project baru mata kuliah Kriptografi menggunakan **Streamlit + Python**. Struktur dibuat modular dengan pola seperti project acuan: `app.py`, `connection.py`, `list_pages/`, dan `functions/`. Project ini dibuat pada folder terpisah dan tidak mengubah ZIP acuan.

## Fitur sesuai ketentuan tugas

1. **Login biometrik dan dongle**: USB token pada flash drive + pengenalan wajah OpenCV LBPH.
2. **Login dengan kriptografi**: password disimpan dengan PBKDF2-HMAC-SHA256, bukan plaintext.
3. **Super enkripsi teks**: Vigenere Cipher (klasik) lalu AES-256-GCM (modern). Dekripsi dilakukan terbalik.
4. **Enkripsi file**: ChaCha20-Poly1305, berbeda dari algoritma teks.
5. **Database terenkripsi**: isi jurnal disuper-enkripsi sebelum masuk SQLite.
6. **Steganografi gambar**: ciphertext disisipkan ke PNG dengan metode LSB.
7. **Blockchain sederhana**: SHA-256 mencatat hash ciphertext catatan/file, timestamp, previous hash, dan block hash.

## Struktur folder

```text
DIARYLOCK/
├── app.py
├── connection.py
├── schema.sql
├── requirements.txt
├── README.md
├── list_pages/
│   ├── Dongle_Page.py
│   ├── Login_Page.py
│   ├── Register_Page.py
│   └── Dashboard.py
├── functions/
│   ├── biometric.py
│   ├── dongle.py
│   ├── security.py
│   ├── text_encrypt_decrypt.py
│   ├── file_encrypt.py
│   ├── steganography_encryption.py
│   └── blockchain.py
├── data/
│   └── faces/       # sampel wajah lokal saat registrasi
└── tests/
```

## Catatan penting tentang Streamlit

**Streamlit sudah menjadi bagian dari project ini.** Streamlit bukan folder atau file `.py` tersendiri yang akan terlihat pada panel Explorer VS Code. Streamlit adalah library Python yang tercantum pada `requirements.txt`, sedangkan `app.py` adalah file utama yang mengimpor Streamlit (`import streamlit as st`) dan menampilkan antarmuka aplikasi.

Jika terminal menampilkan `streamlit is not recognized`, biasanya library belum dipasang pada environment Python yang sedang aktif. Instal dependency terlebih dahulu dengan perintah di bawah. Cara paling aman adalah menjalankan Streamlit melalui `python -m streamlit` agar memakai environment Python yang sama.

## Persyaratan

- Disarankan Python 3.11 atau 3.12.
- Laptop/komputer dengan webcam.
- USB flash drive untuk dongle prototipe.
- Jalankan aplikasi secara lokal di laptop yang sama dengan webcam dan USB.

## Instalasi di Windows / VS Code

Buka folder `DIARYLOCK` di VS Code, lalu jalankan terminal:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Bila Python yang terpasang bukan 3.12, gunakan `python -m venv .venv` sebagai pengganti perintah pertama.

## Urutan penggunaan pertama

1. Jalankan `streamlit run app.py`.
2. Halaman Setup Dongle muncul. Masukkan root flash drive, misalnya `E:\`.
3. Aplikasi membuat `E:\DIARYLOCK\diarylock.key`. Jangan menghapus atau membagikan file tersebut.
4. Setelah dongle diverifikasi, buka menu Register.
5. Buat username dan password. Ambil **3 sampel foto wajah** dari webcam.
6. Buka menu Login. Pastikan flash drive terpasang, masukkan username/password, lalu ambil foto wajah untuk verifikasi.
7. Setelah berhasil login, buka menu Jurnal Saya dan simpan catatan menggunakan kunci Vigenere dan passphrase AES.
8. Gunakan menu lainnya untuk enkripsi teks, enkripsi file, steganografi, dan blockchain.

Jika dongle tidak terdeteksi otomatis, halaman terkunci menyediakan input path token, misalnya `E:\DIARYLOCK\diarylock.key`.

## Catatan implementasi dan batasan

- **Dongle**: versi ini menggunakan token file acak di USB sebagai prototipe tugas. File token masih dapat disalin; ini bukan hardware security dongle/secure element.
- **Biometrik**: menggunakan LBPH dari `opencv-contrib-python`. Ini demonstrasi autentikasi wajah, bukan sistem biometrik produksi dan belum memiliki liveness/anti-spoofing.
- **Vigenere**: tetap disertakan karena diminta untuk tugas, tetapi Vigenere sendiri tidak aman untuk data nyata. Keamanan modern pada super-enkripsi diberikan oleh AES-GCM.
- **Kunci**: kunci Vigenere dan passphrase AES tidak disimpan oleh aplikasi. Kehilangan kunci berarti catatan tidak bisa didekripsi.
- **Database**: isi catatan dienkripsi sebelum disimpan. Metadata seperti username dan waktu penyimpanan tetap terlihat pada SQLite.
- **Blockchain**: implementasi ini adalah rantai hash lokal sederhana, bukan jaringan blockchain publik/distribusi node.
- **Privasi**: sampel wajah tersimpan lokal pada `data/faces/`. Jangan mempublikasikan folder data atau database.
- **Streamlit**: jalankan lokal. Jika ditempatkan pada server, pemeriksaan USB dan webcam akan terjadi pada lingkungan server/browser sesuai arsitektur deployment, bukan otomatis pada laptop pengembang.

## Shortcut Windows

Kamu juga bisa menjalankan `run_windows.bat` dari folder project (klik dua kali). Script tersebut membuat virtual environment jika belum ada, memasang seluruh requirements termasuk Streamlit, lalu menjalankan `app.py` melalui `python -m streamlit run app.py`.

## Pengujian algoritma

Jalankan:

```powershell
python -m unittest discover -s tests -v
```

Tes ini menguji putar-balik Vigenere+AES, ChaCha20-Poly1305, LSB, dan validasi blockchain dasar. Pengujian webcam/dongle fisik harus dilakukan pada laptop pengguna.
