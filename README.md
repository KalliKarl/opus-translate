# Opus Translate

Self-hosted, cross-platform Türkçe↔İngilizce çeviri servisi.
[Helsinki-NLP/opus-mt-tc-big](https://huggingface.co/Helsinki-NLP) modelleri ile GPU-accelerated FastAPI backend + web dashboard.

## Özellikler

- **Çift yönlü çeviri** — Türkçe→İngilizce ve İngilizce→Türkçe
- **GPU hızlandırma** — CUDA varsa otomatik GPU, yoksa CPU
- **Web dashboard** — Dark theme çeviri arayüzü
- **REST API** — OpenAPI/Swagger dokümantasyonu dahil
- **Batch çeviri** — Birden fazla metni tek istekte çevir
- **Dil algılama** — Otomatik kaynak dil tespiti
- **Cross-platform** — Windows ve Linux desteği

## Gereksinimler

- **Python** 3.10+
- **GPU (opsiyonel):** NVIDIA GPU + CUDA Toolkit (Windows'ta cuDNN dahil)
- **RAM:** Minimum 4GB (modeller ~800MB)
- **Disk:** ~2GB (modeller + bağımlılıklar)

## Kurulum

### Windows

```powershell
git clone https://github.com/user/opus-translate.git
cd opus-translate

# Otomatik (venv + bağımlılıklar + başlat)
start.bat

# Manuel
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python server.py
```

### Linux / macOS

```bash
git clone https://github.com/user/opus-translate.git
cd opus-translate

# Otomatik
chmod +x start.sh
./start.sh

# Manuel
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

### GPU Kurulumu

> **Önemli:** `pip install torch` komutu varsayılan olarak **CPU sürümünü** kurar.
> PyTorch, CUDA destekli sürümlerini kendi sunucusunda tutar — `--index-url` belirtmek zorunludur.

**1. NVIDIA sürücü versiyonunu öğrenin:**

```bash
nvidia-smi
# Çıktıda "CUDA Version: X.X" satırına bakın
```

**2. Uygun PyTorch CUDA sürümünü kurun:**

```bash
# CUDA 12.6 (sürücü CUDA 12.x veya 13.x için)
pip install torch --index-url https://download.pytorch.org/whl/cu126

# CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121

# CUDA 11.8
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

> **Not:** Sürücü CUDA versiyonu ≥ PyTorch CUDA versiyonu olmalıdır.
> Örneğin CUDA 13.1 sürücüsü ile cu126 paketi çalışır (geriye dönük uyumlu).

**3. GPU'nun görüldüğünü doğrulayın:**

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"
# Çıktı: True 12.6
```

**4. `.env` dosyasında device'ı ayarlayın:**

```bash
TRANSLATE_DEVICE=cuda
```

GPU yoksa veya CUDA kurulu değilse `TRANSLATE_DEVICE=auto` bırakın — otomatik CPU'ya düşer.

## Kullanım

Sunucu başlatıldıktan sonra:

| Adres | Açıklama |
|---|---|
| `http://localhost:5050` | Web dashboard |
| `http://localhost:5050/docs` | Swagger API dokümantasyonu |
| `http://localhost:5050/health` | Sunucu durumu |

### API Örnekleri

**Tek metin çevirisi:**

```bash
curl -X POST http://localhost:5050/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Merhaba, nasılsınız?", "direction": "tr-en"}'
```

```json
{
  "translation": "Hello, how are you?",
  "direction": "tr-en",
  "model": "opus-mt-tc-big-tr-en",
  "duration_ms": 45.2
}
```

**Batch çeviri:**

```bash
curl -X POST http://localhost:5050/translate/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Merhaba", "Günaydın", "İyi geceler"], "direction": "tr-en"}'
```

```json
{
  "translations": ["Hello", "Good morning", "Good night"],
  "direction": "tr-en",
  "count": 3,
  "duration_ms": 78.5
}
```

**Dil algılama:**

```bash
curl "http://localhost:5050/detect?text=Hello%20world"
```

```json
{
  "language": "en",
  "confidence": 0.8,
  "suggested_direction": "en-tr"
}
```

## Ortam Değişkenleri

Proje kökündeki `.env` dosyasından okunur (yoksa sistem ortam değişkenlerine bakılır):

```bash
# .env
TRANSLATE_HOST=0.0.0.0
TRANSLATE_PORT=5050
TRANSLATE_DEVICE=cuda        # auto | cuda | cpu
TRANSLATE_MAX_LENGTH=512
TRANSLATE_BATCH_SIZE=32
TRANSLATE_API_KEY=gizli-key  # boş bırakılırsa koruma yok
```

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `TRANSLATE_PORT` | `5050` | HTTP port |
| `TRANSLATE_HOST` | `0.0.0.0` | Bind adresi |
| `TRANSLATE_DEVICE` | `auto` | `auto` / `cuda` / `cpu` |
| `TRANSLATE_MAX_LENGTH` | `512` | Maksimum token sayısı |
| `TRANSLATE_BATCH_SIZE` | `32` | Maksimum batch boyutu |
| `TRANSLATE_API_KEY` | `""` | API key (boşsa herkese açık) |

> `.env` dosyası `.gitignore`'da tanımlıdır — API key'i commit etme riski yok.

## Web Dashboard

`http://localhost:5050` adresinden erişilir.

| Özellik | Açıklama |
|---|---|
| Çeviri paneli | Split-panel, Ctrl+Enter kısayolu |
| GPU/CPU toggle | Header'da anlık cihaz değişimi |
| Model kartları | TR→EN / EN→TR yükle / boşalt (VRAM yönetimi) |
| Geçmiş | localStorage'da son 50 çeviri |
| Sunucu durumu | Device, VRAM, uptime, toplam çeviri |
| API Key modal | Sunucu key gerektiriyorsa otomatik açılır |

## API Key

Sunucu `.env`'deki `TRANSLATE_API_KEY` ile korunur. Dashboard'da ilk açılışta modal çıkar, girilen key `localStorage`'a kaydedilir.

API çağrılarında header olarak gönderin:

```bash
curl -X POST http://localhost:5050/translate \
  -H "Authorization: Bearer gizli-key" \
  -H "Content-Type: application/json" \
  -d '{"text": "Merhaba", "direction": "tr-en"}'
```

`TRANSLATE_API_KEY` boş bırakılırsa koruma devre dışı.

## Proje Yapısı

```
opus-translate/
├── server.py               → FastAPI sunucu, endpoint tanımları
├── translator.py           → Çeviri motoru (model yükleme, inference)
├── detector.py             → Dil algılama
├── schemas.py              → Request/Response Pydantic modelleri
├── auth.py                 → API Key authentication
├── config.py               → Konfigürasyon, .env yükleme
├── static/
│   ├── index.html          → Web dashboard
│   ├── style.css           → Dark theme stiller
│   └── app.js              → Client-side JavaScript
├── .env                    → Ortam değişkenleri (git'e eklenmez)
├── requirements.txt        → Python bağımlılıkları
├── start.sh                → Linux başlatma scripti
├── start.bat               → Windows başlatma scripti
├── deploy-fkmsi.sh         → fk-msi sunucu deploy scripti
├── opus-translate.service  → systemd unit dosyası
└── CLAUDE.md               → Geliştirici kılavuzu
```

## Modeller

| Model | Yön | HuggingFace ID | Boyut |
|---|---|---|---|
| TR→EN | Türkçe→İngilizce | `Helsinki-NLP/opus-mt-tc-big-tr-en` | ~400MB |
| EN→TR | İngilizce→Türkçe | `Helsinki-NLP/opus-mt-tc-big-en-tr` | ~400MB |

Modeller ilk çalıştırmada otomatik indirilir ve `~/.cache/huggingface` altında cache'lenir.

## Notlar

- İlk çeviri isteğinde model yüklenir (lazy loading) — başlangıç hızlıdır
- GPU yoksa CPU'ya otomatik düşer (daha yavaş ama çalışır)
- Batch çeviri, tekli çeviriden ~5-10x daha hızlıdır (GPU paralelizasyonu)
- RTX 1060 6GB: iki model ~800MB VRAM, ~5.2GB boş kalır
