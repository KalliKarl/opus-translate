# OPUS Translate — Gelistirme Plani

Self-hosted, cross-platform (Windows + Linux) Turkce↔Ingilizce ceviri servisi.
Helsinki-NLP/opus-mt-tc-big modelleri ile GPU-accelerated FastAPI backend + web dashboard.

## Mimari

```
opus-translate/
├── server.py              → FastAPI ana sunucu (~150 satir)
├── translator.py          → Model yukleme, ceviri mantigi (~80 satir)
├── config.py              → Ayarlar, environment variables (~40 satir)
├── static/
│   ├── index.html         → Web dashboard (ceviri arayuzu)
│   ├── style.css          → Stiller
│   └── app.js             → Client-side JS
├── requirements.txt       → Python bagimliliklari
├── start.sh               → Linux baslatma scripti
├── start.bat              → Windows baslatma scripti
├── CLAUDE.md              → Claude Code kilavuzu
└── README.md              → Dokumantasyon
```

## Teknoloji Secimi

| Bilesim | Teknoloji | Neden |
|---|---|---|
| Backend | **FastAPI** | Async, otomatik OpenAPI docs, hizli |
| Model | **transformers + torch** | MarianMT destegi, GPU otomatik |
| Tokenizer | **sentencepiece** | MarianMT gereksinimi |
| Server | **uvicorn** | ASGI, production-ready |
| Frontend | Vanilla HTML/CSS/JS | Bagimliliksiz, hafif |

## API Tasarimi

### POST /translate
```json
// Request
{
  "text": "Merhaba, nasilsiniz?",
  "direction": "tr-en"        // "tr-en" veya "en-tr"
}

// Response
{
  "translation": "Hello, how are you?",
  "direction": "tr-en",
  "model": "opus-mt-tc-big-tr-en",
  "duration_ms": 45
}
```

### POST /translate/batch
```json
// Request
{
  "texts": ["Merhaba", "Gunaydin", "Iyi geceler"],
  "direction": "tr-en"
}

// Response
{
  "translations": ["Hello", "Good morning", "Good night"],
  "direction": "tr-en",
  "count": 3,
  "duration_ms": 78
}
```

### GET /health
```json
{
  "status": "running",
  "device": "cuda",             // veya "cpu"
  "gpu_name": "NVIDIA GTX 1060",
  "gpu_memory_used": "812 MB",
  "gpu_memory_total": "6144 MB",
  "models_loaded": ["tr-en", "en-tr"],
  "uptime": 3600,
  "total_translations": 1542
}
```

### GET /detect
```json
// Request: ?text=Hello world
// Response
{
  "language": "en",
  "confidence": 0.95,
  "suggested_direction": "en-tr"
}
```

## Model Detaylari

| Model | Yon | HF ID | Boyut | VRAM |
|---|---|---|---|---|
| TR→EN | Turkce→Ingilizce | `Helsinki-NLP/opus-mt-tc-big-tr-en` | ~400MB | ~400MB |
| EN→TR | Ingilizce→Turkce | `Helsinki-NLP/opus-mt-tc-big-en-tr` | ~400MB | ~400MB |
| **Toplam** | | | ~800MB | ~800MB |

RTX 1060 6GB → ~800MB kullanim, **5.2GB bos** kalir.

## Web Dashboard Ozellikleri

1. **Ceviri arayuzu** — Sol panel: kaynak metin, sag panel: ceviri
2. **Yon secimi** — TR→EN / EN→TR toggle, otomatik dil algalama opsiyonu
3. **Gecmis** — Son ceviriler listesi (localStorage)
4. **Istatistikler** — Toplam ceviri, ortalama sure, GPU kullanimi
5. **API dokumantasyonu** — /docs (FastAPI otomatik Swagger)

## Uygulama Adimlari

### Faz 1: Core Backend
- [ ] `config.py` — Ayarlar (port, model path, device, cache)
- [ ] `translator.py` — Model yukleme (lazy load), ceviri fonksiyonu, batch destegi
- [ ] `server.py` — FastAPI app, /translate, /translate/batch, /health, /detect
- [ ] `requirements.txt` — torch, transformers, sentencepiece, fastapi, uvicorn

### Faz 2: Web Dashboard
- [ ] `static/index.html` — Ceviri arayuzu (split-panel layout)
- [ ] `static/style.css` — Dark theme (mcp-bridge ile uyumlu)
- [ ] `static/app.js` — Fetch API, gecmis, istatistik

### Faz 3: Cross-Platform & Deploy
- [ ] `start.sh` — Linux baslatma (venv + uvicorn)
- [ ] `start.bat` — Windows baslatma
- [ ] GPU/CPU otomatik algilama (torch.cuda.is_available)
- [ ] Model cache (ilk indirmeden sonra lokal)
- [ ] README.md + CLAUDE.md

### Faz 4: MCP Bridge Entegrasyonu (Opsiyonel)
- [ ] `translate_text` tool'u mcp-local'e ekleme
- [ ] Bridge uzerinden ceviri servisi kullanimi

## Ortam Degiskenleri

| Degisken | Varsayilan | Aciklama |
|---|---|---|
| `TRANSLATE_PORT` | `5050` | HTTP port |
| `TRANSLATE_DEVICE` | `auto` | `auto`/`cuda`/`cpu` |
| `TRANSLATE_HOST` | `0.0.0.0` | Bind adresi |
| `TRANSLATE_MODELS_DIR` | `~/.cache/huggingface` | Model cache dizini |
| `TRANSLATE_MAX_LENGTH` | `512` | Max token sayisi |
| `TRANSLATE_BATCH_SIZE` | `32` | Max batch boyutu |

## fk-msi Deploy Plani

```bash
# fk-msi uzerinde (SSH)
cd /home/user/
git clone https://github.com/KalliKarl/opus-translate.git
cd opus-translate
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Modeller ilk calistirmada otomatik indirilir (~800MB)
./start.sh
# http://fk-msi:5050 uzerinden erisim
```

## Notlar

- Model ilk calistirmada HuggingFace'den indirilir, sonraki calistirmalarda cache'den yuklenir
- GPU yoksa otomatik CPU'ya duser (daha yavas ama calisiyor)
- Windows'ta CUDA Toolkit + cuDNN gerekli (GPU icin)
- Linux'ta nvidia-driver + CUDA yeterli
- Batch ceviri tekli ceviriden ~5-10x daha hizli (GPU paralelizasyonu)
