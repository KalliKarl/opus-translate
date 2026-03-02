"""Opus Translate — Konfigürasyon."""

import logging
import os
from dataclasses import dataclass, field

LOG_FORMAT = "[%(name)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


@dataclass
class Settings:
    host: str = os.getenv("TRANSLATE_HOST", "0.0.0.0")
    port: int = int(os.getenv("TRANSLATE_PORT", "5050"))
    device: str = os.getenv("TRANSLATE_DEVICE", "auto")
    models_dir: str = os.getenv("TRANSLATE_MODELS_DIR", "")
    max_length: int = int(os.getenv("TRANSLATE_MAX_LENGTH", "512"))
    batch_size: int = int(os.getenv("TRANSLATE_BATCH_SIZE", "32"))

    models: dict[str, str] = field(default_factory=lambda: {
        "tr-en": "Helsinki-NLP/opus-mt-tc-big-tr-en",
        "en-tr": "Helsinki-NLP/opus-mt-tc-big-en-tr",
    })

    @property
    def resolved_device(self) -> str:
        if self.device != "auto":
            return self.device
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"


settings = Settings()
