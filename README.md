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
- **API Key koruması** — Bearer token, boş bırakılırsa herkese açık
- **Runtime GPU/CPU toggle** — Dashboard'dan anlık cihaz değişimi
- **Model yönetimi** — Dashboard'dan yükle / boşalt (VRAM kontrolü)
- **System Tray** — Konsol penceresi olmadan arka planda çalışır (Windows + Linux)
- **Cross-platform** — Windows ve Linux desteği

## Gereksinimler

- **Python** 3.10+
- **GPU (opsiyonel):** NVIDIA GPU + CUDA Toolkit
- **RAM:** Minimum 4GB (modeller ~800MB)
- **Disk:** ~2GB (modeller + bağımlılıklar)

## Kurulum

### Windows — Normal mod

```powershell
git clone https://github.com/KalliKarl/opus-translate.git
cd opus-translate
start.bat
```

### Windows — System Tray modu

```powershell
start-tray.bat
```

Terminal penceresi açılmaz. Sistem tepsisinde **OT** ikonu belirir.
Sağ tıkla: **Dashboard Aç** / **Debug Konsol** / **Çıkış**

> İlk çalıştırmada `pystray` ve `Pillow` otomatik kurulur.

### Linux / macOS — Normal mod

```bash
git clone https://github.com/KalliKarl/opus-translate.git
cd opus-translate
chmod +x start.sh
./start.sh
```

### Linux — System Tray modu

```bash
# GNOME bağımlılıkları (Ubuntu/Debian)
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
                 libayatana-appindicator3-1 gir1.2-ayatanaappindicator3-0.1

chmod +x start-tray.sh
./start-tray.sh
```

Terminal kapanır, sistem tepsisinde **OT** ikonu belirir.
**Sol tıkla** menüyü açın: **Dashboard Aç** / **Debug Konsol** / **Çıkış**

> GNOME autostart: `~/.config/autostart/opus-translate-tray.desktop` olarak kaydedilir.
> Debug Konsol: `journalctl -u opus-translate -f` (systemd) veya log dosyası.

### Manuel (tüm platformlar)

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate.bat
pip install -r requirements.txt
python server.py
```

---

### GPU Kurulumu

> **Önemli:** `pip install torch` komutu varsayılan olarak **CPU sürümünü** kurar.
> PyTorch, CUDA destekli sürümlerini kendi sunucusunda tutar — `--index-url` belirtmek zorunludur.

**1. NVIDIA sürücü versiyonunu öğrenin:**

```bash
nvidia-smi
# Çıktıda "CUDA Version: X.X" satırına bakın
```

**2. GPU mimarisine göre PyTorch CUDA sürümünü kurun:**

| GPU Serisi | Mimari | sm | Komut |
|---|---|---|---|
| RTX 5000 serisi (Blackwell) | sm_120 | cu128 | `pip install torch --index-url https://download.pytorch.org/whl/cu128` |
| RTX 4000 serisi (Ada Lovelace) | sm_89/90 | cu121+ | `pip install torch --index-url https://download.pytorch.org/whl/cu121` |
| RTX 3000 serisi (Ampere) | sm_80/86 | cu116+ | `pip install torch --index-url https://download.pytorch.org/whl/cu121` |
| RTX 2000 / GTX 1000 serisi | sm_61-75 | cu118 | `pip install torch --index-url https://download.pytorch.org/whl/cu118` |

> **Not:** Sürücü CUDA versiyonu ≥ PyTorch CUDA versiyonu olmalıdır.
> Örneğin CUDA 13.1 sürücüsü ile cu128 paketi çalışır (geriye dönük uyumlu).
>
> **RTX 5050 / 5060 / 5070 / 5080 / 5090 kullanıcıları:** cu126 **çalışmaz**, mutlaka cu128 gerekir.

**3. GPU'nun görüldüğünü doğrulayın:**

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"
# Çıktı: True 12.8
```

**4. `.env` dosyasında device'ı ayarlayın:**

```bash
TRANSLATE_DEVICE=cuda
```

GPU yoksa veya CUDA kurulu değilse `TRANSLATE_DEVICE=auto` bırakın — otomatik CPU'ya düşer.

---

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

**Dil algılama:**

```bash
curl "http://localhost:5050/detect?text=Hello%20world"
```

---

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

---

## Web Dashboard

`http://localhost:5050` adresinden erişilir.

| Özellik | Açıklama |
|---|---|
| Çeviri paneli | Split-panel, Ctrl+Enter kısayolu |
| GPU/CPU toggle | Header'da anlık cihaz değişimi |
| Model kartları | TR→EN / EN→TR yükle / boşalt — yükleme sırasında progress badge |
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

---

## Proje Yapısı

```
opus-translate/
├── server.py               → FastAPI sunucu, endpoint tanımları
├── translator.py           → Çeviri motoru (model yükleme, inference)
├── detector.py             → Dil algılama
├── schemas.py              → Request/Response Pydantic modelleri
├── auth.py                 → API Key authentication
├── config.py               → Konfigürasyon, .env yükleme
├── tray.py                 → Cross-platform system tray launcher
├── static/
│   ├── index.html          → Web dashboard
│   ├── style.css           → Dark theme stiller
│   └── app.js              → Client-side JavaScript
├── .env                    → Ortam değişkenleri (git'e eklenmez)
├── requirements.txt        → Python bağımlılıkları
├── start.sh                → Linux normal başlatma
├── start.bat               → Windows normal başlatma
├── start-tray.sh           → Linux system tray başlatma
├── start-tray.bat          → Windows system tray başlatma
├── launch-tray.vbs         → Windows: konsulsuz pythonw.exe launcher
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
- Model yüklerken dashboard'da animasyonlu progress badge gösterilir
- GPU yoksa CPU'ya otomatik düşer (daha yavaş ama çalışır)
- Batch çeviri, tekli çeviriden ~5-10x daha hızlıdır (GPU paralelizasyonu)
- RTX 1060 6GB: iki model ~800MB VRAM, ~5.2GB boş kalır
- System tray companion modu: sunucu zaten çalışıyorsa (systemd vb.) yeni başlatmaz
