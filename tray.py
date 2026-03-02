"""Opus Translate — Windows System Tray Launcher.

launch-tray.vbs tarafından pythonw.exe ile başlatılır (konsol penceresi yok).
Debug için log dosyasını PowerShell penceresiyle takip eder.
"""

import logging
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).parent
LOG_FILE  = BASE_DIR / "opus-translate.log"


# ── Dosya loglama ──────────────────────────────────────────────────────────────

def _setup_logging() -> None:
    fmt = logging.Formatter("%(asctime)s [%(name)s] %(message)s", datefmt="%H:%M:%S")
    fh  = logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a")
    fh.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(fh)


log = logging.getLogger("tray")


# ── Tray ikonu ─────────────────────────────────────────────────────────────────

def _make_icon():
    from PIL import Image, ImageDraw
    img  = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=(108, 99, 255, 255))
    draw.text((14, 18), "OT", fill=(255, 255, 255, 255))
    return img


# ── Sunucu thread ──────────────────────────────────────────────────────────────

def _run_server() -> None:
    import uvicorn
    from config import settings
    uvicorn.run("server:app", host=settings.host, port=settings.port, reload=False)


# ── Ana giriş ──────────────────────────────────────────────────────────────────

def run() -> None:
    try:
        import pystray
    except ImportError:
        sys.exit("pystray kurulu değil: pip install pystray pillow")

    _setup_logging()
    log.info("Opus Translate Tray başlatılıyor")

    from config import settings

    # Sunucuyu daemon thread'de başlat
    threading.Thread(target=_run_server, daemon=True).start()

    _debug_proc: list[subprocess.Popen | None] = [None]

    def on_open(icon, item):
        webbrowser.open(f"http://localhost:{settings.port}")

    def on_debug(icon, item):
        proc = _debug_proc[0]
        if proc and proc.poll() is None:
            proc.terminate()
            _debug_proc[0] = None
            return
        import platform
        if platform.system() == "Windows":
            _debug_proc[0] = subprocess.Popen(
                [
                    "powershell", "-NoExit", "-Command",
                    f"Write-Host 'Opus Translate Log' -ForegroundColor Cyan; "
                    f"Get-Content '{LOG_FILE}' -Wait -Tail 80",
                ],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        else:
            # Linux: mevcut terminal emülatörüyle aç
            tail_cmd = f"tail -n 80 -f '{LOG_FILE}'"
            for term in ("x-terminal-emulator", "gnome-terminal", "xfce4-terminal", "konsole", "xterm"):
                try:
                    if term == "gnome-terminal":
                        _debug_proc[0] = subprocess.Popen([term, "--", "bash", "-c", tail_cmd])
                    else:
                        _debug_proc[0] = subprocess.Popen([term, "-e", tail_cmd])
                    break
                except FileNotFoundError:
                    continue

    def is_debug_open(item) -> bool:
        p = _debug_proc[0]
        return p is not None and p.poll() is None

    def on_quit(icon, item):
        p = _debug_proc[0]
        if p and p.poll() is None:
            p.terminate()
        log.info("Çıkış yapılıyor")
        icon.stop()
        sys.exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("Dashboard Aç", on_open, default=True),
        pystray.MenuItem("Debug Konsol", on_debug, checked=is_debug_open),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Çıkış", on_quit),
    )

    icon = pystray.Icon("opus-translate", _make_icon(), "Opus Translate", menu)
    icon.run()


if __name__ == "__main__":
    run()
