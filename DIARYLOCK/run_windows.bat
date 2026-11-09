@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo        DIARYLOCK - Streamlit Launcher
echo ==============================================
echo.

REM Buat virtual environment jika belum tersedia.
if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Membuat virtual environment...
    py -3.12 -m venv .venv
    if errorlevel 1 (
        echo Python Launcher 3.12 tidak tersedia. Mencoba Python default...
        python -m venv .venv
        if errorlevel 1 goto error
    )
) else (
    echo [1/4] Virtual environment sudah tersedia.
)

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"

echo.
echo [2/4] Memperbarui pip...
"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 goto error

echo.
echo [3/4] Menginstal Streamlit dan seluruh library...
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 goto error

echo.
echo [4/4] Menjalankan aplikasi DIARYLOCK dengan Streamlit...
"%PYTHON_EXE%" -m streamlit run app.py
if errorlevel 1 goto error

goto end

:error
echo.
echo Terjadi kesalahan saat menyiapkan atau menjalankan aplikasi.
echo Pastikan Python 3.11/3.12 terpasang dan koneksi internet tersedia saat instalasi.
echo Periksa pesan error di atas untuk mengetahui library yang bermasalah.
pause
exit /b 1

:end
endlocal
