#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "[start] venv oluşturuluyor..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "[start] Bağımlılıklar kontrol ediliyor..."
pip install -q -r requirements.txt

echo "[start] Opus Translate başlatılıyor..."
python server.py
