@echo off
cd /d "%~dp0"

if not exist "venv" (
    echo [start] venv olusturuluyor...
    python -m venv venv
)

call venv\Scripts\activate.bat
echo [start] Bagimliliklar kontrol ediliyor...
pip install -q --disable-pip-version-check -r requirements.txt

echo [start] Opus Translate baslatiliyor...
python server.py
