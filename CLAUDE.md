# Opus Translate

Self-hosted Türkçe↔İngilizce çeviri servisi. Helsinki-NLP/opus-mt-tc-big + FastAPI + web dashboard.

## Çalıştırma

```bash
# Linux
./start.sh

# Windows
start.bat

# Manuel
pip install -r requirements.txt
python server.py
```

Varsayılan: `http://localhost:5050`

## Mimari (SOLID)

Her dosya tek sorumluluk:

- `config.py` — Konfigürasyon, ortam değişkenleri
- `schemas.py` — Pydantic request/response modelleri
- `translator.py` — Çeviri motoru (model yükleme, inference)
- `detector.py` — Dil algılama (Türkçe karakter heuristic)
- `server.py` — FastAPI routing, endpoint tanımları
- `static/` — Web dashboard (HTML/CSS/JS)

## API

- `POST /translate` — `{"text": "...", "direction": "tr-en"}` → tek çeviri
- `POST /translate/batch` — `{"texts": [...], "direction": "tr-en"}` → batch çeviri
- `GET /health` — Sunucu durumu, GPU bilgisi
- `GET /detect?text=...` — Dil algılama
- `GET /docs` — Swagger UI

## Ortam Değişkenleri

- `TRANSLATE_PORT` (5050) — HTTP port
- `TRANSLATE_DEVICE` (auto) — auto/cuda/cpu
- `TRANSLATE_HOST` (0.0.0.0) — Bind adresi
- `TRANSLATE_MAX_LENGTH` (512) — Max token
- `TRANSLATE_BATCH_SIZE` (32) — Max batch boyutu

## Kurallar

- Python 3.10+ gerekli
- `logging` modülü kullan, `print()` kullanma
- Yeni endpoint → `schemas.py`'ye model ekle
- Yeni iş mantığı → ayrı modül, `server.py`'ye import et
- Tüm response'lar typed Pydantic model dönsün
