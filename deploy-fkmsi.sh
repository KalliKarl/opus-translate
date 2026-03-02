#!/usr/bin/env bash
# Opus Translate — fk-msi deploy scripti
# Kullanım: ./deploy-fkmsi.sh [API_KEY]
set -e

REPO="https://github.com/KalliKarl/opus-translate.git"
INSTALL_DIR="$HOME/opus-translate"
API_KEY="${1:-}"
SERVICE_FILE="/etc/systemd/system/opus-translate.service"

echo "=== Opus Translate Deploy ==="

# 1. Repo klonla veya güncelle
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "[1/5] Repo güncelleniyor..."
    git -C "$INSTALL_DIR" pull
else
    echo "[1/5] Repo klonlanıyor..."
    git clone "$REPO" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# 2. venv
if [ ! -d "venv" ]; then
    echo "[2/5] Python venv oluşturuluyor..."
    python3 -m venv venv
fi
source venv/bin/activate

# 3. Bağımlılıklar — PyTorch CUDA önce, sonra diğerleri
echo "[3/5] Bağımlılıklar kuruluyor..."
pip install -q --upgrade pip
# CUDA 12.x için PyTorch; GPU yoksa sadece requirements.txt yeterli
if command -v nvidia-smi &>/dev/null; then
    CUDA_VER=$(nvidia-smi | grep -oP "CUDA Version: \K[\d.]+" | head -1)
    if [[ "$CUDA_VER" == 12* ]]; then
        pip install -q torch --index-url https://download.pytorch.org/whl/cu121
    elif [[ "$CUDA_VER" == 11* ]]; then
        pip install -q torch --index-url https://download.pytorch.org/whl/cu118
    fi
fi
pip install -q -r requirements.txt

# 4. systemd service dosyası oluştur
echo "[4/5] systemd service kuruluyor..."
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Opus Translate
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment=TRANSLATE_DEVICE=cuda
Environment=TRANSLATE_PORT=5050
Environment=TRANSLATE_HOST=0.0.0.0
$([ -n "$API_KEY" ] && echo "Environment=TRANSLATE_API_KEY=$API_KEY")
ExecStart=$INSTALL_DIR/venv/bin/python server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable opus-translate
sudo systemctl restart opus-translate

# 5. Durum kontrol
echo "[5/5] Servis durumu kontrol ediliyor..."
sleep 3
if curl -sf http://localhost:5050/health > /dev/null; then
    echo ""
    echo "=== BAŞARILI ==="
    echo "Erişim: http://fk-msi:5050"
    echo "API Docs: http://fk-msi:5050/docs"
    [ -n "$API_KEY" ] && echo "API Key: $API_KEY"
else
    echo "Servis başlamadı, log:"
    sudo journalctl -u opus-translate -n 20 --no-pager
    exit 1
fi
