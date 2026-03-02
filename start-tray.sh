#!/usr/bin/env bash
# Opus Translate — Linux/macOS Tray Launcher
# Arka planda çalışır, terminal penceresi açmaz.
set -e
cd "$(dirname "$0")"

if [ ! -d venv ]; then
    echo "[tray] venv oluşturuluyor..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q --disable-pip-version-check -r requirements.txt
else
    source venv/bin/activate
fi

# Tray bağımlılıkları
python3 -c "import pystray, PIL" 2>/dev/null || \
    pip install -q --disable-pip-version-check pystray Pillow

# GNOME / Ubuntu appindicator kontrolü
if [ "$(uname)" = "Linux" ]; then
    if ! python3 -c "
import gi
try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
except:
    gi.require_version('AppIndicator3', '0.1')
" 2>/dev/null; then
        echo "[tray] Uyarı: appindicator kurulu değil."
        echo "       Ubuntu/Debian: sudo apt install libayatana-appindicator3-1 gir1.2-ayatanaappindicator3-0.1"
        echo "       Fedora:        sudo dnf install libappindicator-gtk3"
    fi
fi

# Arka planda başlat — terminal kapanınca ölmemesi için nohup
# PYSTRAY_BACKEND=gtk: GNOME 46'da AppIndicator yerine GTK backend (sağ tık menü çalışır)
nohup env PYSTRAY_BACKEND=gtk python3 tray.py >> "$HOME/.opus-translate-tray.log" 2>&1 &
TRAY_PID=$!
echo "[tray] Opus Translate Tray başlatıldı (PID: $TRAY_PID)"
echo "[tray] Durdurmak için: kill $TRAY_PID"
echo "[tray] veya sistem tepsisinden Çıkış seç"
