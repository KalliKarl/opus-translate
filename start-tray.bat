@echo off
cd /d "%~dp0"

if not exist venv\Scripts\python.exe (
    echo Sanal ortam kuruluyor...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -q --disable-pip-version-check -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

:: Tray bagimliklarini kontrol et
venv\Scripts\python.exe -c "import pystray, PIL" 2>nul
if errorlevel 1 (
    echo pystray ve Pillow kuruluyor...
    pip install -q --disable-pip-version-check pystray Pillow
)

:: Konsol penceresi OLMADAN baslatma — VBScript uzerinden pythonw.exe
echo Opus Translate Tray baslatiliyor...
cscript //nologo launch-tray.vbs
