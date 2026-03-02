"""Opus Translate — Cross-platform System Tray Launcher.

Windows : launch-tray.vbs → pythonw.exe tray.py  (konsol yok)
Linux   : start-tray.sh   → nohup python3 tray.py (arka plan)

Sunucu zaten çalışıyorsa (systemd vb.) yeni başlatmaz, sadece ikon gösterir.
"""

import logging
import platform
import socket
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


# ── Sunucu kontrol / başlatma ──────────────────────────────────────────────────

def _server_running(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0


def _run_server() -> None:
    import uvicorn
    from config import settings
    uvicorn.run("server:app", host=settings.host, port=settings.port, reload=False)


# ── Debug konsol ───────────────────────────────────────────────────────────────

def _open_debug_linux(proc_ref: list) -> None:
    """systemd varsa journalctl, yoksa log dosyasını tail et."""
    # systemd servisi var mı?
    has_systemd = subprocess.run(
        ["systemctl", "is-active", "--quiet", "opus-translate"],
        capture_output=True,
    ).returncode == 0

    if has_systemd:
        tail_cmd = "journalctl -u opus-translate -f -n 80"
    else:
        tail_cmd = f"tail -n 80 -f '{LOG_FILE}'"

    for term in ("gnome-terminal", "x-terminal-emulator", "xfce4-terminal", "konsole", "xterm"):
        try:
            if term == "gnome-terminal":
                proc_ref[0] = subprocess.Popen([term, "--", "bash", "-c", tail_cmd])
            else:
                proc_ref[0] = subprocess.Popen([term, "-e", tail_cmd])
            return
        except FileNotFoundError:
            continue


# ── Ana giriş ──────────────────────────────────────────────────────────────────

def run() -> None:
    try:
        import pystray
    except ImportError:
        sys.exit("pystray kurulu değil: pip install pystray pillow")

    _setup_logging()

    from config import settings

    # Sunucu zaten çalışıyorsa yeni başlatma
    if _server_running("127.0.0.1", settings.port):
        log.info("Sunucu zaten çalışıyor (port %s) — tray companion modu", settings.port)
    else:
        log.info("Sunucu başlatılıyor")
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
            _open_debug_linux(_debug_proc)

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
